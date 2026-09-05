#!/usr/bin/env python3
# pylint: disable=line-too-long
"""Main Worker for RTMon."""
import os
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
    # first so a new dashboard exists before anything else looks for it.
    stateOrder = ("submitted", "delete", "running", "failed", "renew")

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = kwargs.get("logger")
        self.config = kwargs.get("config")
        # templatePath and generated are set by Template.__init__, which runs
        # ahead of this through the cooperative super() chain.
        self.auth_instances = {}
        self.devname = self.config.get("grafana_dev", None)
        self.active_orchestrators = set()

    def _getFolderName(self):
        folderName = self.config.get("grafana_folder", "Real Time Mon")
        if self.devname:
            folderName = f"{folderName} - {self.devname}"
        return folderName

    def _updateState(self, filename, fout):
        """Update the state of the file"""
        with open(f'{self.config.get("workdir", "/srv")}/{filename}', "w", encoding="utf-8") as fd:
            fd.write(dumpJson(fout, self.logger))

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

    def delete_exe(self, filename, fout):
        """Delete Action Execution"""

        def _deletefile(filename):
            filename = f'{self.config.get("workdir", "/srv")}/{filename}'
            if os.path.exists(filename):
                os.remove(filename)

        self.logger.info("Delete Execution: %s, %s", filename, fout)
        # Delete the dashboard and template from Grafana
        for dashbName, dashbVals in self.dashboards.get(self._getFolderName(), {}).items():
            present = True
            for key in ["referenceUUID", "orchestrator", "submission"]:
                if fout.get(key, "") not in dashbVals["tags"]:
                    present = False
            if present:
                self.logger.info("Deleting Dashboard: %s", dashbName)
                self.g_deleteDashboard(dashbName, self._getFolderName())
                _deletefile(filename)
                # Set task action as finished

                self.s_finishTask(
                    fout.get("taskinfo", {}).get("uuid", ""),
                    {"callbackURL": "", "msg": "Deleted dashboard from Grafana"},
                )
                break
        _deletefile(filename)
        # Delete the action from External API
        self.e_submitExternalAPI(fout, "delete")
        # Cancel all SiteRM actions (if any)
        self._executeSiteRMCancel(fout, "delete")

    def running_exe(self, filename, fout):
        """Running Action Execution"""
        self.logger.debug("Running Execution: %s, %s", filename, fout)
        # Check external record to track info of device
        if self.e_submitExternalAPI(fout, "running"):
            # Read back, but deliberately fire-and-forget. The external record is
            # advisory and the dashboard is never gated on it, so acting on the
            # returned status would need a retry policy that does not exist yet.
            self.e_getExternalAPI(fout, "running")
        for dashbName, dashbVals in self.dashboards.get(self._getFolderName(), {}).items():
            present = True
            for key in ["referenceUUID", "orchestrator", "submission"]:
                if fout.get(key, "") not in dashbVals["tags"]:
                    present = False
            if present:
                # Check that version is the same, in case of new release,
                # we need to update the dashboard with new template_tag
                # Set default task info
                fout.setdefault("taskinfo", {}).setdefault("status", "UNKNOWN")
                if fout["taskinfo"]["status"] != "FINISHED":
                    self.s_finishTask(
                        fout["taskinfo"]["uuid"],
                        {"callbackURL": self.g_getDashboardURL(dashbVals["title"], self._getFolderName())},
                    )
                    fout["taskinfo"]["status"] = "FINISHED"
                    self._updateState(filename, fout)
                if self.config["template_tag"] in dashbVals["tags"]:
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
                # Need to update the dashboard with new template_tag
                self.logger.info(
                    "Dashboard is present in Grafana, but with old version: %s",
                    dashbName,
                )
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
        fout["state"] = "delete"
        self._updateState(filename, fout)
        return

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
            fout["state"] = "renew"
            fout["taskinfo"] = task
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
            if not action.startswith("execute"):
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
        """
        stateInfo = {}
        skipped = {}
        for root, _, files in os.walk(self.config.get("workdir", "/srv")):
            for filename in files:
                if not filename.startswith("rtmon-debug-"):
                    continue
                fout = loadFileJson(os.path.join(root, filename), self.logger)
                if not fout:
                    continue
                orchestrator = fout.get("orchestrator", "")
                if orchestrator not in self.active_orchestrators:
                    skipped[orchestrator] = skipped.get(orchestrator, 0) + 1
                    continue
                if fout.get("state", "") in self.stateOrder:
                    stateInfo.setdefault(fout["state"], {})
                    stateInfo[fout["state"]][filename] = fout
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
        stateInfo, skipped = self._collectStateFiles()
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
        }
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
