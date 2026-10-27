#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from unboot.setup import *
from unboot.constructutils import Ver
from unboot.utils import *

Ver.set_version(u)

from unboot.shell import run_shell

from unboot.fw.agx import Agx

p.pmgr_adt_power_enable("/arm-io/gfx-asc")
p.pmgr_adt_power_enable("/arm-io/sgx")

agx = Agx(u)
agx.verbose = 10

#agx.uat.dump(0)

agx.build_initdata()

run_shell(globals(), msg="Have fun!")
