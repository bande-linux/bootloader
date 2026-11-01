# Backlog

## ANE on the M2 mini (t8112)

Plan and sources: [docs/ane.md](../docs/ane.md). Phases A to G, first milestone is phase B: the
fp16 add from `proxyclient/experiments/ane.py` returns 3.0 on the mini, 100 runs without a hang
or DART fault.

- [ ] A. t8112 ADT facts, ADT-driven `fw/ane.py`, H14 `add.hwx` compiled on the host
- [ ] B. Power up the ANE and run the add through proxyclient
- [ ] C. `hv/trace_ane.py` and a macOS trace, only if B stalls
- [ ] D. Port `eiln/ane` to v7.3 and t8112 as a patch in the kernel repo
- [ ] E. One CoreML-compiled model matches CoreML output on Linux
- [ ] F. whisper.cpp encoder on the ANE
- [ ] G. Open task-descriptor compiler

## Noticed in passing

- `import unboot.hw.ane` fails: `ImportError: cannot import name 'DARTRegs' from
  'unboot.hw.dart'`. `hw/ane.py` imports a name `hw/dart.py` no longer defines, so
  `experiments/ane.py` cannot start.
