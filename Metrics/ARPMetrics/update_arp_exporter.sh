#! /bin/bash
arp -a > $PWD/arpFiles/arpOut-.txt
python3 $PWD/convertARP.py $PWD/arpFiles/arpOut-.txt $PWD/jsonFiles/arpOut-.json