"""Define the driver that control the beam charge soft IOC."""
import sys as _sys
import signal as _signal

import pcaspy as _pcaspy
import pcaspy.tools as _pcaspy_tools

import vaca_beamcharge.pvs as _pvs
from . import main as _main
from siriuspy import util as _util


INTERVAL = 0.1
stop_event = False


def _stop_now(signum, frame):
    global stop_event
    print("Exiting")
    _sys.stdout.flush()
    _sys.stderr.flush()
    stop_event = True


class _PCASDriver(_pcaspy.Driver):
    """Driver used to read and write values to app."""

    def __init__(self):
        """Init app."""
        super().__init__()
        self.app = _main.App(self)

    def read(self, reason):
        """Read PV from DB."""
        value = self.app.read(reason)
        if value is None:
            val = super().read(reason)
            return val
        else:
            return value

    def write(self, reason, value):
        """Write to pv."""
        self.app.write(reason, value)


def run(section):
    """Main function."""
    _signal.signal(_signal.SIGINT, _stop_now)
    _signal.signal(_signal.SIGTERM, _stop_now)

    _pvs.ioc_setting(section)
    _main.App.init_class()

    # check if IOC is already running
    pvname = _pvs._PREFIX + next(iter(_main.App.pvs_database.keys()))
    running = _util.check_running_ioc(
        pvname=pvname, use_prefix=False, timeout=0.5)
    if running:
        print('Another ' + section + ' -beamcharge IOC is already running!')
        return

    server = _pcaspy.SimpleServer()
    server.createPV(_pvs._PREFIX, _main.App.pvs_database)

    pcas_driver = _PCASDriver()

    server_thread = _pcaspy_tools.ServerThread(server)
    server_thread.start()

    while not stop_event:
        pcas_driver.app.process(INTERVAL)

    server_thread.stop()
    server_thread.join()
