import random
import multiprocessing
import signal
import time
from pcaspy import Driver, SimpleServer
from pcaspy.tools import ServerThread
import epics
from va import pvs

NOISELVL = 100e-9
INTERVAL = 0.1

def get_pv_database():
    area_structures = (pvs.li,pvs.tb,pvs.bo,pvs.ts,pvs.si,pvs.As)
    my_database = dict()
    for ArS in area_structures:
        pv_database = ArS.record_names.get_database()
        for pv_name, value in pv_database.items():
            # value.update({'scan':0.5})
            parts = ArS.device_names.split_name(pv_name)
            if parts['Discipline'] == 'DI' and parts['Device'] == 'BPM':
                my_database[pv_name] = value
    return my_database


class MyDriver(Driver):

    def __init__(self,pv_database):
        super().__init__()
        self.pv_database = dict()
        for pv_name in pv_database.keys():
            pv = epics.PV('VA2-' + pv_name)
            # pv.add_callback(self.onChanges)
            self.pv_database[pv_name] = pv
            self.setParam(pv_name,pv.get())
        self.updatePVs()

    # Not used right now. It is usefull to add a callback to a pv when processing is not needed
    def onChanges(self,pvname=None,value=None, **kwargs):
        self._add_noise(pvname[4:], value)
        self.updatePVs()

    def read(self, reason):
        return super().read(reason)

    def write(self,reason,value):
        return True

    def process(self):
        for pv_name, pv in self.pv_database.items():
            self._add_noise(pv_name, pv.get())
        self.updatePVs()

    def _add_noise(self,pv_name, value):
        if value is None: return
        if isinstance(value,(int,float)):
            value += NOISELVL * random.uniform(-0.5,0.5)
        else:
            for i in range(len(value)): value[i] += NOISELVL * random.uniform(-0.5,0.5)
        self.setParam(pv_name,value)

if __name__ == '__main__':
    stop_event = multiprocessing.Event()
    stop_now = lambda x,y:stop_event.set()
    signal.signal(signal.SIGINT,stop_now)

    pv_database = get_pv_database()

    server = SimpleServer()
    server.createPV('', pv_database)
    server_thread = ServerThread(server)
    driver = MyDriver(pv_database)

    server_thread.start()
    while not stop_event.is_set():
        driver.process()
        time.sleep(INTERVAL)
    server_thread.stop()
