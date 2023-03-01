# erase all urls on a pushgateway
import requests
import sys
from bs4 import BeautifulSoup
import re

if len(sys.argv) == 1:
    # Set the URL of the Pushgateway
    pushgateway_url = 'http://198.124.151.8:9091'
else:
    if "http" in sys.argv[1]:
        pushgateway_url = sys.argv[1]
    else:
        pushgateway_url = f"http://{sys.argv[1]}"

confirm = input("This action will remove all metrics on this pushgateway and it's irrevertible. Do you want to proceed? (y/n): ")
if confirm.lower() != "y":
    print("Okay, Operation Cancelled.")
    exit(0)

print("Procedding...")
    
main_page_url = f'{pushgateway_url}/'
response = requests.get(main_page_url)

# Check if the request was successful
if response.status_code != 200:
    print(f'Error getting main page from Pushgateway: {response.status_code} {response.reason}')
    exit(1)

# Use BeautifulSoup to parse the HTML and extract all span elements
soup = BeautifulSoup(response.text, 'html.parser')
span_elements = soup.find_all('span')

new_text = []
for ele in span_elements:
    if "badge badge-" in str(ele):
        # store from warning to light
        if "warning" in str(ele):
            block = []
            under_block = True
            send = False
        
        if "light" in str(ele):
            send = True
            under_block = False
        
        if under_block:    
            block.append(ele)
        
        if send:
            new_text.append(block)        

# only keep instance related 
new_text = [x for x in new_text if "instance" in str(x)]
# remove non group related urls
new_text = [x for x in new_text if len(x) >1]
# remove duplicates
new_text = [list(t) for t in set(tuple(x) for x in new_text)]

for block in new_text:
    matches = re.findall(r'>\s*(.*?)\s*<', str(block))
    matches = [x for x in matches if "=" in x]
    url = ""
    
    for item in matches:
        left, right = item.split("=")
        right = right.replace('"', '')
        url += f"{left}/{right}/"

    url = url.rstrip("/") # remove the trailing slash
    delete_url = f'{pushgateway_url}/metrics/{url}'
    print("Deleting the following group: ")
    print(delete_url)
    print("")
    # delete the url (same as Delete Group button)
    requests.delete(delete_url)
