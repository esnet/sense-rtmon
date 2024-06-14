#!/usr/bin/env python3
"""Grafana API for Autogole SENSE RTMon"""
import time
from grafana_client import GrafanaApi

class GrafanaAPI():
    """Autogole SENSE Grafana RTMon API"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.grafanaapi = GrafanaApi.from_url(
                                     url=self.config['grafana_host'],
                                     credential=self.config['grafana_api_key'],
                                     timeout=30)
        self.datasources = {}
        self.dashboards = {}
        self.folders = {}
        self.g_loadAll()

    def g_loadAll(self):
        """Load all Dashboards, Alerts, Folders"""
        self.grafanaapi = GrafanaApi.from_url(
                                     url=self.config['grafana_host'],
                                     credential=self.config['grafana_api_key'],
                                     timeout=30)
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
                    self.dashboards[item['title']] = item
                return
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to get dashboards: {ex}")
                time.sleep(1)
        raise Exception("Failed to get dashboards after 3 retries")

    def g_getDashboardByTitle(self, title):
        """Get dashboard by Title"""
        if title in self.dashboards:
            return self.dashboards[title]
        return {}

    def g_getDataSources(self):
        """Get all data sources"""
        failures = 0
        while failures < 3:
            try:
                self.datasources = {}
                for item in self.grafanaapi.datasource.list_datasources():
                    self.datasources[item['name']] = item
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

    def g_deleteDashboard(self, title):
        """Delete dashboard"""
        if title in self.dashboards:
            failures = 0
            while failures < 3:
                try:
                    return self.grafanaapi.dashboard.delete_dashboard(self.dashboards[title]['uid'])
                except Exception as ex:
                    failures += 1
                    self.logger.error(f"Failed to delete dashboard {title}: {ex}")
                    time.sleep(1)
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
                    self.folders[item['title']] = item
                return
            except Exception as ex:
                failures += 1
                self.logger.error(f"Failed to get folders: {ex}")
                time.sleep(1)
        raise Exception("Failed to get folders after 3 retries")


    def g_getFolderID(self, name):
        """Get folder ID by Name. Default None"""
        if name in self.folders:
            return self.folders[name]['id']
        if name != 'General':
            # General is default and not returned by Grafana API
            self.logger.warning(f"Folder {name} is not configured.")
        return None
