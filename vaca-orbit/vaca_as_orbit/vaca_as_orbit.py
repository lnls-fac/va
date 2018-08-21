#!/usr/bin/env python3
"""IOC Module."""

import os as _os
import logging as _log
import pcaspy as _pcaspy
import pcaspy.tools as _pcaspy_tools
import signal as _signal
import siriuspy.util as _util
from siriuspy.envars import vaca_prefix as _vaca_prefix
from .main import App as _App

stop_event = False
__version__ = _util.get_last_commit_hash()


def _stop_now(signum, frame):
    _log.info('SIGNAL received')
    global stop_event
    stop_event = True


def _attribute_access_security_group(server, db):
    for k, v in db.items():
        if k.endswith(('-RB', '-Sts', '-Cte', '-Mon')):
            v.update({'asg': 'rbpv'})
    path_ = _os.path.abspath(_os.path.dirname(__file__))
    server.initAccessSecurityFile(path_ + '/access_rules.as')


class _PCASDriver(_pcaspy.Driver):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.app.driver = self

    def read(self, reason):
        _log.debug("Reading {0:s}.".format(reason))
        return super().read(reason)

    def write(self, reason, value):
        self.app.write(reason, value)
        return True


def run(acc='SI', debug=False):
    """Start the IOC."""
    _util.configure_log_file(debug=debug)
    _log.info('Starting...')

    # define abort function
    _signal.signal(_signal.SIGINT, _stop_now)
    _signal.signal(_signal.SIGTERM, _stop_now)

    # Creates App object
    _log.debug('Creating SOFB Object.')
    app = _App(acc=acc)
    _log.info('Generating database file.')
    db = app.get_database()
    PREFIX = acc.upper() + '-Glob:VA-Orbit:'
    db.update({PREFIX+'Version-Cte': {'type': 'string', 'value': __version__}})
    _util.save_ioc_pv_list(
                        ioc_name=acc.lower() + '-va-orbit',
                        prefix=('', _vaca_prefix), db=db)
    _util.print_ioc_banner('vaca-orbit', db, 'vaca-orbit', '0.2', _vaca_prefix)
    # create a new simple pcaspy server and driver to respond client's requests
    _log.info('Creating Server.')
    server = _pcaspy.SimpleServer()
    _log.info('Setting Server Database.')
    _attribute_access_security_group(server, db)
    server.createPV(_vaca_prefix, db)
    _log.info('Creating Driver.')
    _PCASDriver(app)

    # initiate a new thread responsible for listening for client connections
    server_thread = _pcaspy_tools.ServerThread(server)
    _log.info('Starting Server Thread.')
    server_thread.setDaemon(True)
    server_thread.start()

    # main loop
    while not stop_event:
        app.process()

    _log.info('Stoping Server Thread...')
    # sends stop signal to server thread
    server_thread.stop()
    server_thread.join()
    _log.info('Server Thread stopped.')
    _log.info('Good Bye.')


if __name__ == '__main__':
    run()
