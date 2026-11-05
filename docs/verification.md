# Verification and implementation status

This page records how to run the project tests, what they currently verify,
and what can be concluded from the local hardening run. It is separate
from [`info.md`](info.md), which supplies the Tiny Tapeout project datasheet.

## RTL and gate-level simulation

The assertion-based test modules are split by behavior under
[`test/testbenches/`](../test/testbenches/), with shared drivers in
[`test/testbenches/coros/`](../test/testbenches/coros/). The modules are selected
for both RTL and gate-level runs by [`test/Makefile`](../test/Makefile). They
cover the vplan's F01–F43 functional features and F44 synchronizer timing.
RTL simulation additionally checks PC, ACC, IR, halted, and loader internals
when available; gate-level checks use the public Tiny Tapeout pins so the suite
does not depend on preserved internal hierarchy.

The RTL F35 reference-model test runs 1,000 deterministic, fully loaded
programs for 64 edges each with randomized `run` control. At each edge it
checks both output bytes; RTL also compares the architectural registers
against the model. Both RTL and gate-level runs pass all eight grouped
tests against the current source.

Install Icarus Verilog and the Python packages listed in
[`test/requirements.txt`](../test/requirements.txt). From the repository root:

```sh
cd test
make clean
make
python -m cocotb_tools.check_results results.xml
```

For gate-level simulation, first harden the current RTL. The Tiny Tapeout flow
writes the powered GF180 netlist to
`runs/wokwi/final/pnl/{top_module}.pnl.v`. Copy the netlist generated from the
current source and run:

```sh
cd test
cp ../runs/wokwi/final/pnl/tt_um_yappingnoises_TCPU16.pnl.v gate_level_netlist.v
make clean
make GATES=yes
python -m cocotb_tools.check_results results.xml
```

`PDK_ROOT` defaults to `~/ttsetup/pdk`; set `PDK_ROOT=/path/to/pdk` if the
PDK is installed elsewhere. Gate-level functional checks use top-level pins
and allow standard-cell delays to settle before sampling outputs. F44's
pin-visible run/reset latency is checked in both modes; its load-address
latency assertion is made when RTL hierarchy is available.

In this workspace, `test/gate_level_netlist.v` was regenerated from checkout
`a47cac1` using an isolated LibreLane run at
`src/runs/current-source-cpu-tests/`. All eight grouped RTL tests and all
eight grouped gate-level tests pass. The older hardening snapshot under
`runs/wokwi/` is preserved and records source commit `34ee4c8`; its netlist
predates the current PC/IR ownership change and must not be copied over the
current test netlist.

## CI workflows

- [`test.yaml`](../.github/workflows/test.yaml) runs the RTL test suite on
  pushes and manual dispatch, validates the Cocotb result XML, and uploads
  test results and a waveform.
- [`gds.yaml`](../.github/workflows/gds.yaml) runs the Tiny Tapeout GF180 GDS
  flow, precheck, gate-level test, and viewer workflow on pushes and manual
  dispatch.
- [`docs.yaml`](../.github/workflows/docs.yaml) builds the Tiny Tapeout
  documentation.

The local test commands above are useful for iteration; CI and the latest
workflow artifacts should be consulted for the status of a particular commit.

## Local hardening snapshot

The older local outputs in `runs/wokwi/` record source commit `34ee4c8` (as
noted in `runs/wokwi/final/commit_id.json`), not the current checkout. A
separate current-source run was generated under
`src/runs/current-source-cpu-tests/` and used for the passing gate-level
tests. These generated outputs are not tracked by Git and may not be present
on another clone. For the preserved `runs/wokwi/` snapshot:

- The flow reports no lint errors or timing-construct errors; it reports two
  lint warnings.
- Magic DRC and LVS checks are reported clear; the KLayout DRC step was
  skipped by the flow configuration.
- Hold checks report no violations. The post-P&R summary reports setup
  violations in slow-corner timing scenarios (worst overall setup slack
  `-7.4392` in the report's time units).
- The flow log mentions a generic fallback SDC because project-specific
  `PNR_SDC_FILE` and `SIGNOFF_SDC_FILE` were not defined. Treat the timing
  numbers as evidence from that run's constraints, not as a current timing
  sign-off.

Before using physical-design metrics as current project results, rerun the
hardening flow for the current source and review its timing constraints,
reports, and workflow status.
