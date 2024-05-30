#!/usr/bin/env python3
"""General Libraries for RTMon"""
import os
import json
import logging
from logging import StreamHandler
from yaml import safe_load as yload
from yaml import safe_dump as ydump

def getStreamLogger(logLevel='DEBUG'):
    """ Get Stream Logger """
    levels = {'FATAL': logging.FATAL,
              'ERROR': logging.ERROR,
              'WARNING': logging.WARNING,
              'INFO': logging.INFO,
              'DEBUG': logging.DEBUG}
    logger = logging.getLogger()
    handler = StreamHandler()
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="%a, %d %b %Y %H:%M:%S")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(levels[logLevel])
    return logger

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

def getConfig(logger):
    """Get Config"""
    if not os.path.isfile("/etc/rtmon.yaml"):
        logger.error("Config file /etc/rtmon.yaml does not exist.")
        raise Exception("Config file /etc/rtmon.yaml does not exist.")
    with open("/etc/rtmon.yaml", "r", encoding="utf-8") as fd:
        return yload(fd.read())
