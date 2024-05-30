#!/usr/bin/env python3
"""Grafana API for Autogole SENSE RTMon"""

from grafana_client import GrafanaApi

class GrafanaAPI():
    """Autogole SENSE Grafana RTMon API"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        self.grafanaapi = GrafanaApi.from_url(
                                     url=self.config['grafana_host'],
                                     credential=self.config['grafana_api_key'])
        self.datasources = {}
        self.dashboards = {}
        self.folders = {}
        self.g_loadAll()

    def g_loadAll(self):
        """Load all Dashboards, Alerts, Folders"""
        self.g_getDashboards()
        self.g_getFolders()
        self.g_getDataSources()


    def g_getDashboards(self):
        """Get dashboards from Grafana"""
        self.dashboards = {}
        for item in self.grafanaapi.search.search_dashboards():
            self.dashboards[item['title']] = item

    def g_getDashboardByTitle(self, title):
        """Get dashboard by Title"""
        if title in self.dashboards:
            return self.dashboards[title]
        return {}

    def g_getDataSources(self):
        """Get all data sources"""
        for item in self.grafanaapi.datasource.list_datasources():
            self.datasources[item['name']] = item

    def g_addNewDashboard(self, dashbJson):
        """Add new dashboard"""
        return self.grafanaapi.dashboard.update_dashboard(dashbJson)

    def g_deleteDashboard(self, title):
        """Delete dashboard"""
        if title in self.dashboards:
            return self.grafanaapi.dashboard.delete_dashboard(self.dashboards[title]['uid'])
        return False

    def g_createFolder(self, title):
        """Create Folder"""
        self.g_getFolders()
        if title in self.folders:
            return self.folders[title]
        return self.grafanaapi.folder.create_folder(title)

    def g_getFolders(self):
        """Get all folders"""
        for item in self.grafanaapi.folder.get_all_folders():
            self.folders[item['title']] = item

    def g_getFolderID(self, name):
        """Get folder ID by Name. Default None"""
        if name in self.folders:
            return self.folders[name]['id']
        if name != 'General':
            # General is default and not returned by Grafana API
            self.logger.warning(f"Folder {name} is not configured.")
        return None
