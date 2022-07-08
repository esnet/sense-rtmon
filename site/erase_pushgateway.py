# erase all urls from this host (instance)
import json
import os
import requests

dir = str(os.getcwd())    
# delete previous urls
delete_file_path = dir + "../Metrics/ARPMetrics/jsonFiles/delete.json"
with open(delete_file_path,"rt") as fp:
# check if the file is empty
    if os.stat(delete_file_path).st_size != 0:
        load_delete = json.load(fp)
        for each_url in load_delete:
            requests.delete(each_url)
    delete_list = []
    