#!/usr/bin/env python3
# pylint: disable=line-too-long
"""Main Worker for RTMon."""
import os
import time
from pprint import pformat
from RTMonLibs.GeneralLibs import loadFileJson, getConfig, dumpJson, getUTCnow, SENSEOFailure, valtoboolean
from RTMonLibs.LogLib import getLoggingObject
from RTMonLibs.SenseAPI import SenseAPI
from RTMonLibs.GrafanaAPI import GrafanaAPI
from RTMonLibs.Template import Template
from RTMonLibs.Template import Mermaid
from RTMonLibs.SiteOverride import SiteOverride
from RTMonLibs.SiteRMApi import SiteRMApi
from RTMonLibs.ExternalAPI import ExternalAPI
from RTMonLibs.Prometheus import Prometheus


class RTMonWorker(
    SenseAPI,
    GrafanaAPI,
    Template,
    SiteOverride,
    SiteRMApi,
    ExternalAPI,
    Mermaid,
    Prometheus,
):
    """RTMon Worker"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = kwargs.get("logger")
        self.config = kwargs.get("config")
        self.templatePath = self.config["template_path"]
        self.generated = {}
        self.auth_instances = {}
        self.goodStates = ["CREATE - READY", "REINSTATE - READY", "MODIFY - READY"]
        self.senseotimer = getUTCnow()
        self.devname = self.config.get("grafana_dev", None)

    def _getFolderName(self):
        folderName = self.config.get("grafana_folder", "Real Time Mon")
        if self.devname:
            folderName = f"{folderName} - {self.devname}"
        return folderName

    def _updateState(self, filename, fout):
        """Update the state of the file"""
        with open(f'{self.config.get("workdir", "/srv")}/{filename}', "w", encoding="utf-8") as fd:
            fd.write(dumpJson(fout, self.logger))

    def _checkSenseOState(self, fout):
        """Check SENSE-O Task State and cancel if not in a final state"""
        # Run it only once an hour
        if getUTCnow() - self.senseotimer < 3600:
            return True
        self.senseotimer = getUTCnow()
        instanceuuid = fout.get("taskinfo").get("config", {}).get("uuid", "")
        if not instanceuuid:
            # If we are missing instanceuuid, we ignore it;
            return True
        out = self.s_getInstance(instanceuuid)
        if out["state"] not in self.goodStates:
            self.logger.info(f'Instance {instanceuuid} is in good state: {out["state"]}')
            return False
        return True

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
        fout.setdefault("retries", 0)
        # Cancel actions (if any have changed)
        fout = self._executeSiteRMCancel(fout, "renew")
        self._updateState(filename, fout)
        # Update dashboard url to sense-o
        self.s_finishTask(fout.get("taskinfo", {}).get("uuid", ""), {"callbackURL": self.g_getDashboardURL(template["dashboard"]["title"], self._getFolderName())})
        self._updateDashboardPermissions(fout)

    def submit_exe(self, filename, fout):
        """Submit Action Execution"""
        self.logger.info("=" * 80)
        self.logger.info("Submit Execution: %s, %s", filename, fout)
        try:
            # 1. Get the instance from SENSE-0
            instance = self.s_getInstance(fout["referenceUUID"])
            fout["instance"] = instance
            self.logger.info(f"Here is instance for {fout['referenceUUID']}:")
            self.logger.info(pformat(instance))
            # 1.a Check if instance is found
            if not instance:
                msg = f'Instance not found in SENSE-0: {fout["referenceUUID"]}'
                self.logger.error(msg)
                raise Exception(msg)
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
                raise Exception(msg)
        except Exception as ex:
            errmsg = f"Got exceptions while receiving data from SENSE-0: {ex}"
            self.logger.error(errmsg)
            fout.setdefault("warnings", [])
            fout["warnings"].append(errmsg)
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
        fout.setdefault("retries", 0)
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
            # TODO: We might want to check status of external service.
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
                    self._updateState(filename, fout)
                    # Add user permissions (if any)
                    # Check SENSE-O State and delete if not in a final state anymore;
                    if not self._checkSenseOState(fout):
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

    def _executeSiteRMActions(self, fout, instance, manifest):
        """Execute SiteRM Actions"""
        ## Need to loop over supported action and check if there was a request to execute it.
        for action in self.supported_actions:
            # Any action that starts with execute is a SiteRM action
            # All other actions are for dashboard generation.
            if action.startswith("execute"):
                if self.getTaskEnabled(fout.get("taskinfo"), action):
                    tmpOut = self.sr_submit_action(action, fout, instance=instance, manifest=manifest)
                    if tmpOut:
                        fout[tmpOut[2]] = tmpOut[0]
                        if tmpOut[1] and isinstance(tmpOut[1], list):
                            annotation_results = {}
                            for annotation in tmpOut[1]:
                                # Generate new place to store results
                                if annotation.get("storeresults"):
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
                                        annoout = self.g_submitAnnotation(
                                            submitout=annotation.get("submitout", {}), dashbInfo=annotation.get("dashbInfo", {}), timespan=annotation.get("timespan", True)
                                        )
                                        tmp_result.extend(annoout)
                                    except Exception as e:
                                        self.logger.error(f"Error submitting annotation: {e}")
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

    def main(self):
        """Main Method"""
        # 1. Identify all files and submitted items;
        # list alls files under '/srv/ and load as json
        stateInfo = {}
        for root, _, files in os.walk(self.config.get("workdir", "/srv")):
            for filename in files:
                if filename.startswith("rtmon-debug-"):
                    fout = loadFileJson(os.path.join(root, filename), self.logger)
                    if not fout:
                        continue
                    if fout.get("state", "") in [
                        "delete",
                        "submitted",
                        "running",
                        "failed",
                        "renew",
                    ]:
                        stateInfo.setdefault(fout["state"], {})
                        stateInfo[fout["state"]][filename] = fout
        if not stateInfo:
            return
        excp = None
        for state in ["submitted", "delete", "running", "failed", "renew"]:
            self.logger.info("State: %s, Files: %s", state, len(stateInfo.get(state, {})))
            for filename, fout in stateInfo.get(state, {}).items():
                try:
                    self.logger.debug("Filename: %s, Content: %s", filename, fout)
                    # Set correct environment variables for SENSE API
                    os.environ["SENSE_AUTH_OVERRIDE_NAME"] = fout["orchestrator"]
                    if state == "submitted":
                        self.submit_exe(filename, fout)
                    elif state == "delete":
                        self.delete_exe(filename, fout)
                    elif state == "running":
                        self.running_exe(filename, fout)
                    elif state == "failed":
                        self.failed_exe(filename, fout)
                    elif state == "renew":
                        self.renew_exe(filename, fout)
                    self.logger.info("=" * 80)
                except Exception as ex:
                    excp = ex
                    self.logger.error("Exception: %s", ex)
                    self.logger.error("Failed to process file: %s", filename)
                    self.logger.error("File content: %s", fout)
                    self.logger.info("-" * 80)
            self.logger.info("-" * 80)
        if excp:
            # Re-raise exception to sleep 30 seconds.
            self.logger.error("Here is the last exception: %s", excp)
            raise excp

    def startwork(self):
        """Execute Main Program."""
        try:
            self._startwork()
        except SENSEOFailure as ex:
            self.logger.error("SENSEOFailure: %s", ex)

    def _startwork(self):
        """Execute Main Program."""
        # Loop via all sense-o instances and create files for each instance
        timings = {}
        # Load all grafana dashboards
        self.g_loadAll()
        for key, val in self.config.get("sense_endpoints", {}).items():
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
            except SENSEOFailure as ex:
                self.logger.error("SENSEOFailure: %s", ex)
                self.logger.error("Failed to load SENSE-O data. Will not check any local files")
                raise ex
        startTime = int(time.time())
        self.logger.info("Running Main")
        self.main()
        endTime = int(time.time())
        self.logger.info("Main run finished")
        timings["MAIN_PROGRAM"] = endTime - startTime
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
