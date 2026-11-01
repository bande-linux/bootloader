# Apple Neural Engine on the M2 Mac mini (t8112, J473)

Research and plan, October 2026. No experiment in this document has run on the M2 yet.
Statements marked **(guess)** are inference, not observation.

## Summary

- The only Linux ANE stack that ever ran is Eileen Yoon's `eiln/ane` (kernel module, `libane`,
  Python bindings) plus `eiln/anecc`. It covers M1 (t8103, H13) and M1 Pro/Max (t6000) only,
  last changed in 2023, and does not build on our v7.3 tree unmodified.
- That stack does **not** boot the ANE's RTKit firmware. The CPU programs the ANE task manager
  directly and takes the completion interrupt. If this holds on t8112, no Apple firmware is
  needed on Linux.
- No open compiler exists. Every working path runs models compiled by Apple's `ANECompiler`
  on macOS (`.hwx`) and converts them for Linux. `ANECompiler` on our M4 Pro host lists
  H13 to H17 targets, including `h14*` variants, and exports `ANECCompileOffline` and
  `kANEFTargetArchitectureKey`, so H14 models can probably be compiled here without the mini
  **(guess, untested)**.
- First milestone: run `add.hwx` (1 + 2 = 3 in fp16) on the M2 through proxyclient, as
  `experiments/ane.py` does on M1.

## 1. Prior art

| Work | What it covers | Chips | State | License |
|---|---|---|---|---|
| [eiln/ane](https://github.com/eiln/ane) | `drivers/accel`-style kernel module (`ane.ko`, `DRIVER_COMPUTE_ACCEL`, GEM BOs, DART mapping, task-manager submit, runtime PM), `libane` (C), Python bindings, matmul and SRGAN tests | `apple,t8103-ane`, `apple,t6000-ane` (H13) | Last commit `0dcea997` (2023-11-12). Out of tree, never submitted. `.remove` returns `int`, but `struct platform_driver::remove` is `void` in our tree (`include/linux/platform_device.h:280`), so it fails to build on v7.3 as is. DART code hardcodes t8020 registers. | MIT (`MODULE_LICENSE("Dual MIT/GPL")`) |
| [eiln/anecc](https://github.com/eiln/anecc) | `tohwx` (Objective-C, macOS, calls the private compiler) turns an `.mlmodel` into `.hwx`; `anecc` converts `.hwx` into the `.anec` container `libane` loads | as above | Last push 2023-06-20 | MIT |
| `proxyclient/unboot/{hw,fw}/ane.py`, `experiments/ane.py` (this repo, inherited from m1n1) | Python bring-up: static tunables, power-state writes, DART setup, task-queue enqueue, IRQ event readout, fp16 add | t8103, t6000/t6002 power-state addresses hardcoded | `import unboot.hw.ane` fails today (see backlog). Needs the `anect` pip package. | GPL-2.0-or-later (SPDX headers in the files) |
| [Eileen Yoon, ANE retrospective](https://eiln.github.io/posts/ane.html) (2026-08-10) | Architecture of the M1 ANE: 16 cores x 128 fp16 MAC lanes, 64 KiB kernel memory per core, 2 MiB shared L2 tile memory, three DMA engines, task manager with 8 queues, each with two descriptor slots and 32 BARs. Task descriptors are serialized register writes, about 628 bytes for a 1x1 convolution: "ANE has no ISA". Explains why the driver stopped: too specialised to justify upstreaming. | M1 (H13); bandwidth measured on M3 | Blog post | not stated |
| tinygrad `extra/accel/ane` | Early hwx parsing and private-API experiments on macOS | H13 era | Removed from tinygrad on 2025-06-08 (`3ece2e4b`); last real change `d0e75200` (2023-09-21) | MIT |
| [maderix/ANE](https://github.com/maderix/ANE), [Substack series](https://maderix.substack.com/p/inside-the-m4-apple-neural-engine) | Training on the ANE through `_ANEClient`, `_ANECompiler`, `_ANEInMemoryModelDescriptor`; about 32 MB on-chip SRAM limit; compiler leaks force process restarts | M4 (H16), macOS only | Active in 2026 | MIT |
| [Orion](https://github.com/mechramc/Orion), [arXiv 2603.06728](https://arxiv.org/abs/2603.06728) | Runtime and characterisation for small LLMs on the ANE without CoreML; reports INT8 being dequantised to fp16 before compute | M4 / M4 Max, macOS only | Active in 2026 | MIT |
| [AmiraniLabs/libane](https://github.com/AmiraniLabs/libane) | Graph IR, op fusion, direct dispatch from C++ and Python on macOS | macOS only | Active in 2026 | Apache-2.0 |
| [ANEForge, arXiv 2606.17090](https://arxiv.org/abs/2606.17090), [ane-guide](https://ane-guide.readthedocs.io/) | Python for direct ANE computation; a reference list of most work above | macOS only | 2026 | see repos |
| [hollance/neural-engine](https://github.com/hollance/neural-engine) | Community notes; per-device core counts and TOPS (M2: 16 cores, 15.8 TOPS) | all | maintained | MIT |
| [Wu, Black Hat Asia 2021](https://i.blackhat.com/asia-21/Friday-Handouts/as21-Wu-Apple-Neural_Engine.pdf) | Security view of the macOS/iOS stack: `aned`, `H11ANEIn` user client, `ANE_ProgramSendRequest`, firmware shipped as `Firmware/ane/h11_ane_fw_*.im4p` | H11 | talk | n/a |
| Asahi Linux | No ANE node or driver in any `asahi/bits/*` branch (checked `000-devicetree`); Asahi's ANE work is eiln's out-of-tree repo | | | |

Everything except eiln's stack and our proxyclient runs on macOS through private frameworks.
Those projects are useful for the compiler side (what the private compiler accepts, which ops
reach the ANE, performance limits) but contribute nothing to a Linux driver.

What macOS itself reveals, read on this host (macOS 27, M4 Pro):

- `AppleH11ANEInterface.kext` matches `IONameMatch = ane,t8020` with `IOClass = H11ANEIn` and
  starts it as an `RTBuddyService`: on macOS the ANE coprocessor runs RTKit firmware. Newer
  generations add per-SoC HAL kexts (`AppleT8132ANEHAL`, `AppleT6030ANEHAL`, ...); there is
  none for t8103 or t8112, which suggests H13 and H14 share the generic `ane,t8020` path
  **(guess)**.
- The dyld shared cache contains compiler target names `h13{c,d,g,p,s}`, `h14{c,d,g,p,s}`,
  `h15*`, `h16*`, `h17*`, plus `ANECCompileOffline` and `kANEFTargetArchitectureKey`.
  Which `h14` suffix is t8112 is not known **(guess: `h14g`)**.

## 2. M2 (t8112) facts

| Topic | Known | Unknown, and how to find out |
|---|---|---|
| Generation | M2 uses the A15-class 16-core ANE, H14; M1 is H13 (eiln's TD dumps are labelled "M1 h13"). The M(n) = H(n+12) mapping is consistent with every source. | Confirm from the ADT and from the `h14*` target the compiler picks for t8112. |
| ADT | proxyclient expects `/arm-io/ane` and `/arm-io/dart-ane` (three `reg` entries for the DART, multiple-die chips use `ane0`..`ane3`). macOS matches `ane,t8020`. | t8112 node names, `reg` layout, interrupts, power-state list. Source without the device: the `DeviceTree.j473ap.im4p` in the macOS IPSW for Mac14,3, extracted with `ipsw` (blacktop, MIT); or an ADT dump the hardware agent already has. |
| Device tree | `t8112-pmgr.dtsi` has only `ps_ane_sys` at `0x4a8`, parented to `ps_mmx`; `t8112.dtsi` has `pmp_report_ane_sys`. No ANE or ANE-DART node in `t8112.dtsi` or `t8112-j473.dts`. t8103 additionally has `ps_ane_sys_cpu` at `0xc000`, and proxyclient writes seven ANE power states at `0x23b70c000 + 8*n` on t8103. | t8112 equivalents of `ane_sys_cpu` and the seven sub-states. `tools/pmgr_adt2dt.py` on the t8112 ADT produces them. |
| Firmware | macOS boots the ANE ASC with RTKit firmware (`RTBuddyService`). `hw/ane.py` names the ASC (`ASC_IO_RVBAR`, `ASC_EDPRCR`) and RTKit ack registers. Firmware ships in the restore image as `Firmware/ane/h1x_ane_fw_*.im4p` (seen for H11, H13). | Whether t8112's task manager can be driven with the ASC off, as on M1 **(guess: yes, the same `ane,t8020` driver class covers both)**. File name for J473 **(guess: `h14_ane_fw_*.im4p`)**; only needed for the RTKit fallback or for reading tunables out of it. |
| DART | M1 ANE uses t8020 DARTs, three instances, and DMA fails unless DART1 and DART2 are given DART0's TTBR. eiln's driver and `fw/ane.py` both hardcode t8020 offsets. | t8112 uses `apple,t8110-dart` / `apple,t8112-dart` for every DART in `t8112.dtsi` **(guess: ANE too)**. Then the TTBR copy and TLB invalidation must be redone for t8110 (`proxyclient/unboot/hw/dart8110.py` already models it). Usable IOVA window (M1: `0x4000` .. `0xe0000000`). |
| Power | M1: `ane_sys` -> `ane_sys_cpu` -> seven sub-states, plus a static tunable list ("cost me a solid week"). | t8112 tunables. Likely in the ADT (`tunables` properties) **(guess)**; otherwise from a hypervisor trace of macOS. |
| Registers | M1 task manager at engine `+0x24000`, task queues at `+0x25000`, queue stride `0x148`, `VERS` at `+0x1840000`. | Whether H14 keeps the layout. Read `VERS` first. |

## 3. Software stack

**Kernel driver: `drivers/accel/`.** The ANE is a job-submission accelerator with no display
and no graphics API, which is what the accel subsystem is for; eiln's driver is already shaped
that way, and `rocket` (Rockchip NPU) and `ethosu` in our tree are the closest models: power,
buffer map, submit, everything else in userspace. A misc-device or UIO driver would avoid DRM
rules but loses GEM, dma-buf and the scheduler, and could never go upstream. Upstreaming is
blocked by the DRM rule that new uAPI needs a real open-source userspace
(`Documentation/gpu/drm-uapi.rst`, "Open-Source Userspace Requirements"). A userspace that only
replays Apple-compiled `.hwx` is unlikely to pass. Plan: a held patch in the kernel repo, not upstream, until an
open compiler exists.

Work beyond eiln's module: t8112 match data, t8110 DART handling, DT binding and nodes for
`t8112.dtsi`, `void` remove, a DRM GPU scheduler for multiple queues, per-file IOMMU address
spaces instead of one shared `drm_mm` **(the current shared space lets every client see every
buffer)**.

**Userspace runtime.** Start from `libane`: load a model container, allocate BOs for the BAR
layout, fill inputs, submit, wait. Replace the `.anec` format with something documented by us.

**Compiler (the hard part).** Two tracks:

1. Apple-compiled. Compile on macOS with `ANECCompileOffline` for the `h14*` target, convert the
   `.hwx` on Linux. Works soon, needs a Mac for every new model or shape, and redistributing
   Apple-compiled artifacts is a legal question for the user, not settled here.
2. Open. Emit task descriptors ourselves. Per eiln, a TD is a register file written by a
   control DMA, with fixed-function stages (convolution engine, planar engine, activation LUT,
   DMA descriptors), so the compiler is a tiler and register allocator over a few fixed op
   templates, not an ISA backend. The hard parts are tiling into 64 KiB kernel memory and 2 MiB
   tile memory, and the many undocumented fields. Reachable for conv, matmul and elementwise;
   a full CoreML op set is not realistic.

**Integration targets**, in order of realism:

1. `libane` + Python, standalone. Validation only.
2. whisper.cpp encoder. whisper.cpp already runs the encoder on the ANE through CoreML on
   macOS, so the model split, fixed shapes and fp16 tolerances are proven. Best first real workload.
3. ONNX Runtime execution provider for static-shape vision and embedding models, with
   ahead-of-time compiled subgraphs.
4. Mesa Teflon (TFLite delegate), the route `rocket` and `ethosu` take upstream; only with the
   open compiler.
5. IREE / MLIR: a HAL driver plus codegen. The right home for an open compiler long term, the
   largest effort.
6. llama.cpp: poor fit. Decode is memory-bandwidth-bound, the ANE shares the M2's LPDDR5 with the
   GPU, and ggml's dynamic shapes clash with ahead-of-time compiled graphs. At most prefill
   matmuls, for power rather than speed. Not a first target, even though it is what "local AI"
   usually means.

Expectation to set: on M2 the ANE wins on power, not throughput, against the GPU
(maderix reports the same on M4).

## 4. Reverse engineering with our tools

- **Hypervisor trace of macOS.** unboot's hypervisor runs macOS with `hv/trace_*.py` tracers.
  There is no `trace_ane.py`; build one from `trace_isp.py` (same shape: ASC, DART, MMIO) and
  `unboot/trace/asc.py` and `dart.py`. Record while a CoreML model of known weights runs:
  ANE and PMGR MMIO writes (tunables, power sequence), RTKit endpoints and messages, DART page
  tables (which BAR holds what), task-queue pushes and the TD bytes they point at. Needs macOS
  installed on the mini and hypervisor runs, both owned by the hardware agent.
- **Diffing compiled models.** On the M4 Pro host, compile controlled variants for the H14 target
  (one op, one changed parameter: kernel size, stride, channel count, activation, a single
  weight) and diff the `.hwx`. Each field that moves with exactly one input is identified.
  Fully automatable on the host, no device needed, and the bulk of compiler RE.
- **Ground truth.** Run the same model through CoreML on macOS and through our stack on Linux,
  compare outputs within fp16 tolerance. Outputs from CoreML are the spec, never our code.
- **HIL and agents.** The HIL relay refuses power-management proxy calls and calls that run code
  on the device, so ANE bring-up (power states) and hypervisor tracing cannot go through it
  under the current policy. Agents can still: run the compile-and-diff loop unattended, maintain
  a field database, generate TDs and check them against Apple's for the same input, and, once
  a policy allows ANE power-up, run proxyclient regression on each change.

## 5. Phased plan

| Phase | Goal | Done when | Needs | Effort (guess) |
|---|---|---|---|---|
| A. Desk prep | t8112 ADT nodes, power states, tunables, DART type, firmware name; fix the proxyclient ANE import; make `fw/ane.py` read power states and DART type from the ADT instead of t8103 constants; build a tool that compiles a CoreML model for `h14*` on the host | proxyclient ANE code loads on a t8112 ADT offline; an H14 `add.hwx` exists | IPSW or ADT dump; host Mac | days |
| B. Power and first job | `experiments/ane.py` on the mini: power up, read `VERS`, run fp16 add | Output is 3.0; repeated 100 times without a hang or DART fault | Device time; HIL policy or hardware-agent lease allowing ANE power states | 1-3 weeks; risk: missing tunables, which then need phase C first |
| C. macOS trace (only if B stalls) | `hv/trace_ane.py`; record macOS bring-up and one inference | Replaying the recorded writes from proxyclient makes B pass | macOS on the mini; hypervisor runs | 2-4 weeks |
| D. Kernel driver | eiln's driver ported to v7.3: t8112 match, t8110 DART, DT nodes and binding, runtime PM | Matmul test from `eiln/ane` passes on t8112; module unloads and reloads cleanly; idle ANE is powered down | Device time | 2-4 weeks |
| E. Known model matches CoreML | A small CNN compiled on macOS for H14, run on Linux | Every output within fp16 tolerance of CoreML on macOS for a fixed input set | Host Mac | 2-4 weeks |
| F. Real workload | whisper.cpp encoder on the ANE | Transcripts identical to the CPU path on a test set; encoder latency and power measured against the GPU | | 1-2 months |
| G. Open compiler (research) | Emit H14 TDs for conv, matmul, elementwise without Apple's compiler | Generated TDs produce CoreML-matching output for the phase-E model | Phase-A diff tooling | many months; may not finish |

Upstream submission is not a phase: it depends on G.

## Risks

- H14 may differ from H13 more than the shared `ane,t8020` kext suggests: register layout, TD
  format, or a firmware-only path. Phase B answers this cheaply.
- Without an open compiler the stack depends on macOS for every model and cannot go upstream.
- The community is small: eiln stopped, and from M5 on Apple moves neural acceleration into the
  GPU, so few people will work on H14 alongside us.
- Payoff is power efficiency on fixed-shape models, not faster LLMs.
