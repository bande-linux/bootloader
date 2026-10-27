#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from unboot.setup import *
from unboot.hw.pmu import PMU

PMU(u).reset_panic_counter()
