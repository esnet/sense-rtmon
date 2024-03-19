import subprocess
import logging
import time
import json
import sys
import requests
import re 
import os
import glob
import datetime
from time import gmtime, strftime
from sense.client.workflow_combined_api import WorkflowCombinedApi
from sense.client.discover_api import DiscoverApi

def fetch_data():
    response = ""
    response = DiscoverApi().discover_service_instances_get()
    response = DiscoverApi().discover_service_instances_get()
    print("Response Sucessful")
    
    if response == "":
        logging.error("No Data")
       
    
    data = json.loads(response)
    
    return data

fetch_data()