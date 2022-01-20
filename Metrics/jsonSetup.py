#!/usr/bin/env python3

import os
import subprocess

loc = str(os.getcwd())
runCmd = "docker run -v "+ loc +"/data.json:/data.json json-exporter"
subprocess.run("docker build -t json-exporter .",shell=True)
subprocess.run(runCmd, shell=True)
