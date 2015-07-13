#!/usr/bin/env python3

import time
import signal
import queue
import multiprocessing


INTERVAL = 0.1
TIMEOUT = 1.0


class Model(object):

    def __init__(self, q_in, q_out, model_module=None, all_pvs=None):#, log_func=utils.log):
        self.q_in = q_in
        self.q_out = q_out
        self.model_module = model_module
        self.all_pvs = all_pvs
        # self.log = log_func

    def process(self):
        self.get_pvs_from_queue_in()
        # self.update()
        # self.set_pvs_to_queue_out()

    def get_pvs_from_queue_in(self):
        start_time = time.time()
        while (time.time()-start_time < INTERVAL/2) and not self.q_in.empty():
            try: # ok?
                pv_name, value = self.q_in.get()
                self.set_pv(pv_name, value)
            except queue.Empty:
                print('Error: tried to read from empty queue')
        # print('Exiting get_pvs_from_queue_in')

    def set_pv(self, pv_name, value):
        print('SET PV:', pv_name, value)
