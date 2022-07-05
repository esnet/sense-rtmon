#! /bin/bash
arp -a > ./arpFiles/arpOut-.txt
python3 convertARP.py ./arpFiles/arpOut-.txt ./jsonFiles/arpOut-.json