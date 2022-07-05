#! /bin/bash
arp -a > .ARPMetrics/arpFiles/arpOut-.txt
python3 convertARP.py .ARPMetrics/arpFiles/arpOut-.txt ./jsonFiles/arpOut-.json