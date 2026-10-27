#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from unboot.setup import *
from unboot.ishell import run_ishell

run_ishell(globals(), msg="Have fun!")
