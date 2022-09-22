import sys
import re

# domain port ssl_certificate ssl_key

with open("./nginx/proxy_conf") as f:
    lines = f.readlines()

lines[0] = f"proxy_pass http://{str(sys.argv[1])}:{str(sys.argv[2])}/;\n"

with open("./nginx/proxy_conf", "w") as f:
    f.writelines(lines)
    
with open("./nginx/server_conf", "w") as f:
    f.write(f'''server_name {str(sys.argv[1])};
ssl_certificate     "{str(sys.argv[3])}";
ssl_certificate_key "{str(sys.argv[4])}";\n''')

# read in args.sh file
with open('docker-stack.yml', 'r') as file:
    write_data = file.readlines()

find_line1 = False
find_line2 = False 

stack_yml = []
for each_line in write_data:
    # replacing the correct port for Grafana
    # each_line = re.sub("      - .*:3000", f"      - {str(sys.argv[2])}:3000", each_line)
    # each_line = re.sub("      - 3000", f"      - {str(sys.argv[2])}", each_line)    
    
    # if find_line2: # replace secobd line key
    #     each_line = re.sub(".*", f"      - {str(sys.argv[4])}:{str(sys.argv[4])}", each_line)
    #     find_line2 = False
    
    if find_line1: # replace first line certificate
        each_line = re.sub(".*", f"      - {str(sys.argv[3])}:{str(sys.argv[3])}", each_line)
        find_line1 = False
        find_line2 = True
        
    # locating the line
    if "- $PWD/nginx/:/etc/nginx/conf.d/" in each_line:
        find_line1 = True 
    stack_yml.append(each_line)
      
with open('docker-stack.yml', 'w') as file:
    file.writelines(stack_yml)