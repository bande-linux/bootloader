#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
import sys, pathlib, time
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from unboot.setup import *

from unboot.fw.isp_base import ISP
from unboot.fw.isp.isp_vid import ISPFrameReceiver


isp = ISP(u)
isp.boot()

rcver = ISPFrameReceiver(isp)
rcver.stream()  # Press 'Enter' to exit stream
