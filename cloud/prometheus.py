# import json
# import os
# import sys
# import re 
# import cloud_functions

# # read yml file
# data,file_name = cloud_functions.read_yml_file("config_cloud",sys.argv,1,1)
                
# # read in promethues.yml file 
# with open('prometheus.yml', 'r') as file:
#     write_data = file.readlines()

# new_data = []
# hostip = data['hostIP']
# for each_line in write_data:
#     each_line = re.sub("'.*:9090", f"'{hostip}:9090", each_line) # different format for 9090
#     each_line = re.sub("- .*:9091", f"- {hostip}:9091", each_line)
#     each_line = re.sub("- .*:9469", f"- {hostip}:9469", each_line)
#     new_data.append(each_line)
    
# with open('prometheus.yml', 'w') as file:
#     file.writelines(new_data)
