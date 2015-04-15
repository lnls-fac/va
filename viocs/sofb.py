#!/usr/bin/env python3
import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")

pvs = ['SI_BPM', 'BO_BPM']
for i in range(len(pvs)):
    v = proxy.read_pv(pvs[i])
    print(pvs[i], v)
