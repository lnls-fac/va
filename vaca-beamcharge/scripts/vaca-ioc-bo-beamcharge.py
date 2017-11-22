#!/usr/local/bin/python-sirius -u
"""Beam Charge Simulation IOC executable."""

from vaca_beamcharge import vaca_beamcharge as ioc_module

ioc_module.run("BO")
