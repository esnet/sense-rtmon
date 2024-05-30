#!/usr/bin/env python3
"""This part of code is taken from:
https://web.archive.org/web/20160305151936/http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
Please respect developer (Sander Marechal) and always keep a reference to URL and also as kudos to him
Changes applied to this code:
    Dedention (Justas Balcas 07/12/2017)
    pylint fixes: with open, split imports, var names, old style class (Justas Balcas 07/12/2017)
"""
import os
import sys
import time
import argparse
import traceback
import atexit
import psutil
from SNMPMon.utilities import getConfig
from SNMPMon.utilities import getTimeRotLogger

def getParser(description):
    """Returns the argparse parser."""
    oparser = argparse.ArgumentParser(description=description,
                                      prog=os.path.basename(sys.argv[0]), add_help=True)
    oparser.add_argument('--action', dest='action', default='',
                         help='Action - start, stop, status, restart service.')
    oparser.add_argument('--foreground', action='store_true',
                         help="Run program in foreground. Default no")
    oparser.set_defaults(foreground=False)
    oparser.add_argument('--logtostdout', action='store_true',
                         help="Log to stdout and not to file. Default false")
    oparser.add_argument('--onetimerun', action='store_true',
                         help="Run once and exit from loop (Only for start). Default false")
    oparser.add_argument('--devicename', dest='devicename', default='',
                         help='Device name to start the process. Only for threading.')
    oparser.set_defaults(logtostdout=False)
    return oparser

def validateArgs(inargs):
    """Validate arguments."""
        # Check port
    if inargs.action not in ['start', 'stop', 'status', 'restart']:
        raise Exception(f"Action '{inargs.action}' not supported. Supported actions: start, stop, status, restart")

class Daemon():
    """A generic daemon class.
    Usage: subclass the Daemon class and override the run() method.
    """

    def __init__(self, component, inargs):
        self.component = component
        self.inargs = inargs
        self.runCount = 0
        self.pidfile = f'/tmp/nsi-snmpmon-{component}.pid'
        if self.inargs.devicename:
            self.pidfile = f'/tmp/nsi-snmpmon-{component}-{self.inargs.devicename}.pid'
        self.config = getConfig('/etc/snmp-mon.yaml')
        self.logger = getTimeRotLogger(**self.config['logParams'])

    def daemonize(self):
        """do the UNIX double-fork magic, see Stevens' "Advanced Programming in
        the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16."""
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as ex:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (ex.errno, ex.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as ex:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (ex.errno, ex.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        with open('/dev/null', 'r', encoding='utf-8') as fd:
            os.dup2(fd.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+', encoding='utf-8') as fd:
            os.dup2(fd.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'a+', encoding='utf-8') as fd:
            os.dup2(fd.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+', encoding='utf-8') as fd:
            fd.write(f"{pid}\n")

    def delpid(self):
        """Remove pid file."""
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""
        # Check for a pidfile to see if the daemon already runs
        pid = None
        try:
            directory = os.path.dirname(self.pidfile)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(self.pidfile, 'r', encoding='utf-8') as fd:
                pid = int(fd.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    @staticmethod
    def __kill(pid):
        """Kill process using psutil lib"""
        def processKill(procObj):
            try:
                procObj.kill()
            except psutil.NoSuchProcess:
                pass
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return
        for proc in process.children(recursive=True):
            processKill(proc)
        processKill(process)

    def stop(self):
        """Stop the daemon."""
        # Get the pid from the pidfile
        pid = None
        try:
            with open(self.pidfile, 'r', encoding='utf-8') as fd:
                pid = int(fd.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        self.__kill(pid)
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def status(self):
        """Daemon status."""
        try:
            with open(self.pidfile, 'r', encoding='utf-8') as fd:
                pid = int(fd.read().strip())
                print(f'Application info: PID {pid}')
        except IOError:
            print('Is application running?')
            sys.exit(1)

    def command(self):
        """Execute a specific command to service."""
        if self.inargs.action == 'start' and self.inargs.foreground:
            self.start()
        elif self.inargs.action == 'start' and not self.inargs.foreground:
            self.run()
        elif self.inargs.action == 'stop':
            self.stop()
        elif self.inargs.action == 'restart':
            self.restart()
        elif self.inargs.action == 'status':
            self.status()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)

    def runLoop(self):
        """Return True if it is not onetime run."""
        if self.inargs.onetimerun and self.runCount == 0:
            return True
        if self.inargs.onetimerun and self.runCount > 0:
            return False
        return True

    def refreshThreads(self):
        """Refresh threads"""
        while True:
            try:
                runThreads = self.getThreads()
                return runThreads
            except:
                exc = traceback.format_exc()
                self.logger.critical("Exception!!! Error details:  %s", exc)
                time.sleep(5)

    def run(self):
        """Run main execution"""
        runThreads = self.refreshThreads()
        while self.runLoop():
            self.runCount += 1
            hadFailure = False
            try:
                for sitename, rthread in list(runThreads.items()):
                    self.logger.info('Start worker for %s site', sitename)
                    try:
                        rthread.startwork()
                    except:
                        hadFailure = True
                        exc = traceback.format_exc()
                        self.logger.critical("Exception!!! Error details:  %s", exc)
                if self.runLoop():
                    time.sleep(5)
            except KeyboardInterrupt as ex:
                self.logger.critical("Received KeyboardInterrupt: %s ", ex)
                sys.exit(3)
            if hadFailure:
                self.logger.info('Had Runtime Failure. Sleep for 30 seconds')
                if self.runLoop():
                    time.sleep(5)
                else:
                    sys.exit(4)

    @staticmethod
    def getThreads():
        """Overwrite this then Daemonized in your own class"""
        return {}
