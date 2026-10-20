#!/usr/bin/env python3
"""Offline checks for the renew guard in RTMonWorker.renew_exe.

No Grafana, no SENSE-O, no network. renew_exe's first decision is whether the
instance and manifest it has on hand are usable, and that decision is what
separates "render from what we stored" from "go ask SENSE-O again". Both
branches are reachable with nothing but a stub, so this checks the guard
directly rather than standing up a worker.

Why this is worth a test: s_getManifest returns {} when the orchestrator
cannot answer, submit_exe persists it, and _taskAccept then moves the entry to
renew because the instance itself reads READY. If renew_exe tests for key
presence it accepts that {} and builds a dashboard from nothing - the path
walk raises KeyError: 'Ports' - and because the entry stays in renew, no later
cycle ever re-fetches. The loop does not recover even after the orchestrator
does.

Run from the repository root:

    python3 test/test_renew.py

Exits non-zero on the first failure and prints what failed.
"""

# linter.sh formats with 'pyink -l 200' and then checks with pylint's 120
# column limit, so the formatter re-joins lines the checker then rejects.
# test_archify.py and the RTMon modules resolve that the same way.
# pylint: disable=line-too-long

import importlib.abc
import importlib.util
import logging
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "autogole-api", "src", "python"))


# The clients worker.py imports at module scope. They are deployment
# dependencies - present in the image, not necessarily on a developer's
# machine - and renew_exe's guard touches none of them, so a bare checkout
# should still be able to run this file. Only names that are genuinely absent
# are stood in for; an installed package is always preferred.
_OPTIONAL = ("sense", "grafana_client", "diagrams", "prometheus_api_client", "psutil", "yaml", "requests")


class _StubModule(types.ModuleType):
    """A module whose every attribute is a fresh empty class.

    Enough for `from x import Y` to succeed at import time. Anything that
    actually called Y would get a class with no methods rather than a working
    client, which fails loudly - the tests below never reach that far.
    """

    # One public method is the whole interface: a module is not a class with a
    # useful API, it is a namespace that answers attribute lookups.
    # pylint: disable=too-few-public-methods

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = type(name, (), {})
        setattr(self, name, value)
        return value


class _StubFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Resolves the absent clients, and nothing else, to _StubModule.

    Appended to sys.meta_path, so it is consulted only after every real
    finder has declined: an installed package always wins.
    """

    def find_spec(self, fullname, path=None, target=None):
        """Claim a submodule of an absent client, decline everything else."""
        del path, target
        if fullname.split(".")[0] not in _OPTIONAL:
            return None
        return importlib.util.spec_from_loader(fullname, self, is_package=True)

    def create_module(self, spec):
        """Hand back a _StubModule instead of a plain one."""
        module = _StubModule(spec.name)
        # Set here rather than in _StubModule.__init__ because importlib owns
        # the construction: a package needs __path__ for its submodules to be
        # importable, and this is where the module becomes one.
        module.__path__ = []  # pylint: disable=attribute-defined-outside-init
        return module

    def exec_module(self, module):
        """Nothing to execute: the module's attributes are made on demand."""


def _install_stubs():
    """Fabricate the optional clients that this machine does not have."""
    missing = []
    for name in _OPTIONAL:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        print(f"Note: standing in for absent packages: {', '.join(missing)}")
        sys.meta_path.append(_StubFinder())


FAILURES = []


def check(condition, message):
    """Record a pass or a failure and keep going within the test."""
    if condition:
        print(f"  ok   {message}")
        return True
    print(f"  FAIL {message}")
    FAILURES.append(message)
    return False


class _Stub:
    """Just enough of a worker for renew_exe's guard to run.

    renew_exe is called unbound with one of these as self. Reaching anything
    beyond the guard means the guard let the entry through, so t_createTemplate
    raises rather than returning: the tests below assert on which of the two
    paths was taken, and a silent third one would be the bug.
    """

    def __init__(self):
        self.logger = logging.getLogger("renew-stub")
        self.logger.addHandler(logging.NullHandler())
        self.resubmitted = False
        self.rendered = False

    def submit_exe(self, filename, fout):
        """The re-fetch path. Records that it was taken."""
        del filename, fout
        self.resubmitted = True

    def t_createTemplate(self, *args, **kwargs):
        """The render path. Records it, then stops the test here.

        Signature copied from the real one, which is (*args, **kwargs) for a
        reason: renew_exe calls it as t_createTemplate(instance, manifest,
        **fout), and fout carries an "instance" key of its own, so a named
        first parameter would collide.
        """
        del args, kwargs
        self.rendered = True
        raise AssertionError("rendered")


def run(fout):
    """Call the real renew_exe against a stub and report which path it took.

    The import is here, not at module scope, because the path and the stand-in
    clients have to be in place before RTMon.worker can be imported at all,
    and an import after that setup is a module-level import out of order.
    test_archify.py imports its subjects from inside a function for the same
    reason.
    """
    from RTMon.worker import RTMonWorker  # pylint: disable=import-outside-toplevel

    stub = _Stub()
    try:
        RTMonWorker.renew_exe(stub, "rtmon-debug-test", fout)
    except AssertionError as ex:
        if str(ex) != "rendered":
            raise
    return stub


def test_empty_manifest_is_refetched():
    """An empty manifest goes back to submit, which is what re-fetches."""
    print("Empty manifest:")
    stub = run({"state": "renew", "referenceUUID": "abc", "instance": {"state": "CREATE - READY"}, "manifest": {}})
    check(stub.resubmitted, "submit_exe is called")
    check(not stub.rendered, "no dashboard is built from an empty manifest")


def test_empty_instance_is_refetched():
    """Same for the instance, for the same reason."""
    print("Empty instance:")
    stub = run({"state": "renew", "referenceUUID": "abc", "instance": {}, "manifest": {"Ports": {}}})
    check(stub.resubmitted, "submit_exe is called")
    check(not stub.rendered, "no dashboard is built from an empty instance")


def test_missing_keys_are_refetched():
    """The original case the guard was written for still holds."""
    print("Absent keys:")
    stub = run({"state": "renew", "referenceUUID": "abc"})
    check(stub.resubmitted, "submit_exe is called")
    check(not stub.rendered, "no dashboard is built with nothing stored")


def test_real_data_is_rendered():
    """And the guard does not stand in the way of a usable entry."""
    print("Populated entry:")
    stub = run({"state": "renew", "referenceUUID": "abc", "instance": {"state": "CREATE - READY"}, "manifest": {"Ports": {"a": {}}}})
    check(stub.rendered, "t_createTemplate is called")
    check(not stub.resubmitted, "submit_exe is not called")


def main():
    """Run every check and exit non-zero if any of them failed."""
    logging.disable(logging.CRITICAL)
    _install_stubs()
    test_empty_manifest_is_refetched()
    test_empty_instance_is_refetched()
    test_missing_keys_are_refetched()
    test_real_data_is_rendered()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("All renew guard checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
