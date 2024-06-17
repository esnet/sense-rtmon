#!/usr/bin/env python3
"""General Libraries for RTMon"""
import os
import json
from yaml import safe_load as yload
from yaml import safe_dump as ydump

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

def getConfig(logger=None):
    """Get Config"""
    if not os.path.isfile("/etc/rtmon.yaml"):
        if logger:
            logger.error("Config file /etc/rtmon.yaml does not exist.")
        raise Exception("Config file /etc/rtmon.yaml does not exist.")
    with open("/etc/rtmon.yaml", "r", encoding="utf-8") as fd:
        return yload(fd.read())
