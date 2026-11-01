# bande-linux bootloader

the source of truth; keep it current. Open work goes to [NOTES/backlog.md](NOTES/backlog.md).

The rules below override your defaults. Follow them unless I say otherwise in the session.

## 0. Proper implementations only

No shortcuts and no band-aids. Every change is the long-term implementation:

- Fix the cause, not the symptom. Never widen a check, raise a limit, skip a step or special-case
  a value to make something work without knowing why that is correct.
- Support a new firmware, iBoot or hardware version by understanding it: get its real layout and
  behaviour (a trace, the ADT, the macOS driver), implement it explicitly, and keep refusing
  versions that are not understood.
- Write it so it could go upstream as it is.

When the proper implementation is not possible yet, say so and leave the gap visible (a refused
version, a missing feature, a backlog item) instead of covering it up.

## 1. No comments

Write none, in C, Rust, Python, Makefiles or shell. The only exception is a fact this repository
cannot tell the reader:

- behaviour of hardware or firmware we do not own (Apple SoC blocks, iBoot, ADT quirks, RTKit
  coprocessors), with how it was established: a trace, the ADT, a macOS driver
- a magic value copied from outside, with its source

One line. Never write what the next line does, a note to the reviewer ("now", "replaces",
"fixed"), a defence of a design, a banner, or a doc comment that restates a name or signature.
Doc comments are comments.

Existing comments stay as they are. Removing them is its own commit, never part of a change.

## 2. No explanatory text on the console

Everything the bootloader prints on the framebuffer or serial, and everything a proxyclient tool
prints, is read. Output carries data, state and errors, nothing that explains them:

- a state or a problem in one short sentence ("No payload found.")
- keep a warning only for hardware risk or data loss
- no progress chatter beyond what a person or an agent needs to tell a hang from work

## 3. No tests without a motivation

Do not add a test because you changed code. A new test needs one of these motivations, stated in
its name or first line:

- it reproduces a bug that actually happened and would come back unseen
- it pins behaviour of hardware or firmware we do not own; the expected value comes from a
  hardware trace, the ADT or macOS, never from reading our code
- it guards a safety property: a blocked MMIO range stays blocked, a malformed payload is
  refused, the version handoff to the kernel stays intact

Even then, propose it in one line and wait for a yes. Prefer a test through proxyclient against
the device, or through a built binary, over a unit test of a helper.

Never write tests of constants, getters or formatting, a return value restated, mocks asserting
they were called, one test per branch, or edge-case sweeps.

When your change breaks an existing test: fix it if it guards one of the motivations above;
delete it if it only restated the old code, and list every deletion in your reply.

## 4. Before you finish

Re-read your diff. Delete every comment that fails §1, every string that fails §2 and every test
you added that fails §3. Expect that to be most of them.

## 5. Scope and consent

- Do what I asked, then stop. Name adjacent problems in one line at the end of your reply; don't
  fix them.
- No unrequested docs, renames or formatting passes. No CI or packaging work unless asked.
- Reuse before you add: search proxyclient's `hw/`, `fw/` and `trace/` modules and `src/` first.
  Duplicate logic is a bug; factor it out the second time, inside your scope. No speculative
  optimisation.
- Ask first, in two or three sentences with the trade-off, before you:
  - touch more than a handful of files
  - move, rename or split a file, the proxyclient package or a build output
  - change an interface another repo depends on: `/chosen` device-tree properties, the version
    marker and variable block the installer reads, payload formats, USB descriptors host tools
    match on
  - add a dependency (Rust crate, Python package, toolchain)
  - write to power management, PMU, SMC, voltage, fan or thermal registers, NVRAM or boot
    policy, from code or from the proxy shell
  - act on the real Mac: install a stage 1, boot a payload, run a proxyclient tool against it,
    a DFU restore
- Commit in small commits of one intent on a branch and push it. A branch reaches main once it is
  built and verified on the mini, never by a force-push. CI runs only on `v*` tags.

## 6. Architecture

- One binary runs on bare metal before any OS: as stage 1, installed by the installer as the
  custom boot object with its variables appended, and as stage 2 from the EFI system partition.
- Without a payload it waits in proxy mode on USB, driven from the host by `proxyclient/`. The
  proxy and the hypervisor (`run_guest.py`) are the hardware-in-the-loop interface: every
  hardware experiment goes through them, scripted and logged, never by hand.
- It builds the kernel's device tree from Apple's ADT. Properties it sets under `/chosen` are an
  interface with the kernel and userspace.
- Hardware knowledge learned from a trace goes into proxyclient's `hw/`, `fw/` or `trace/`
  modules, with its source, so the next experiment starts from it.
