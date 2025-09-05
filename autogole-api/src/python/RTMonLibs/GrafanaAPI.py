#!/usr/bin/env python3
"""Grafana API for Autogole SENSE RTMon"""
import time
import random
from grafana_client import GrafanaApi


class GrafanaAPI:
    """Autogole SENSE Grafana RTMon API"""

    def __init__(self, **kwargs):
        # pylint: disable=E1123
        # Grafana lib does support timeout, but pylint does not know it.
        super().__init__(**kwargs)
        self.config = kwargs.get("config")
        self.logger = kwargs.get("logger")
        self.grafanaapi = GrafanaApi.from_url(url=self.config["grafana_host"], credential=self.config["grafana_api_key"], timeout=30)
        self.datasources = {}
        self.dashboards = {}
        self.folders = {}
        self.g_loadAll()

    def g_loadAll(self):
        """Load all Dashboards, Alerts, Folders"""
        # pylint: disable=E1123
        # Grafana lib does support timeout, but pylint does not know it.
        self.grafanaapi = GrafanaApi.from_url(url=self.config["grafana_host"], credential=self.config["grafana_api_key"], timeout=30)
        self.g_getDashboards()
        self.g_getFolders()
        self.g_getDataSources()

    def g_getDashboards(self):
        """Get dashboards from Grafana"""
        self.dashboards = {}
        failures = 0
        while failures < 3:
            try:
                for item in self.grafanaapi.search.search_dashboards():
                    folderTitle = item.get("folderTitle", "")
                    if folderTitle:
                        self.dashboards.setdefault(folderTitle, {})
                        self.dashboards[folderTitle][item["title"]] = item
                        self.dashboards[folderTitle][item["title"]]["url"] = f"{self.config['grafana_host']}/d/{item['uid']}/{item['slug']}"
                return
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to get dashboards: {ex}")
                time.sleep(1)
        raise Exception("Failed to get dashboards after 3 retries")

    def g_getDashboardByTitle(self, title, folderTitle):
        """Get dashboard by Title inside folder"""
        if folderTitle in self.dashboards and title in self.dashboards[folderTitle]:
            return self.dashboards[folderTitle][title]
        return {}

    def g_getDataSources(self):
        """Get all data sources"""
        failures = 0
        while failures < 3:
            try:
                self.datasources = {}
                for item in self.grafanaapi.datasource.list_datasources():
                    self.datasources[item["name"]] = item
                return
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to get datasources: {ex}")
                time.sleep(1)
        raise Exception("Failed to get datasources after 3 retries")

    def g_addNewDashboard(self, dashbJson):
        """Add new dashboard"""
        failures = 0
        while failures < 3:
            try:
                return self.grafanaapi.dashboard.update_dashboard(dashbJson)
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to create dashboard {dashbJson}: {ex}")
                time.sleep(1)
        raise Exception(f"Failed to create dashboard {dashbJson} after 3 retries")

    def g_getDashboardURL(self, title, folderTitle):
        """Get dashboard URL"""
        if folderTitle in self.dashboards and title in self.dashboards[folderTitle]:
            return self.dashboards[folderTitle][title]["url"]
        return None

    def g_deleteDashboard(self, title, folderTitle):
        """Delete dashboard"""
        if folderTitle in self.dashboards and title in self.dashboards[folderTitle]:
            failures = 0
            while failures < 3:
                try:
                    return self.grafanaapi.dashboard.delete_dashboard(self.dashboards[folderTitle][title]["uid"])
                except Exception as ex:
                    if "Dashboard not found" in str(ex):
                        # Dashboard already deleted
                        return True
                    failures += 1
                    self.logger.error(f"Failed to delete dashboard {title}: {ex}")
                    time.sleep(5)
        else:
            return False
        raise Exception(f"Failed to delete dashboard {title} after 3 retries")

    def g_createFolder(self, title):
        """Create Folder"""
        self.g_getFolders()
        if title in self.folders:
            return self.folders[title]
        failures = 0
        while failures < 3:
            try:
                return self.grafanaapi.folder.create_folder(title)
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to create folder {title}: {ex}")
                time.sleep(1)
        raise Exception(f"Failed to create folder {title} after 3 retries")

    def g_getFolders(self):
        """Get all folders"""
        failures = 0
        while failures < 3:
            try:
                self.folders = {}
                for item in self.grafanaapi.folder.get_all_folders():
                    self.folders[item["title"]] = item
                return
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to get folders: {ex}")
                time.sleep(1)
        raise Exception("Failed to get folders after 3 retries")

    def g_getFolderID(self, name):
        """Get folder ID by Name. Default None"""
        if name in self.folders:
            return self.folders[name]["id"]
        if name != "General":
            # General is default and not returned by Grafana API
            self.logger.warning(f"Folder {name} is not configured.")
        return None

    def _g_addAnnotation(self, **kwargs):
        """Add annotation for dashboard based on uid"""
        # Check that all params present;
        if not all([kwargs.get("dashboard_uid"), kwargs.get("panelId"), kwargs.get("time_from"), kwargs.get("time_to"), kwargs.get("tags"), kwargs.get("text")]):
            self.logger.error("Missing params for annotation")
            return {}
        return self.grafanaapi.annotations.add_annotation(
            dashboard_uid=kwargs["dashboard_uid"], panel_id=kwargs["panelId"], time_from=kwargs["time_from"], time_to=kwargs["time_to"], tags=kwargs["tags"], text=kwargs["text"]
        )

    def g_submitAnnotation(self, **kwargs):
        """Submit annotation"""
        dashbuid = kwargs["dashbInfo"]["uid"]
        submitinfo = kwargs["submitout"]
        # random int (to delay a bit the annotation to be after the submit time)
        # SiteRM might take longer time to start it
        # TODO, It would be nice to get back start time from SiteRM
        # and update it later (but that is currently not tracked in SiteRM.)
        # It reports only current state, and updateTime
        randdelaytime = random.randint(10, 30) * 1000
        time_from = submitinfo["submit_time"] * 1000 + randdelaytime
        time_to = submitinfo["submit_time"] * 1000 + submitinfo["time"] * 1000 if kwargs.get("timespan", True) else submitinfo["submit_time"] * 1000
        time_to += randdelaytime if kwargs.get("timespan", True) else 0
        annotation = {
            "dashboard_uid": dashbuid,
            "panelId": None,
            "time_from": time_from,
            "time_to": time_to,
            "tags": [f"{submitinfo['type'].capitalize()}"],
            "text": f"{submitinfo['type'].capitalize()} request submitted for {submitinfo['sitename']} {submitinfo['hostname']}: {submitinfo['submit_out']}",
        }
        # Loop for all annotation panels
        annotations = []
        for annid in kwargs["dashbInfo"]["annotation_panels"]:
            # Now we have panelId and loop for each panel and add annotation
            annotation["panelId"] = annid
            annout = self._g_addAnnotation(**annotation)
            # Need to get just ID;
            annotations.append(annout.get("id"))
        return annotations

    def g_updateAnnotationEndTime(self, **kwargs):
        """Update annotation"""
        for annotation_id in kwargs.get("annotation_ids", []):
            self.grafanaapi.annotations.partial_update_annotation(annotation_id, time_to=kwargs["time_to"])
