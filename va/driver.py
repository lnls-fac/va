
import time
import threading
from pcaspy import Driver


class PCASDriver(Driver):
    def  __init__(self, stop_event):
        super().__init__()
        self._stop_event = stop_event

    def process(self):
        pass

    def read(self, reason):
        utils.log('read',reason,c='yellow')
        return super().read(reason)

    def write(self, reason, value):
        pass


class DriverThread(threading.Thread):

    def __init__(self, driver, stop_event):
        self._driver = driver
        self._stop_event = stop_event
        super().__init__(target=self._main)

    def _main(self):
        while True:
            if self._stop_event.is_set():
                break
            time.sleep(0.1)
            # self._driver.process()
            # if self._stop_event.is_set():
            #     print('Stop_event is set')
            #     for process in self._driver._model_process_list:
            #         process.join()
            #     break
