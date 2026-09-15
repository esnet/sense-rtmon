#!/usr/bin/env python3
# Over the 1000 line limit since retention split the teardown path in two. The
# module is one class and splitting it would mean splitting RTMonWorker, which is
# the thing the mixins are composed into.
# pylint: disable=line-too-long,too-many-lines
"""Main Worker for RTMon."""
import os
import math
import time
from pprint import pformat
from RTMonLibs.GeneralLibs import loadFileJson, getConfig, dumpJson, getUTCnow, SENSEOFailure, InstanceDataFailure, valtoboolean
from RTMonLibs.LogLib import getLoggingObject
from RTMonLibs.SenseAPI import SenseAPI
from RTMonLibs.GrafanaAPI import GrafanaAPI
from RTMonLibs.Template import Template
from RTMonLibs.Template import Mermaid
from RTMonLibs.SiteOverride import SiteOverride
from RTMonLibs.SiteRMApi import SiteRMApi
from RTMonLibs.ExternalAPI import ExternalAPI
from RTMonLibs.Prometheus import Prometheus
from RTMonLibs.DataWarnings import DataWarnings


# The instance attributes are per cycle counters and caches that main() resets
# together, in the same spirit as the accumulators on Template and Mermaid.
# pylint: disable=too-many-instance-attributes
class RTMonWorker(
    SenseAPI,
    GrafanaAPI,
    Template,
    SiteOverride,
    SiteRMApi,
    ExternalAPI,
    Mermaid,
    Prometheus,
    DataWarnings,
):
    """RTMon Worker"""

    # States SENSE-O reports for an instance RTMon is willing to monitor.
    # Constant rather than an instance attribute: it never varies per worker.
    goodStates = ["CREATE - READY", "REINSTATE - READY", "MODIFY - READY"]

    # The states main() acts on, in the order it acts on them. Submitted runs
    # first so a new dashboard exists before anything else looks for it. Every
    # entry here needs a handler in main(), which checks the two agree.
    stateOrder = ("submitted", "delete", "running", "failed", "renew", "retained")

    # States processed whatever _startwork made of their orchestrator this run.
    # The ownership filter exists so two RTMon instances do not fight over the
    # same entry, but it also means an entry whose orchestrator is unreachable,
    # or has been dropped from the config, is never looked at again. That is
    # harmless for work that needs the orchestrator and wrong for work that does
    # not.
    # Retiring a retained dashboard touches Grafana and the local state file and
    # nothing else, so it must not wait on the orchestrator. A retained entry's
    # task is already finished, so its orchestrator may never be polled again,
    # and gating expiry on ownership is how a retained dashboard becomes
    # permanent.
    ownerlessStates = ("retained",)

    # Dashboard retention. default_days 0 keeps the old behaviour, where a
    # cancelled instance takes its dashboard with it. retentionMinSeconds stops a
    # rounding error or a tiny request producing an expiry that has already
    # passed: removing now is only ever reached by asking for no retention at
    # all, never by asking for a very small amount.
    retentionDefaultDays = 0
    retentionMaxDays = 90
    retentionMinSeconds = 300
    expirePerCycle = 10

    # How long between SENSE-O state checks for a single monitoring entry, and
    # how many consecutive checks have to agree the instance is gone before the
    # dashboard is retired. Both are tracked in the entry's own state file, so
    # the pacing survives a restart and a crash looping pod cannot confirm an
    # absence three times in three minutes.
    senseoCheckInterval = 3600
    senseoAbsentLimit = 3

    # Per entry retry pacing. A failed entry waits retryBase seconds, doubling
    # on each further failure up to retryMax, before it is looked at again.
    # Without this every entry retries on the 30 second loop, so a maintenance
    # window a few minutes long exhausts a retry budget meant to span hours.
    retryBase = 60
    retryMax = 3600

    # How many dashboards on an outdated template are rebuilt in a single cycle.
    # A template_tag bump makes every dashboard stale at once, and each rebuild
    # is a SENSE-O fetch plus a Grafana write, so doing them all in one pass
    # stalls the cycle and holds up the heartbeat the health probes read.
    # Overridable with rerender_per_cycle.
    rerenderPerCycle = 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = kwargs.get("logger")
        self.config = kwargs.get("config")
        # templatePath and generated are set by Template.__init__, which runs
        # ahead of this through the cooperative super() chain.
        self.auth_instances = {}
        self.devname = self.config.get("grafana_dev", None)
        self.active_orchestrators = set()
        # Rebuilds and expiries done in the current cycle. main() resets both.
        self.rerendered = 0
        self.expired = 0
        self.retained = 0

    def _getFolderName(self):
        folderName = self.config.get("grafana_folder", "Real Time Mon")
        if self.devname:
            folderName = f"{folderName} - {self.devname}"
        return folderName

    def _updateState(self, filename, fout):
        """Write an entry's state file, atomically.

        Written to a temporary file alongside the real one and moved into place,
        because the previous truncate and rewrite left a window where a crash or
        a full disk produced a half written file. loadFileJson skips whatever it
        cannot parse, so an entry damaged that way is dropped from every later
        run and whatever it was tracking is never cleaned up.
        """
        workdir = self.config.get("workdir", "/srv")
        target = os.path.join(workdir, filename)
        tmp = f"{target}.tmp"
        with open(tmp, "w", encoding="utf-8") as fd:
            fd.write(dumpJson(fout, self.logger))
            fd.flush()
            os.fsync(fd.fileno())
        os.replace(tmp, target)

    def _checkSenseOState(self, filename, fout):
        """Ask SENSE-O whether the instance behind this dashboard is still live.

        Returns False only when the dashboard should be retired. An orchestrator
        that could not answer never produces False: absence has to be reported by
        a SENSE-O that actually responded, on senseoAbsentLimit consecutive
        checks, before anything is torn down. Until senseo_state_retire is turned
        on, a confirmed absence is logged and nothing is retired.
        """
        instanceuuid = fout.get("taskinfo", {}).get("config", {}).get("uuid", "")
        if not instanceuuid:
            # Entries written before the task carried an instance uuid have
            # nothing to ask about, so they are left alone.
            return True
        # Paced per entry, not globally. A single shared timer meant only the
        # first entry reached in a given hour was ever checked, which is why
        # dashboards for long deleted instances survived indefinitely.
        if getUTCnow() - fout.get("senseocheck", 0) < self.senseoCheckInterval:
            return True
        try:
            instance = self.s_getInstance(instanceuuid)
        except SENSEOFailure as ex:
            # The orchestrator could not answer. That is not evidence the
            # instance is gone, so the absence count is left untouched and the
            # check is simply retried next cycle. Escalating here is how a
            # maintenance window would delete a live dashboard.
            self.logger.warning("SENSE-O could not be queried for %s: %s. Leaving dashboard alone.", instanceuuid, ex)
            return True
        fout["senseocheck"] = getUTCnow()
        if instance and instance.get("state", "") in self.goodStates:
            if fout.pop("senseoabsent", 0):
                self.logger.info("Instance %s is back in a good state. Clearing absence count.", instanceuuid)
            self._updateState(filename, fout)
            return True
        reason = "gone from SENSE-O" if not instance else f'in state {instance.get("state", "")}'
        confirmations = fout.get("senseoabsent", 0) + 1
        fout["senseoabsent"] = confirmations
        self._updateState(filename, fout)
        if confirmations < self.senseoAbsentLimit:
            self.logger.info("Instance %s is %s (%s of %s confirmations). Not retiring yet.", instanceuuid, reason, confirmations, self.senseoAbsentLimit)
        elif not valtoboolean(self.config.get("senseo_state_retire", False)):
            self.logger.info("Instance %s is %s, confirmed %s times. Would retire dashboard, but senseo_state_retire is off.", instanceuuid, reason, confirmations)
        else:
            self.logger.info("Instance %s is %s, confirmed %s times. Retiring dashboard.", instanceuuid, reason, confirmations)
            return False
        return True

    def _retryReady(self, filename, fout):
        """False while a previously failed entry is still inside its backoff."""
        nextattempt = fout.get("nextattempt", 0)
        if getUTCnow() >= nextattempt:
            return True
        self.logger.debug("Skipping %s for another %s seconds of backoff", filename, nextattempt - getUTCnow())
        return False

    def _backoff(self, fout):
        """Push this entry's next attempt out, exponentially in its failures.

        Every kind of failure lengthens the wait, including the ones that are not
        held against the entry, so an orchestrator that is down is retried less
        and less often without that ever being read as the entry misbehaving.
        """
        attempts = fout.get("retries", 0) + len(fout.get("warnings", [])) + fout.get("senseofailures", 0)
        delay = min(self.retryBase * 2 ** max(attempts - 1, 0), self.retryMax)
        fout["nextattempt"] = getUTCnow() + delay
        return delay

    @staticmethod
    def _clearRetryState(fout):
        """Forget an entry's failure history once it has succeeded."""
        fout.pop("nextattempt", None)
        fout.pop("warnings", None)
        fout.pop("senseofailures", None)
        fout["retries"] = 0

    def _updateDashboardPermissions(self, fout):
        """Update dashboard permissions"""
        # Get dashboard uid;
        dashbuid = fout.get("dashbInfo", {}).get("uid", None)
        if not dashbuid:
            self.logger.error("Dashboard UID not found in dashbInfo. Cannot update permissions")
            return
        self.g_addUserDashboardPermissions(dashbuid, fout["taskinfo"]["config"]["users"])

    def renew_exe(self, filename, fout):
        """Renew instance mainly if new information received"""
        if "instance" not in fout or "manifest" not in fout:
            self.logger.error("Instance or Manifest not found in renew. Call back submit: %s", fout)
            self.submit_exe(filename, fout)
            return
        instance = fout["instance"]
        manifest = fout["manifest"]
        # Create dashboard
        try:
            template, dashbInfo = self.t_createTemplate(instance, manifest, **fout)
            fout["dashbInfo"] = dashbInfo
        except IOError as ex:
            msg = f"Failed to create template: {ex}"
            self.logger.error(msg)
            self.s_setTaskState(fout.get("taskinfo", {}).get("uuid", ""), "REJECTED", {"error": msg})
            return
        # Submit to Grafana (Check if folder exists, if not create it)
        folderInfo = self.g_createFolder(self._getFolderName())
        template["folderId"] = folderInfo["id"]
        template["overwrite"] = True
        self.g_addNewDashboard(template)
        # Update State
        fout["state"] = "running"
        fout.setdefault("taskinfo", {})
        fout["taskinfo"]["status"] = "FINISHED"
        self._clearRetryState(fout)
        # Cancel actions (if any have changed)
        fout = self._executeSiteRMCancel(fout, "renew")
        self._updateState(filename, fout)
        # Update dashboard url to sense-o
        self.s_finishTask(fout.get("taskinfo", {}).get("uuid", ""), {"callbackURL": self.g_getDashboardURL(template["dashboard"]["title"], self._getFolderName())})
        self._updateDashboardPermissions(fout)

    def _s_fetchInstanceManifest(self, fout):
        """Fetch the instance and its manifest from SENSE-O.

        Raises InstanceDataFailure when either is missing, so the caller records
        a retryable warning rather than going on to build an empty dashboard.
        """
        # 1. Get the instance from SENSE-0
        instance = self.s_getInstance(fout["referenceUUID"])
        fout["instance"] = instance
        self.logger.info(f"Here is instance for {fout['referenceUUID']}:")
        self.logger.info(pformat(instance))
        # 1.a Check if instance is found
        if not instance:
            msg = f'Instance not found in SENSE-0: {fout["referenceUUID"]}'
            self.logger.error(msg)
            raise InstanceDataFailure(msg)
        # 2.a Check if the instance is already running and in good state
        if instance["state"] not in self.goodStates:
            msg = f'Instance not in correct state: {fout["referenceUUID"]}, {instance["state"]}'
            self.logger.error(msg)
        # 3. Get the manifest from SENSE-0
        manifest = self.s_getManifest(instance)
        fout["manifest"] = manifest
        # 4. Check if manifest is found
        if not manifest:
            msg = f'Manifest not found. Got empty manifest from SENSE-0: {fout["referenceUUID"]}'
            self.logger.error(msg)
            raise InstanceDataFailure(msg)
        return instance, manifest

    def _recordSubmitFailure(self, filename, fout, errmsg):
        """Record a failed submit attempt, and give up once there are more than three."""
        self.logger.error(errmsg)
        fout.setdefault("warnings", [])
        fout["warnings"].append(errmsg)
        delay = self._backoff(fout)
        self.logger.info("Next attempt for %s in %s seconds", filename, delay)
        self._updateState(filename, fout)
        if len(fout["warnings"]) > 3:
            errormsg = f"Got exceptions while receiving data from SENSE-0 for 3 times. Will mark it as failed. Errors: {fout['warnings']}"
            self.logger.error(errormsg)
            self.s_setTaskState(
                fout.get("taskinfo", {}).get("uuid", ""),
                "REJECTED",
                {"error": "Failed to get manifest"},
            )
            fout["state"] = "failed"
            self._updateState(filename, fout)

    def submit_exe(self, filename, fout):
        """Submit Action Execution"""
        self.logger.info("=" * 80)
        self.logger.info("Submit Execution: %s, %s", filename, fout)
        try:
            instance, manifest = self._s_fetchInstanceManifest(fout)
        except SENSEOFailure as ex:
            # The orchestrator could not answer. Back off and come back to it,
            # but do not hold it against the entry. Warnings are what walk an
            # entry to failed, and failed_exe walks it from there to delete, so
            # counting an outage here is how a maintenance window ends up
            # deleting a live instance.
            fout["senseofailures"] = fout.get("senseofailures", 0) + 1
            delay = self._backoff(fout)
            self.logger.error("SENSE-O unavailable for %s: %s. Retrying in %s seconds, attempt %s.", filename, ex, delay, fout["senseofailures"])
            self._updateState(filename, fout)
            return
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # Deliberately broad. Anything the SENSE-O client can raise, from a
            # missing manifest to a socket timeout, has to become a retryable
            # warning on this one entry. Narrowing it would let a transport
            # error escape to main() and abort the remaining state files.
            self._recordSubmitFailure(filename, fout, f"Got exceptions while receiving data from SENSE-0: {ex}")
            return

        # If we reach here - we set task as accepted
        self.s_setTaskState(fout.get("taskinfo", {}).get("uuid", ""), "ACCEPTED")
        self.logger.info("Here is manifest for the following instance:")
        self.logger.info(pformat(manifest))
        # 5. Create the dashboard and template
        try:
            template, dashbInfo = self.t_createTemplate(instance, manifest, **fout)
            fout["dashbInfo"] = dashbInfo
        except IOError as ex:
            self.logger.error("Failed to create template: %s", ex)
            return
        # 6. Submit to Grafana (Check if folder exists, if not create it)
        folderInfo = self.g_createFolder(self._getFolderName())
        template["folderId"] = folderInfo["id"]
        template["overwrite"] = True
        self.g_addNewDashboard(template)
        # Get dashboard URL and report back to SENSE-O
        self.g_loadAll()  # Reload all dashboards (need to get URL)
        self.s_finishTask(
            fout.get("taskinfo", {}).get("uuid", ""),
            {"callbackURL": self.g_getDashboardURL(template["dashboard"]["title"], self._getFolderName())},
        )
        self._updateDashboardPermissions(fout)
        # 7. Submit SiteRM Action to issue a test both ways
        fout = self._executeSiteRMActions(fout, instance, manifest)
        # 8. Submit to External API (if any configured)
        self.e_submitExternalAPI(fout, "submit")
        # 9. Update State to Running
        fout["state"] = "running"
        # A submit that got all the way here clears the failure history. Warnings
        # left over from an orchestrator outage must not count toward the three
        # that mark the entry failed the next time something goes wrong.
        self._clearRetryState(fout)
        self._updateState(filename, fout)

    def _deleteStateFile(self, filename):
        """Remove an entry's state file, and any temporary left beside it."""
        path = os.path.join(self.config.get("workdir", "/srv"), filename)
        for candidate in (path, f"{path}.tmp"):
            if os.path.exists(candidate):
                os.remove(candidate)

    def _cacheRetentionRequest(self, fout, task):
        """Remember what a task asked to retain, while there is still a task to ask.

        SENSE-O creates the cancel task with an empty config and nothing copies
        the enable task's settings into it, so by the time teardown needs the
        number the task carrying it is gone. The state file is the only thing
        that survives the exchange, so the choice is written there as it
        arrives.

        Only a task that carries the setting updates the cache. A task without
        it is not a request for the default, it is a task that was never asked
        the question, and treating the two alike is what loses the value on the
        next renew.
        """
        settings = (task or {}).get("config", {}).get("settings", {}) or {}
        if "retention.days" not in settings:
            return fout
        # None as the default, so an unusable value is left uncached and falls
        # through to the operator default the same way it always has.
        requested = self.getTaskNumber(task, "retention", "days", None)
        if requested is None:
            return fout
        if fout.get("retention_days") != requested:
            self.logger.info("Task asked to retain this dashboard for %s days. Caching it for teardown.", requested)
        fout["retention_days"] = requested
        return fout

    def _retentionSeconds(self, fout):
        """How long this entry's dashboard should outlive its instance.

        Returns 0 for no retention and None for perpetual. The operator sets the
        default and the ceiling; a task can only ask for less than the ceiling,
        never more, and a request that is not a usable number falls back to the
        operator default rather than being read as an instruction to remove now.
        """
        retention = self.config.get("dashboard_retention", {}) or {}
        default = retention.get("default_days", self.retentionDefaultDays)
        maxdays = retention.get("max_days", self.retentionMaxDays)
        requested = fout.get("retention_days")
        if isinstance(requested, bool) or not isinstance(requested, (int, float)):
            # Nothing cached, so this is an entry from before the cache existed.
            # The live task here is the cancel task and its settings are empty,
            # which is exactly the bug, but reading it is still right for an
            # entry whose enable task is somehow still attached.
            requested = self.getTaskNumber(fout.get("taskinfo"), "retention", "days", default)
        if requested < 0 and valtoboolean(retention.get("allow_perpetual", False)):
            self.logger.info("Retention is perpetual for this entry, as the task asked and the operator allows.")
            return None
        if requested <= 0:
            # Includes a negative request when perpetual is not allowed. Asking
            # for something impossible is not the same as asking for nothing, so
            # it falls back rather than removing the dashboard immediately.
            if requested < 0:
                self.logger.info("Perpetual retention was requested but allow_perpetual is off. Using %s days.", default)
                requested = default
            if requested <= 0:
                return 0
        if requested > maxdays:
            self.logger.info("Retention request of %s days exceeds max_days %s. Clamping.", requested, maxdays)
            requested = maxdays
        return max(int(round(requested * 86400)), self.retentionMinSeconds)

    def _teardownActions(self, filename, fout):
        """Everything a cancellation has to tell the outside world.

        Runs once, at cancel time, and needs the orchestrator. Deliberately does
        not touch the filesystem: the state file is what carries the promise to
        keep a dashboard, and the old delete_exe removed it unconditionally on
        the way past.

        s_finishTask is called whether or not a dashboard was found. It used to
        sit inside the branch that matched one, so a cancellation with no
        dashboard left the task unfinished and SENSE-O redelivered it forever.
        """
        if fout.get("teardown_done"):
            return
        self.s_finishTask(
            fout.get("taskinfo", {}).get("uuid", ""),
            {"callbackURL": "", "msg": "Monitoring stopped for this instance"},
        )
        self.e_submitExternalAPI(fout, "delete")
        self._executeSiteRMCancel(fout, "delete")
        fout["teardown_done"] = True
        self._updateState(filename, fout)

    def _removeDashboard(self, filename, fout):
        """Delete the dashboard and forget the entry. Local only, no orchestrator."""
        dashbName, _ = self._findDashboard(fout, retained=True)
        if dashbName:
            self.logger.info("Deleting Dashboard: %s", dashbName)
            self.g_deleteDashboard(dashbName, self._getFolderName())
        self._deleteStateFile(filename)

    def delete_exe(self, filename, fout):
        """Delete Action Execution.

        Splits into the part that has to talk to the orchestrator and the part
        that only touches Grafana and disk, so a dashboard can be kept for a
        while after its instance is cancelled without leaving the task hanging.
        """
        self.logger.info("Delete Execution: %s, %s", filename, fout)
        if fout.get("state", "") == "retained":
            # Already torn down and waiting out its deadline. Re-running the
            # decision would recompute the retention from scratch, and since
            # _findDashboard hides a retained dashboard it would conclude there
            # is nothing to keep and delete the entry outright.
            self.logger.debug("%s is already retained. Leaving it to the expiry sweep.", filename)
            return
        self._teardownActions(filename, fout)
        seconds = self._retentionSeconds(fout)
        dashbName, _ = self._findDashboard(fout)
        if not dashbName:
            # Nothing to keep. An entry that never rendered leaves no history
            # worth a retention record.
            self.logger.info("No dashboard found for %s. Removing the entry.", filename)
            self._removeDashboard(filename, fout)
            return
        if seconds == 0:
            self._removeDashboard(filename, fout)
            return
        # setdefault, not assignment: SENSE-O redelivers a cancel task until it
        # is finished, and recomputing the deadline on each redelivery pushes it
        # out by the full period every cycle, which no log line would show.
        if seconds is None:
            fout.setdefault("retain_forever", True)
            fout.pop("retain_until", None)
            self.logger.info("Retaining dashboard %s for %s indefinitely.", dashbName, filename)
        else:
            fout.setdefault("retain_until", getUTCnow() + seconds)
            self.logger.info("Retaining dashboard %s for %s until %s.", dashbName, filename, fout["retain_until"])
        fout["state"] = "retained"
        self._updateState(filename, fout)

    def retained_exe(self, filename, fout):
        """Remove a retained dashboard once its deadline has passed."""
        if fout.get("retain_forever"):
            return
        deadline = fout.get("retain_until")
        if not isinstance(deadline, int) or deadline <= 0:
            # A missing or unusable deadline must never read as expired, or a
            # renamed key would delete every retained dashboard at once.
            self.logger.error("Retained entry %s has no usable deadline (%r). Re-stamping it.", filename, deadline)
            fout["retain_until"] = getUTCnow() + max(self._retentionSeconds(fout) or 0, self.retentionMinSeconds)
            self._updateState(filename, fout)
            return
        if getUTCnow() < deadline:
            return
        if self.expired >= self._expireLimit():
            self.logger.info("Expiry budget for this cycle is used up. %s waits until the next cycle.", filename)
            return
        self.expired += 1
        self.logger.info("Retention expired for %s. Removing the dashboard.", filename)
        self._removeDashboard(filename, fout)

    def _expireLimit(self):
        """How many retained dashboards may be removed this cycle."""
        try:
            return max(int((self.config.get("dashboard_retention", {}) or {}).get("expire_per_cycle", self.expirePerCycle)), 1)
        except (TypeError, ValueError):
            return self.expirePerCycle

    def _findDashboard(self, fout, retained=False):
        """The Grafana dashboard belonging to this entry, matched on its tags.

        Returns (None, None) when there is none. A dashboard already carrying
        the configured template_tag wins: a rebuild that had to change the title
        leaves the superseded dashboard in place until the new one is confirmed,
        so both can be present at once, and matching the stale one would rebuild
        it again on every cycle.

        A retained entry's dashboard is deliberately invisible unless retained is
        set. It still carries the tags this matches on, so without that a live
        entry could be handed a dashboard that is only waiting to be deleted, and
        the running path would rebuild and re-adopt something already retired.
        """
        if fout.get("state", "") == "retained" and not retained:
            return (None, None)
        match = (None, None)
        for dashbName, dashbVals in self.dashboards.get(self._getFolderName(), {}).items():
            if any(fout.get(key, "") not in dashbVals["tags"] for key in ["referenceUUID", "orchestrator", "submission"]):
                continue
            if self.config.get("template_tag", "") in dashbVals["tags"]:
                return dashbName, dashbVals
            if match[0] is None:
                match = (dashbName, dashbVals)
        return match

    def _rerenderLimit(self):
        """How many dashboards may be rebuilt this cycle."""
        try:
            return max(int(self.config.get("rerender_per_cycle", self.rerenderPerCycle)), 1)
        except (TypeError, ValueError):
            self.logger.error("rerender_per_cycle is not a number: %s. Using %s.", self.config.get("rerender_per_cycle"), self.rerenderPerCycle)
            return self.rerenderPerCycle

    def _rerenderData(self, filename, fout):
        """Instance and manifest to rebuild a dashboard from, newest first.

        Falls back to the copy held in the state file, so bumping the template
        during an orchestrator outage still applies the new template to the last
        data RTMon had instead of leaving the dashboard behind indefinitely.
        """
        # Snapshotted because _s_fetchInstanceManifest assigns into fout before
        # it checks what it got, so a lookup that comes back empty overwrites the
        # cached copy with nothing. Restoring it below also keeps that failure
        # from destroying what renew_exe would otherwise have rebuilt from.
        cached = (fout.get("instance", {}), fout.get("manifest", {}))
        try:
            return self._s_fetchInstanceManifest(fout)
        except (SENSEOFailure, InstanceDataFailure) as ex:
            self.logger.warning("Could not refresh data for %s: %s. Falling back to the cached copy.", filename, ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # Same reason as submit_exe: anything the SENSE-O client raises has
            # to leave the existing dashboard standing rather than escape.
            self.logger.error("Failed to refresh data for %s: %s. Falling back to the cached copy.", filename, ex)
        fout["instance"], fout["manifest"] = cached
        if not cached[0] or not cached[1]:
            self.logger.error("Nothing to rebuild %s from. Leaving the dashboard on the old template.", filename)
        return cached

    def _dropSupersededDashboard(self, dashbVals, newtitle):
        """Remove the dashboard a rebuild replaced, once the new one is up.

        Only reached when the rebuilt title differs from the old one. The title
        carries the instance timestamp and the uid is derived from it, so a
        changed title means the rebuild landed beside the old dashboard instead
        of on top of it. Leaving it is not an option: both carry the tags
        _findDashboard matches on.

        Only the Grafana dashboard goes. The state file and the SENSE-O task
        stay, which is the whole difference between this and delete_exe.
        """
        if not self.g_getDashboardByTitle(newtitle, self._getFolderName()):
            self.logger.error("Rebuilt dashboard %s is not in Grafana yet. Keeping %s until it is.", newtitle, dashbVals["title"])
            return
        self.logger.info("Deleting superseded dashboard %s, replaced by %s", dashbVals["title"], newtitle)
        self.g_deleteDashboard(dashbVals["title"], self._getFolderName())

    def _rerenderDashboard(self, filename, fout, dashbVals):
        """Rebuild a dashboard whose template_tag is behind the configured one.

        This used to set the state to delete, which sent the entry through
        delete_exe: the dashboard went, the state file went, and s_finishTask
        un-assigned the SENSE-O task, so nothing was left to rebuild from.
        Bumping the tag permanently destroyed the dashboards it was documented
        to refresh.

        Nothing here deletes on failure. A dashboard on an old template is
        recoverable on the next cycle and a deleted one is not, so every failure
        path leaves the current dashboard exactly where it is.
        """
        if self.rerendered >= self._rerenderLimit():
            self.logger.info("Rebuild budget for this cycle is used up. %s stays on the old template until the next cycle.", filename)
            return
        self.rerendered += 1
        instance, manifest = self._rerenderData(filename, fout)
        if not instance or not manifest:
            self._backoff(fout)
            self._updateState(filename, fout)
            return
        try:
            template, dashbInfo = self.t_createTemplate(instance, manifest, **fout)
        except IOError as ex:
            self.logger.error("Failed to build the new template for %s: %s. Keeping the current dashboard.", filename, ex)
            self._backoff(fout)
            self._updateState(filename, fout)
            return
        fout["dashbInfo"] = dashbInfo
        folderInfo = self.g_createFolder(self._getFolderName())
        template["folderId"] = folderInfo["id"]
        template["overwrite"] = True
        self.g_addNewDashboard(template)
        self.g_loadAll()  # Reload, both to confirm the rebuild landed and to get its URL
        newtitle = template["dashboard"]["title"]
        if newtitle != dashbVals["title"]:
            self._dropSupersededDashboard(dashbVals, newtitle)
            # The old URL is what SENSE-O still hands users, and it now points at
            # a dashboard that is gone, so the task has to be told the new one.
            self.s_finishTask(fout.get("taskinfo", {}).get("uuid", ""), {"callbackURL": self.g_getDashboardURL(newtitle, self._getFolderName())})
        self._updateDashboardPermissions(fout)
        self.logger.info("Rebuilt %s on template %s", newtitle, self.config.get("template_tag", ""))
        self._clearRetryState(fout)
        self._updateState(filename, fout)

    def running_exe(self, filename, fout):
        """Running Action Execution"""
        self.logger.debug("Running Execution: %s, %s", filename, fout)
        # Check external record to track info of device
        if self.e_submitExternalAPI(fout, "running"):
            # Read back, but deliberately fire-and-forget. The external record is
            # advisory and the dashboard is never gated on it, so acting on the
            # returned status would need a retry policy that does not exist yet.
            self.e_getExternalAPI(fout, "running")
        dashbName, dashbVals = self._findDashboard(fout)
        if dashbName:
            # Set default task info
            fout.setdefault("taskinfo", {}).setdefault("status", "UNKNOWN")
            if fout["taskinfo"]["status"] != "FINISHED":
                self.s_finishTask(
                    fout["taskinfo"]["uuid"],
                    {"callbackURL": self.g_getDashboardURL(dashbVals["title"], self._getFolderName())},
                )
                fout["taskinfo"]["status"] = "FINISHED"
                self._updateState(filename, fout)
            if self.config["template_tag"] not in dashbVals["tags"]:
                # A new release bumped template_tag, so this dashboard is on an
                # older template. Rebuild it where it stands. Routing it through
                # delete_exe instead is what destroyed dashboards permanently.
                self.logger.info("Dashboard is present in Grafana, but with old version: %s", dashbName)
                self._rerenderDashboard(filename, fout, dashbVals)
                return
            self.logger.info("Dashboard is present in Grafana: %s", dashbName)
            self._updateDashboardPermissions(fout)
            # Check if we need to execute any SiteRM actions
            self._executeSiteRMActions(fout, fout.get("instance", {}), fout.get("manifest", {}))
            # Seeing the dashboard is the definition of this entry being
            # healthy, so the misses that got it here are forgotten. They
            # used to accumulate for the lifetime of the entry, which
            # meant thirty transient misses spread over months eventually
            # marked a working dashboard failed.
            self._clearRetryState(fout)
            self._updateState(filename, fout)
            # Add user permissions (if any)
            # Check SENSE-O State and delete if not in a final state anymore;
            if not self._checkSenseOState(filename, fout):
                self.logger.info("SENSE-O Task State not in a final state. Will delete the dashboard")
                fout["state"] = "delete"
                self._updateState(filename, fout)
            return
        # If we reach here - means the dashboard is not present in Grafana
        self.logger.info("Dashboard is not present in Grafana: %s", fout)
        fout.setdefault("retries", 0)
        fout["retries"] += 1
        # If retries are more than 3 - we need to mark it as failed
        if fout["retries"] > 30:
            fout["state"] = "failed"
            self._updateState(filename, fout)
        else:
            # Space the resubmits out. submit_exe clears this again if it works.
            self._backoff(fout)
            self.submit_exe(filename, fout)

    def failed_exe(self, filename, fout):
        """Failed Action Execution"""
        self.logger.info("Failed Execution: %s, %s", filename, fout)
        fout.setdefault("retries", 0)
        self.logger.info(f'Will mark it as delete after 10 cycles. Current: {fout["retries"]}')
        fout["retries"] += 1
        # If retries are more than 10 - we need to mark it as delete
        if fout["retries"] > 10:
            fout["state"] = "delete"
        else:
            # Ten cycles used to be five minutes, short enough that an
            # orchestrator restart walked an entry from failed to delete. Backed
            # off, the same ten cycles span hours.
            self._backoff(fout)
        self._updateState(filename, fout)

    def _taskCancel(self, task, filename):
        """Cancel task"""
        fullpathfilename = f'{self.config.get("workdir", "/srv")}/{filename}'
        self.s_setTaskState(task["uuid"], "ACCEPTED")
        if not os.path.exists(fullpathfilename):
            self.logger.info(f"File {fullpathfilename} not found on the server. RTMon has no knowledge about this monitoring instance")
            # SENSE-O expects it to be FINISHED (even RTMon has no knowledge about it)
            self.s_setTaskState(
                task["uuid"],
                "FINISHED",
                {"error": "File not found on the server. RTMon has no knowledge about this monitoring instance"},
            )
            return
        fout = loadFileJson(fullpathfilename, self.logger)
        if not fout:
            self.logger.info(f"File {fullpathfilename} not found on the server. RTMon has no knowledge about this monitoring instance")
            # SENSE-O expects it to be FINISHED (even RTMon has no knowledge about it)
            self.s_setTaskState(
                task["uuid"],
                "FINISHED",
                {"error": "File not found on the server. RTMon has no knowledge about this monitoring instance"},
            )
            return
        fout["taskinfo"] = task
        if fout.get("state", "") == "retained":
            # SENSE-O redelivers a cancel task until it is finished. Without this
            # the entry would be walked back through delete_exe every cycle,
            # which is harmless for the dashboard but re-runs teardown forever.
            self.logger.debug("Cancel redelivered for %s, which is already retained. Nothing to do.", filename)
            return
        fout["state"] = "delete"
        self._updateState(filename, fout)
        return

    def _adoptRetained(self, filename, fout, instance):
        """Take a retained entry back into service for a re-provisioned instance.

        Same instance uuid, so it is the same state file and the same dashboard.
        Clearing the retention keys is what stops the expiry sweep deleting a
        dashboard that is live again, and dropping the cached instance and
        manifest is what stops the rebuild rendering the previous provisioning:
        the title carries the instance timestamp, so stale data would also mean a
        stale title and a second dashboard beside the one being adopted.
        """
        if not fout or fout.get("state", "") != "retained":
            return fout
        self.logger.info("Instance behind retained entry %s is provisioned again. Adopting the dashboard back.", filename)
        # retention_days is deliberately not cleared. The deadline is dropped
        # because the dashboard is live again and has nothing to expire, but the
        # value the user chose is still their choice for the next cancellation,
        # and the accept that follows overwrites it if they picked a new one.
        for key in ["retain_until", "retain_forever", "teardown_done", "instance", "manifest"]:
            fout.pop(key, None)
        fout["referenceUUID"] = instance.get("referenceUUID", fout.get("referenceUUID", ""))
        self._clearRetryState(fout)
        return fout

    def _taskAccept(self, task, filename):
        """Accept task"""
        fullpathfilename = f'{self.config.get("workdir", "/srv")}/{filename}'
        instanceuuid = task.get("config", {}).get("uuid", "")
        # A SENSEOFailure here is deliberately not caught. It means the
        # orchestrator could not answer, and _startwork records it as a failed
        # orchestrator and skips the rest of its tasks this run. Catching it
        # would fall through to the rejection below and report a live task
        # failed because the orchestrator happened to be restarting.
        out = self.s_getInstance(instanceuuid)
        if os.environ["SENSE_AUTH_OVERRIDE_NAME"] in self.auth_instances:
            del self.auth_instances[os.environ["SENSE_AUTH_OVERRIDE_NAME"]]
        self.auth_instances.setdefault(os.environ["SENSE_AUTH_OVERRIDE_NAME"], [])
        if not out:
            msg = f'Instance {instanceuuid} not found in Orchestrator. Task UUID {task["uuid"]}. Reporting task as failed'
            self.logger.error(msg)
            self.s_setTaskState(task["uuid"], "REJECTED", {"error": msg})
            return
        if not os.path.exists(fullpathfilename) and out["state"] in self.goodStates:
            fout = {
                "state": "submitted",
                "referenceUUID": out["referenceUUID"],
                "orchestrator": os.environ["SENSE_AUTH_OVERRIDE_NAME"],
                "submission": "AUTH_KEY",
                "taskinfo": task,
            }
            with open(fullpathfilename, "w", encoding="utf-8") as fd:
                fd.write(dumpJson(fout, self.logger))
        if out["state"] in self.goodStates:
            self.auth_instances[os.environ["SENSE_AUTH_OVERRIDE_NAME"]].append(out["referenceUUID"])
            self.s_setTaskState(task["uuid"], "WAITING")
            # In this case task remained in ACCEPTED state (or means dashboard already present).
            # We push it to renew
            fout = loadFileJson(fullpathfilename, self.logger)
            fout = self._adoptRetained(filename, fout, out)
            fout["state"] = "renew"
            fout["taskinfo"] = task
            # Every accept, not just the first: a user editing retention in the
            # UI arrives as another task on an entry that is already running.
            fout = self._cacheRetentionRequest(fout, task)
            self._updateState(filename, fout)
        else:
            msg = f'Instance not in correct state: {out["referenceUUID"]}, {out["state"]}'
            self.logger.info(msg)
            self.s_setTaskState(task["uuid"], "REJECTED", {"error": msg})

    def getTaskEnabled(self, taskinfo, parameter):
        """Get Task Enabled - returns True/False.
        Default - based on Registration Setting.
        If not in registration, returns False."""
        # Identify the default value for the parameter
        if parameter not in self.supported_actions:
            self.logger.error(f"Parameter {parameter} not found in supported actions. Returning: False")
            return False
        inputVal = taskinfo.get("config", {}).get("settings", {}).get(f"{parameter}.enabled", None)
        return valtoboolean(inputVal)

    def getTaskNumber(self, taskinfo, parameter, option, default):
        """Read a number typed option off a task, falling back on anything odd.

        supported_actions already advertises number options (streams, runtime),
        but nothing reads them, so the obvious int(value) is what a caller would
        write next. It raises on every value SENSE-O can legitimately send that
        is not a number, and an exception on a teardown path leaves the entry
        half processed. This never raises and never returns a value it did not
        understand.

        Non finite floats are rejected outright rather than clamped: float()
        accepts "inf", json would write it straight back into the state file, and
        every later comparison against it silently succeeds.
        """
        if parameter not in self.supported_actions:
            self.logger.error("Parameter %s not found in supported actions. Using default %s", parameter, default)
            return default
        raw = (taskinfo or {}).get("config", {}).get("settings", {}).get(f"{parameter}.{option}", None)
        if raw is None or isinstance(raw, bool):
            # A boolean is never a meaningful answer to a numeric question, and
            # bool is a subclass of int, so it has to be rejected before float().
            return default
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return default
        try:
            value = float(raw)
        except (TypeError, ValueError):
            self.logger.error("Option %s.%s is not a number: %r. Using default %s", parameter, option, raw, default)
            return default
        if not math.isfinite(value):
            self.logger.error("Option %s.%s is not finite: %r. Using default %s", parameter, option, raw, default)
            return default
        return value

    def _storeAnnotationResults(self, annotations):
        """Submit the annotations for one action and return what should be stored."""
        annotation_results = {}
        for annotation in annotations:
            # Generate new place to store results
            if not annotation.get("storeresults"):
                continue
            tmp_results = {}
            for idnum, keyval in enumerate(annotation["storeresults"], start=1):
                # If it is the last item, then we make default to list
                if idnum == 1:
                    tmp_result = annotation_results.setdefault(keyval, {})
                if idnum == len(annotation["storeresults"]):
                    tmp_result = tmp_results.setdefault(keyval, [])
                else:
                    tmp_result = tmp_results.setdefault(keyval, {})
            try:
                annoout = self.g_submitAnnotation(submitout=annotation.get("submitout", {}), dashbInfo=annotation.get("dashbInfo", {}), timespan=annotation.get("timespan", True))
                tmp_result.extend(annoout)
            except Exception as e:  # pylint: disable=broad-exception-caught
                # An annotation is cosmetic. Losing one must not abort the
                # remaining annotations or the actions that follow.
                self.logger.error(f"Error submitting annotation: {e}")
        return annotation_results

    def _executeSiteRMActions(self, fout, instance, manifest):
        """Execute SiteRM Actions"""
        ## Need to loop over supported action and check if there was a request to execute it.
        for action in self.supported_actions:
            # Any action that starts with execute is a SiteRM action
            # All other actions are for dashboard generation.
            if not action.startswith(self.sitermActionPrefix):
                continue
            if self.s_actionDisabled(action):
                # Advertised as "(temporarily off)", but a task can still arrive
                # with one enabled: it was accepted before the freeze, or the
                # user asked for it anyway. Neither submits anything.
                if self.getTaskEnabled(fout.get("taskinfo"), action):
                    self.logger.info("Action %s is enabled on this task but held off: it needs a SiteRM token exchange. Not submitting it.", action)
                continue
            if not self.getTaskEnabled(fout.get("taskinfo"), action):
                continue
            tmpOut = self.sr_submit_action(action, fout, instance=instance, manifest=manifest)
            if not tmpOut:
                continue
            fout[tmpOut[2]] = tmpOut[0]
            if tmpOut[1] and isinstance(tmpOut[1], list):
                annotation_results = self._storeAnnotationResults(tmpOut[1])
                fout.setdefault("all_annotations", {}).setdefault(action[7:], {}).update(annotation_results)
        return fout

    def _executeSiteRMCancel(self, fout, callstate):
        """Cancel SiteRM Actions"""
        # In case it is renew, We need to check what actions was enabled originally:
        # ping is only cancelled if callstate = delete
        # other, like ethr,iperf, fdt, only cancelled if they have an entry in fout;
        # and current action is disabled in taskinfo.
        for action in self.supported_actions:
            if action.startswith("execute"):
                actionchecks = [action[7:]]
                if action == "executeperf":
                    actionchecks = ["iperf", "ethr", "fdt"]
                    # Which performance action was originally enabled?
                for actioncheck in actionchecks:
                    if callstate == "delete" and actioncheck in fout:
                        fout = self.sr_cancel_action(actioncheck, fout, callstate=callstate)
                        del fout[actioncheck]
                    elif callstate == "renew" and actioncheck in fout and not self.getTaskEnabled(fout.get("taskinfo"), action[7:] if action != "executeperf" else "executeperf"):
                        fout = self.sr_cancel_action(actioncheck, fout, callstate=callstate)
                        del fout[actioncheck]
        return fout

    def _getAllTasks(self):
        """Get all instances from sense-o and ensure we have file present for each instance"""
        # 1. Get all instances
        # 2. Check if we have file for each instance
        # 3. If not - create file with state 'submitted'
        # Get tasks here, and for each write new entry
        newtasks = self.s_getassignedTasks()
        for task in newtasks:
            instanceuuid = task.get("config", {}).get("uuid", "")
            if not instanceuuid:
                msg = f"Instance UUID not found in task provided by SENSE-O. Task: {task}"
                self.logger.error(msg)
                self.s_setTaskState(task["uuid"], "REJECTED", {"error": msg})
                continue
            filename = f'rtmon-debug-{os.environ["SENSE_AUTH_OVERRIDE_NAME"]}-{instanceuuid}'
            # In case "register": false, we need to update the task to delete and task status to accepted;
            if task.get("config", {}).get("register", None) is False:
                self._taskCancel(task, filename)
                continue
            if task.get("config", {}).get("register", None) is True:
                self._taskAccept(task, filename)
            else:
                msg = f"Register flag not found in task provided by SENSE-O. Task: {task}"
                self.logger.error(msg)
                self.s_setTaskState(task["uuid"], "REJECTED", {"error": msg})

    def _collectStateFiles(self):
        """Load every state file this instance owns, grouped by state.

        Returns the grouped files and a per-orchestrator count of the ones
        skipped because another RTMon instance owns them.

        Files whose state RTMon does not recognise are counted and reported
        rather than passed over in silence. Downgrading to a build that predates
        a state makes every entry in it invisible, and an invisible entry is one
        nothing will ever finish or clean up.
        """
        stateInfo = {}
        skipped = {}
        unknown = {}
        for root, _, files in os.walk(self.config.get("workdir", "/srv")):
            for filename in files:
                # .tmp is _updateState's half written file, which is about to be
                # moved over the real one. It carries the same prefix.
                if not filename.startswith("rtmon-debug-") or filename.endswith(".tmp"):
                    continue
                fout = loadFileJson(os.path.join(root, filename), self.logger)
                if not fout:
                    self.logger.error("State file %s is empty or could not be parsed. Skipping it this run.", filename)
                    continue
                state = fout.get("state", "")
                if state not in self.stateOrder:
                    unknown[state] = unknown.get(state, 0) + 1
                    continue
                orchestrator = fout.get("orchestrator", "")
                if orchestrator not in self.active_orchestrators and state not in self.ownerlessStates:
                    skipped[orchestrator] = skipped.get(orchestrator, 0) + 1
                    continue
                stateInfo.setdefault(state, {})
                stateInfo[state][filename] = fout
        if unknown:
            self.logger.error("State files in states this build does not handle: %s. They are not being processed.", unknown)
        return stateInfo, skipped

    def main(self):
        """Process every state file this instance owns.

        Returns the entries that could not be processed, keyed by filename. A
        failed entry is a property of that entry, not of the process, so it is
        reported rather than raised: one unprocessable state file used to abort
        the cycle and take the whole pod NotReady until it was cleaned up.
        """
        # 1. Identify all files and submitted items;
        # list all files under '/srv/ and load as json
        self.rerendered = 0
        self.expired = 0
        stateInfo, skipped = self._collectStateFiles()
        # Reported so a retained backlog is visible from outside the process.
        # Retention is the one thing here that accumulates silently: nothing
        # fails and nothing logs an error while a folder fills up.
        self.retained = len(stateInfo.get("retained", {}))
        if skipped:
            self.logger.info("Skipped files for orchestrators not owned by this instance: %s", skipped)
        if not stateInfo:
            return {}
        handlers = {
            "submitted": self.submit_exe,
            "delete": self.delete_exe,
            "running": self.running_exe,
            "failed": self.failed_exe,
            "renew": self.renew_exe,
            "retained": self.retained_exe,
        }
        # These two are edited by hand and drift apart quietly. A state in
        # stateOrder with no handler raises KeyError mid cycle; a handler with no
        # state in stateOrder is never reached and its entries pile up unseen.
        if set(handlers) != set(self.stateOrder):
            self.logger.error("stateOrder and handlers disagree. Only in stateOrder: %s. Only in handlers: %s.", sorted(set(self.stateOrder) - set(handlers)), sorted(set(handlers) - set(self.stateOrder)))
        failedentries = {}
        for state in self.stateOrder:
            self.logger.info("State: %s, Files: %s", state, len(stateInfo.get(state, {})))
            for filename, fout in stateInfo.get(state, {}).items():
                if not self._retryReady(filename, fout):
                    continue
                try:
                    self.logger.debug("Filename: %s, Content: %s", filename, fout)
                    # Set correct environment variables for SENSE API
                    os.environ["SENSE_AUTH_OVERRIDE_NAME"] = fout["orchestrator"]
                    handlers[state](filename, fout)
                    self.logger.info("=" * 80)
                except Exception as ex:  # pylint: disable=broad-exception-caught
                    # Deliberately broad, for the same reason as the orchestrator
                    # loop below: one unprocessable state file must not stop the
                    # rest. It is recorded per entry and surfaced in the
                    # heartbeat, so nothing is swallowed silently.
                    failedentries[filename] = f"{type(ex).__name__}: {ex}"
                    self.logger.error("Exception: %s", ex)
                    self.logger.error("Failed to process file: %s", filename)
                    self.logger.error("File content: %s", fout)
                    self.logger.info("-" * 80)
                    try:
                        self._backoff(fout)
                        self._updateState(filename, fout)
                    except OSError as writeex:
                        self.logger.error("Could not record backoff for %s: %s", filename, writeex)
            self.logger.info("-" * 80)
        if failedentries:
            self.logger.error("Entries that failed this run: %s", sorted(failedentries))
        return failedentries

    def _writeHeartbeat(self, clean, failed, endpoints, failedentries=None):
        """Record run status so health can be judged from outside the process.

        This is a simple JSON file that contains the last run time,
        whether the last run was clean,
        and the list of configured and active orchestrators.
        It also records the last time a clean run was completed,
        so that external monitoring can determine if the process is healthy or not.

        failed_entries is reported but deliberately left out of healthy. An entry
        RTMon cannot process is a problem with that entry, and restarting the pod
        does not fix it, so it must not take readiness down. It stays here to be
        alerted on.
        """
        hbfile = os.path.join(self.config.get("workdir", "/srv"), ".rtmon-heartbeat")
        healthy = not failed and clean
        data = {
            "last_run": getUTCnow(),
            "healthy": healthy,
            "configured_orchestrators": sorted(endpoints),
            "active_orchestrators": sorted(self.active_orchestrators),
            "failed_orchestrators": failed,
            "failed_entries": failedentries or {},
            "retained_dashboards": self.retained,
            "main_error": not clean,
        }
        if healthy:
            data["last_clean_run"] = data["last_run"]
        else:
            previous = {}
            if os.path.exists(hbfile):
                try:
                    previous = loadFileJson(hbfile, self.logger) or {}
                except OSError as ex:
                    self.logger.error("Failed to read previous heartbeat %s: %s", hbfile, ex)
            data["last_clean_run"] = previous.get("last_clean_run", 0)
        try:
            with open(hbfile, "w", encoding="utf-8") as fd:
                fd.write(dumpJson(data, self.logger))
        except OSError as ex:
            self.logger.error("Failed to write heartbeat file %s: %s", hbfile, ex)

    def startwork(self):
        """Execute Main Program."""
        try:
            self._startwork()
        except SENSEOFailure as ex:
            self.logger.error("SENSEOFailure: %s", ex)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            # The daemon must not exit on a transient fault. Anything reaching
            # here already failed after main() ran, so the heartbeat has recorded
            # it and readiness reports the degradation; letting it escape would
            # only kill the loop that is going to retry in 30 seconds.
            self.logger.error("Unhandled %s in main run: %s", type(ex).__name__, ex)

    def _startwork(self):
        """Execute Main Program."""
        # Loop via all sense-o instances and create files for each instance
        timings = {}
        failed = {}
        self.active_orchestrators = set()
        # Load all grafana dashboards
        self.g_loadAll()
        endpoints = self.config.get("sense_endpoints", {})
        for key, val in endpoints.items():
            try:
                startTime = int(time.time())
                os.environ["SENSE_AUTH_OVERRIDE_NAME"] = key
                os.environ["SENSE_AUTH_OVERRIDE"] = val
                os.environ["SENSE_TIMEOUT"] = str(self.config.get("sense_timeout", 30))
                self.s_reloadClient()
                self.s_updateMetadata()
                self._getAllTasks()
                endTime = int(time.time())
                timings[key] = endTime - startTime
                self.active_orchestrators.add(key)
            except Exception as ex:  # pylint: disable=broad-exception-caught
                # Deliberately broad. The guarantee this loop has to provide is
                # that no single orchestrator can stop the others, and that has
                # to hold for every failure mode, not just the anticipated ones.
                # Catching only SENSEOFailure missed the case that caused
                # sdn-sense/siterm#1003 in the first place: an orchestrator that
                # is simply down raises requests.exceptions.ConnectionError,
                # which escaped to the caller and skipped main() entirely.
                # Swallowing here is safe only because the failure is recorded in
                # the heartbeat and surfaces through the readiness probe.
                self.logger.error("Orchestrator %s failed with %s: %s", key, type(ex).__name__, ex)
                self.logger.error("Skipping %s this run. Other orchestrators are unaffected.", key)
                failed[key] = f"{type(ex).__name__}: {ex}"
        if failed:
            self.logger.error("Orchestrators unavailable this run: %s", sorted(failed))
        if endpoints and not self.active_orchestrators:
            # Still not a reason to exit or to stop cycling. RTMon reports itself
            # unhealthy and keeps polling, so it recovers by itself once they return.
            self.logger.error("No configured orchestrator is reachable. Reporting unhealthy and continuing.")
        startTime = int(time.time())
        self.logger.info("Running Main")
        clean = False
        failedentries = {}
        try:
            failedentries = self.main()
            clean = True
        finally:
            endTime = int(time.time())
            timings["MAIN_PROGRAM"] = endTime - startTime
            self._writeHeartbeat(clean, failed, endpoints, failedentries)
        self.logger.info("Main run finished")
        self.logger.info("Timings: %s", timings)
        # self.runtimeGauge.labels(**self._getLabels('MAIN_PROGRAM', "main", "xrootd")).set(totalRuntime)
        # data = generate_latest(self.registry)
        # with open(f'{self.workdir}/xrootd-metrics', 'wb') as fd:
        #    fd.write(data)
        # self.logger.info('StartTime: %s, EndTime: %s, Runtime: %s', startTime, endTime, totalRuntime)


if __name__ == "__main__":
    LOGGER = getLoggingObject()
    CONFIG = getConfig(LOGGER)
    worker = RTMonWorker(config=CONFIG, logger=LOGGER)
    while True:
        try:
            worker.startwork()
        except IOError as exc:  # Exception as exc:
            LOGGER.error("Exception: %s", exc)
        time.sleep(CONFIG.get("sleep_timer", 30))
