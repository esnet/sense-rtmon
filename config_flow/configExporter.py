import time
import sys
import hashlib
from urllib.request import urlopen, Request

SCRAPE_DURATION = 3

if len(sys.argv) <= 2:
	HOST = ""
	urlStart = "http://localhost"
else:
	HOST = str(sys.argv[2])
PORT = int(sys.argv[1])

urlBuilt = urlStart + ":" + str(PORT)
url = Request(urlBuilt,
              headers={'User-Agent': 'Mozilla/5.0'})

response = urlopen(url).read()

currentHash = hashlib.sha224(response).hexdigest()
print("Starting listen on SENSE-O served config...")
while True:
    try:
        # perform the get request and store it in a var
        print("Scraping latest config...")
        response = urlopen(url).read()
 
        # create a hash
        currentHash = hashlib.sha224(response).hexdigest()
 
        time.sleep(SCRAPE_DURATION)
 
        # perform the get request
        response = urlopen(url).read()
 
        # create a new hash
        newHash = hashlib.sha224(response).hexdigest()
 
        # check if new hash is same as the previous hash
        if newHash == currentHash:
            print("\n----------------------------")
            print("No flow description changes.")
            print("----------------------------\n")
            continue
        # if something changed in the hashes
        else:
            # notify
            print("\n----------------------------------------------------------------------")
            print("Flow description has changed! Propogating changes to site exporters...")
            print("----------------------------------------------------------------------\n")
            # again read the website
            response = urlopen(url).read()
 
            # create a hash
            currentHash = hashlib.sha224(response).hexdigest()
 
            continue
 
    except Exception as e:
        print("error")