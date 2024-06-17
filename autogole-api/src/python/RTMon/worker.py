#!/usr/bin/env python3
"""Main Worker for RTMon."""
import os
import time
from pprint import pformat
from RTMonLibs.GeneralLibs import loadFileJson, getConfig, dumpJson
from RTMonLibs.LogLib import getLoggingObject
from RTMonLibs.SenseAPI import SenseAPI
from RTMonLibs.GrafanaAPI import GrafanaAPI
from RTMonLibs.Template import Template
from RTMonLibs.Template import Mermaid
from RTMonLibs.SiteOverride import SiteOverride

class RTMonWorker(SenseAPI, GrafanaAPI, Template, Mermaid, SiteOverride):
    """ RTMon Worker """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = kwargs.get('logger')
        self.config = kwargs.get('config')
        self.templatePath = self.config['template_path']
        self.generated = {}
        self.auth_instances = {}
        self.goodStates = ['CREATE - READY', 'REINSTATE - READY', 'MODIFY - READY']

    def _updateState(self, filename, fout):
        """Update the state of the file"""
        with open(f'{self.config.get("workdir", "/srv")}/{filename}', 'w', encoding="utf-8") as fd:
            fd.write(dumpJson(fout, self.logger))

    def submit_exe(self, filename, fout):
        """Submit Action Execution"""
        # 1. Get the instance from SENSE-0
        self.logger.info('='*80)
        self.logger.info('Submit Execution: %s, %s', filename, fout)
        instance = self.s_getInstance(fout['referenceUUID'])
        self.logger.info(f"Here is instance for {fout['referenceUUID']}:")
        self.logger.info(pformat(instance))
        # 2. Get the manifest from SENSE-0
        if not instance:
            self.logger.error('Instance not found: %s', fout['referenceUUID'])
            return
        # 2.a Check if the instance is already running
        if instance['state'] not in self.goodStates:
            self.logger.error('Instance not in correct state: %s, %s', fout['referenceUUID'], instance['state'])
            return
        manifest = self.s_getManifest(instance)
        self.logger.info("Here is manifest for the following instance:")
        self.logger.info(pformat(manifest))
        if not manifest:
            self.logger.error('Manifest not found: %s', fout['referenceUUID'])
            return
        # 3. Create the dashboard and template
        try:
            template = self.t_createTemplate(instance, manifest, **fout)
        #except Exception as ex:
        except IOError as ex:
            self.logger.error('Failed to create template: %s', ex)
            return
        # 4. Submit to Grafana (Check if folder exists, if not create it)
        folderName = self.config.get('grafana_folder', 'Real Time Mon')
        folderInfo = self.g_createFolder(folderName)
        template['folderId'] = folderInfo['id']
        template['overwrite'] = True
        self.g_addNewDashboard(template)
        # 5. Update State to Running
        fout['state'] = 'running'
        fout.setdefault('retries', 0)
        self._updateState(filename, fout)

    def delete_exe(self, filename, fout):
        """Delete Action Execution"""
        self.logger.info('Delete Execution: %s, %s', filename, fout)
        # Delete the dashboard and template from Grafana
        for dashbName, dashbVals in self.dashboards.items():
            present = True
            for key in ['referenceUUID', 'orchestrator', 'submission']:
                if fout.get(key, '') not in dashbVals['tags']:
                    present = False
            if present:
                self.logger.info('Deleting Dashboard: %s', dashbName)
                self.g_deleteDashboard(dashbName)
                filename = f'{self.config.get("workdir", "/srv")}/{filename}'
                if os.path.exists(filename):
                    os.remove(filename)
                break

    def running_exe(self, filename, fout):
        """Running Action Execution"""
        self.logger.debug('Running Execution: %s, %s', filename, fout)
        for dashbName, dashbVals in self.dashboards.items():
            present = True
            for key in ['referenceUUID', 'orchestrator', 'submission']:
                if fout.get(key, '') not in dashbVals['tags']:
                    present = False
            if present:
                # Check that version is the same, in case of new release,
                # we need to update the dashboard with new template_tag
                if self.config['template_tag'] in dashbVals['tags']:
                    self.logger.info('Dashboard is present in Grafana: %s', dashbName)
                    return
                # Need to update the dashboard with new template_tag
                self.logger.info('Dashboard is present in Grafana, but with old version: %s', dashbName)
                fout['state'] = 'delete'
                self._updateState(filename, fout)
                return
        # If we reach here - means the dashboard is not present in Grafana
        self.logger.info('Dashboard is not present in Grafana: %s', fout)
        fout.setdefault('retries', 0)
        fout['retries'] += 1
        # If retries are more than 3 - we need to mark it as failed
        if fout['retries'] > 3:
            fout['state'] = 'failed'
            self._updateState(filename, fout)
        else:
            self.submit_exe(filename, fout)

    def failed_exe(self, filename, fout):
        """Failed Action Execution"""
        self.logger.info('Failed Execution: %s, %s', filename, fout)


    def _keepAlive(self, fout):
        """Checks if this item is from auth_key and should be kept alive"""
        # In case it is received dynamically from Orchestrator (not via API)
        # We check if it is still enabled in the orchestrator and state is good.
        if fout.get('submission', '') == 'AUTH_KEY':
            if fout['orchestrator'] in self.auth_instances:
                if fout['referenceUUID'] in self.auth_instances[fout['orchestrator']]:
                    return True
            return False
        # If it is not from AUTH_KEY - we just keep it alive
        return True

    def _getAllInstances(self):
        """Get all instances from sense-o and ensure we have file present for each instance"""
        # 1. Get all instances
        # 2. Check if we have file for each instance
        # 3. If not - create file with state 'submitted'
        out = self.s_getInstances()
        if os.environ["SENSE_AUTH_OVERRIDE_NAME"] in self.auth_instances:
            del self.auth_instances[os.environ["SENSE_AUTH_OVERRIDE_NAME"]]
        self.auth_instances.setdefault(os.environ["SENSE_AUTH_OVERRIDE_NAME"], [])
        if not out:
            return
        for item in out:
            filename = f'{self.config.get("workdir", "/srv")}/rtmon-debug-{os.environ["SENSE_AUTH_OVERRIDE_NAME"]}-{item["referenceUUID"]}'
            if not os.path.exists(filename) and item['state'] in self.goodStates:
                fout = {'state': 'submitted', 'referenceUUID': item['referenceUUID'], 'orchestrator': os.environ['SENSE_AUTH_OVERRIDE_NAME'], 'submission': 'AUTH_KEY'}
                with open(filename, 'w', encoding="utf-8") as fd:
                    fd.write(dumpJson(fout, self.logger))
            if item['state'] in self.goodStates:
                self.auth_instances[os.environ["SENSE_AUTH_OVERRIDE_NAME"]].append(item['referenceUUID'])
            else:
                self.logger.info('Instance not in correct state: %s, %s', item['referenceUUID'], item['state'])

    def main(self):
        """ Main Method"""
        # 1. Identify all files and submitted items;
        # list alls files under '/srv/ and load as json
        stateInfo = {}
        for root, _, files in os.walk(self.config.get('workdir', '/srv')):
            for filename in files:
                if filename.startswith('rtmon-debug-'):
                    fout = loadFileJson(os.path.join(root, filename), self.logger)
                    if not fout:
                        continue
                    keepentry = self._keepAlive(fout)
                    if fout.get('state', '') in ['delete', 'submitted', 'running', 'failed']:
                        if not keepentry:
                            # Means it is not anymore present in SENSE-O, need to delete
                            fout['state'] = 'delete'
                        stateInfo.setdefault(fout['state'], {})
                        stateInfo[fout['state']][filename] = fout
        if not stateInfo:
            return
        for state in ['submitted', 'delete', 'running', 'failed']:
            self.logger.info('State: %s, Files: %s', state, len(stateInfo.get(state, {})))
            for filename, fout in stateInfo.get(state, {}).items():
                self.logger.debug('Filename: %s, Content: %s', filename, fout)
                # Set correct environment variables for SENSE API
                os.environ['SENSE_AUTH_OVERRIDE_NAME'] = fout['orchestrator']
                if state == 'submitted':
                    self.submit_exe(filename, fout)
                elif state == 'delete':
                    self.delete_exe(filename, fout)
                elif state == 'running':
                    self.running_exe(filename, fout)
                elif state == 'failed':
                    self.failed_exe(filename, fout)
                self.logger.info('='*80)
            self.logger.info('-'*80)

    def startwork(self):
        """Execute Main Program."""
        # Loop via all sense-o instances and create files for each instance
        timings = {}
        # Load all grafana dashboards
        self.g_loadAll()
        for key, val in self.config.get('sense_endpoints', {}).items():
            startTime = int(time.time())
            os.environ['SENSE_AUTH_OVERRIDE_NAME'] = key
            os.environ['SENSE_AUTH_OVERRIDE'] = val
            self.s_reloadClient()
            self._getAllInstances()
            endTime = int(time.time())
            timings[key] = endTime - startTime
        startTime = int(time.time())
        self.logger.info('Running Main')
        self.main()
        endTime = int(time.time())
        self.logger.info('Main run finished')
        timings['MAIN_PROGRAM'] = endTime - startTime
        self.logger.info('Timings: %s', timings)
        #self.runtimeGauge.labels(**self._getLabels('MAIN_PROGRAM', "main", "xrootd")).set(totalRuntime)
        #data = generate_latest(self.registry)
        #with open(f'{self.workdir}/xrootd-metrics', 'wb') as fd:
        #    fd.write(data)
        #self.logger.info('StartTime: %s, EndTime: %s, Runtime: %s', startTime, endTime, totalRuntime)


if __name__ == "__main__":
    LOGGER = getLoggingObject()
    CONFIG = getConfig(LOGGER)
    worker = RTMonWorker(config=CONFIG, logger=LOGGER)
    while True:
        try:
            worker.startwork()
        except Exception as exc:
            LOGGER.error('Exception: %s', exc)
        time.sleep(CONFIG.get('sleep_timer', 30))
