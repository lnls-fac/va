#!/usr/bin/env python3

import time
import os
import sys
import subprocess

_FACCODE = os.environ.get('FACCODE')
_CURRDIR = os.getcwd()

def run_vaca():
    global pp1
    print('init vaca process...')
    server = os.path.join(_FACCODE, 'va', 'server.py')
    cmd_string = server + ' VA- ' + ' > ' + os.path.join(_CURRDIR, 'vaca.log') + ' 2>&1'
    subprocess.Popen(cmd_string, shell=True, executable='/bin/bash')

def run_viocs(ioc):
    print('init ' + ioc + ' vioc...')
    base_folder = os.path.join(_FACCODE, 'va', 'viocs', ioc)
    app_folder  = os.path.join(base_folder, ioc+'App', 'src' , 'O.linux-x86_64')
    boot_folder = os.path.join(base_folder, 'iocBoot', 'ioc'+ioc)
    cmd_string  = 'cd ' + boot_folder + '; ' + \
                  os.path.join(app_folder, ioc) + ' ' + os.path.join(boot_folder, 'st.cmd') + \
                  ' > ' + os.path.join(_CURRDIR, ioc+'.log') + ' 2>&1'
    subprocess.Popen(cmd_string, shell=True, executable='/bin/bash')

def run_si_current(): run_viocs('si_current')
def run_si_bpms(): run_viocs('si_bpms')
def run_si_lifetime(): run_viocs('si_lifetime')
def run_si_ps(): run_viocs('si_ps')
def run_si_tune(): run_viocs('si_tune')

if __name__ == '__main__':

    if _FACCODE is None:
        print('environment variable "FACCODE" is not defined!')
        sys.exit()

    print('pid: ', os.getpid())

    run_vaca()
    run_si_current()
    run_si_lifetime()
    run_si_bpms()
    run_si_ps()
    run_si_tune()

    # loops indefinitely
    while True: time.sleep(10)
