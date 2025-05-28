#!/usr/bin/env python3
"""External API. Inform external systems about the status and submit request to record data"""
import ast
import requests

class ExternalAPI():
    """Autogole SENSE Grafana RTMon API"""
    def __init__(self, **kwargs):
        # pylint: disable=E1123
        # Grafana lib does support timeout, but pylint does not know it.
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.cert = (self.config['hostcert'], self.config['hostkey'])
        self.external = {}

    def makeRequest(self, url, **kwargs):
        """Make HTTP Request"""
        if kwargs.get('verb', None) not in ['POST']:
            raise Exception(f"Wrong action call {kwargs}")
        # POST
        if kwargs.get('verb') == 'POST':
            out = requests.post(url, cert=self.cert, json=kwargs.get('data', {}),
                                params=kwargs.get('urlparams', None),
                                verify=False, timeout=60)
        try:
            outval = out.json()
            return outval, out.ok, out
        except:
            outval = ""
        try:
            outval = ast.literal_eval(out.text)
        except (ValueError, SyntaxError):
            outval = out.text
        return outval, out.ok, out

    def _e_submitcheck(self, url, item):
        tmpurl = f"{url.rstrip('/')}/submitcheck"
        return self.makeRequest(tmpurl, verb='POST', data=item)

    def _e_submitget(self, url, item):
        tmpurl = f"{url.rstrip('/')}/submitget"
        return self.makeRequest(tmpurl, verb='POST', data=item)

    def _e_submit(self, url, item):
        """Submit action to external system"""
        # In case of submit, we need to check if action is present
        # and if not - submit a new action;
        out = self._e_submitcheck(url, item)
        self.logger.info(f"Submit check {out} for {item}")
        if not out[1]:
            self.logger.info(f"Submit action {item} to external API {url}")
            tmpurl = f"{url.rstrip('/')}/submit"
            # Submit action
            out = self.makeRequest(tmpurl, verb='POST', data=item)
            if not out[1]:
                self.logger.error(f"Failed to submit action to external API {url}. {out}")
        return out

    def _e_delete(self, url, item):
        """Delete action from external system"""
        # In case of delete, we need to check if action is present
        # and if it is - delete the action;
        out = self._e_submitcheck(url, item)
        self.logger.info(f"Delete check {out} for {item}")
        if out[1]:
            self.logger.info(f"Delete action {item} from external API {url}")
            tmpurl = f"{url.rstrip('/')}/submitdelete"
            # Delete action
            out = self.makeRequest(tmpurl, verb='POST', data=item)
            if not out[1]:
                self.logger.error(f"Failed to delete action from external API {url}. {out}")
        return out

    def _e_running(self, url, item):
        """Check if action is running in external system"""
        # In case of running, we need to check if action is present
        # and if it is not - check if it is running
        out = self._e_submitcheck(url, item)
        self.logger.info(f"Running check {out} for {item}")
        if not out[1]:
            self.logger.info(f"Running action {item} from external API {url}")
            tmpurl = f"{url.rstrip('/')}/submit"
            # Check if action is running
            out = self.makeRequest(tmpurl, verb='POST', data=item)
            if not out[1]:
                self.logger.error(f"Failed to submit if action is running in external API {url}. {out}")
        return out

    def _e_submitAction(self, url, data, action):
        """Submit action to external system"""
        if action == 'submit':
            return self._e_submit(url, data)
        if action == 'delete':
            return self._e_delete(url, data)
        if action == 'running':
            return self._e_running(url, data)
        self.logger.error(f"Unknown action {action} for external API")
        return False

    def e_submitExternalAPI(self, data, action):
        """Submit data to external API"""
        self.external = {}
        for _idx, item in enumerate(data.get('manifest', {}).get('Ports', [])):
            tmpitem = self.so_override(item)
            if tmpitem.get('JointSite') in self.config['external_service']:
                url = self.config['external_service'][tmpitem.get('JointSite')]
                self.external.setdefault(url, {'uuid': data['referenceUUID'], 'orchestrator': data['orchestrator'], 'devices': []})
                if len(tmpitem['JointNetwork'].split('|')) < 2:
                    continue
                tmpdict = {'device': tmpitem['JointNetwork'].split('|')[0],
                           'port': tmpitem['JointNetwork'].split('|')[1].replace('_', '/'),
                           'vlan': tmpitem['Vlan']}
                self.external[url]['devices'].append(tmpdict)
        for url, extdata in self.external.items():
            out = self._e_submitAction(url, extdata, action)
            self.logger.info(f"External API {url} {action} {extdata} {out}")
        if self.external:
            return True
        return False

    def _e_httpfailed(self, httpout):
        """Check http error in output from external API"""
        if len(httpout) == 3:
            if httpout[2].status_code >= 400:
                self.logger.error(f"External API error: {httpout[2].status_code} {httpout[2].text}")
                return True
        return False

    def e_getExternalAPI(self, data, action):
        """Get external API data"""
        extinfo = []
        for url, extdata in self.external.items():
            out = self._e_submitget(url, extdata)
            self.logger.info(f"External API {url} {action} {extdata} {out}")
            if self._e_httpfailed(out):
                continue
            extinfo.append(out)
        return extinfo
