#!/usr/bin/env python3
"""General Libraries for RTMon"""
import os
import json
import time
import uuid
import hashlib
from datetime import datetime, timezone
import requests
from yaml import safe_load as yload
from yaml import safe_dump as ydump

def _processName(name):
    """Process Name for Mermaid and replace all special chars with _"""
    for repl in [[" ", "_"], [":", "_"], ["/", "_"], ["-", "_"], [".", "_"], ["?", "_"]]:
        name = name.replace(repl[0], repl[1])
    return name

def getUTCnow():
    """Get UTC Time."""
    return int(datetime.now(timezone.utc).timestamp())

def getUUID(inputstr):
    """Generate UUID from Input Str"""
    hashObject = hashlib.sha256(inputstr.encode('utf-8'))
    hashHex = hashObject.hexdigest()
    customUUID = str(uuid.UUID(hashHex[:32]))
    # Grafana allows max 40 chars for UUID
    return customUUID[:40]

def loadFileJson(filename, logger):
    """Load File"""
    with open(filename, 'rb') as fd:
        try:
            return json.loads(fd.read())
        except json.JSONDecodeError as ex:
            logger.error('Error in loading file: %s', ex)
    return {}

def dumpFileJson(filename, data, logger):
    """Dump File"""
    with open(filename, 'wb') as fd:
        try:
            fd.write(json.dumps(data).encode('utf-8'))
        except json.JSONDecodeError as ex:
            logger.error('Error in dumping file: %s', ex)
    return {}

def loadJson(data, logger):
    """Load JSON"""
    if isinstance(data, (dict, list)):
        return data
    try:
        return json.loads(data)
    except json.JSONDecodeError as ex:
        logger.error('Error in loading json dict: %s', ex)
    return {}

def dumpJson(data, logger):
    """Dump JSON"""
    try:
        return json.dumps(data)
    except json.JSONDecodeError as ex:
        logger.error('Error in dumping json dict: %s', ex)
    return {}

def dumpYaml(data, logger):
    """Dump YAML"""
    try:
        return ydump(data, default_flow_style=False)
    except json.JSONDecodeError as ex:
        logger.error('Error in dumping yaml dict: %s', ex)
    return {}

def loadYaml(data, logger):
    """Load YAML"""
    if isinstance(data, (dict, list)):
        return data
    try:
        return yload(data)
    except Exception as ex:
        if logger:
            logger.error('Error in loading yaml dict: %s', ex)
            logger.error('Data: %s', data)
            logger.error('Data type: %s', type(data))
        else:
            print('Error in loading yaml dict: %s', ex)
            print('Data: %s', data)
            print('Data type: %s', type(data))
    return {}

def getConfig(logger=None):
    """Get Config"""
    if not os.path.isfile("/etc/rtmon.yaml"):
        if logger:
            logger.error("Config file /etc/rtmon.yaml does not exist.")
        raise Exception("Config file /etc/rtmon.yaml does not exist.")
    with open("/etc/rtmon.yaml", "r", encoding="utf-8") as fd:
        return loadYaml(fd.read(), logger)

def getWebContentFromURL(url, logger, raiseEx=True):
    """GET from URL"""
    retries = 3
    out = {}
    while retries > 0:
        retries -= 1
        try:
            out = requests.get(url, timeout=60)
            return out
        except requests.exceptions.RequestException as ex:
            logger.error(f"Got requests.exceptions.RequestException: {ex}. Retries left: {retries}")
            if raiseEx and retries == 0:
                raise
            out = {}
            out['error'] = str(ex)
            out['status_code'] = -1
            time.sleep(5)
    return out

def escape(invalue):
    """Escape special characters for regex matching"""
    return invalue.replace("+", "[+]")

class ExceptionTemplate(Exception):
    """Exception template."""
    def __call__(self, *args):
        return self.__class__(*(self.args + args))
    def __str__(self):
        return ': '.join(self.args)

class SENSEOFailure(ExceptionTemplate):
    """Not Found error."""
