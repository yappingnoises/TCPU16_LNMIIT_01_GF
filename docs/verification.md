# Verification and implementation status

This page records how to run the project tests, what they currently verify,
and what can be concluded from the local hardening run. It is separate
from [`info.md`](info.md), which supplies the Tiny Tapeout project datasheet.

## RTL simulation

The RTL test configuration is in [`test/Makefile`](../test/Makefile). It runs
`F01`–`F04` from `rtl_tb/` and `F05`–`F08` from `test_prog_loader.py`.

From the repository root:

```sh
cd test
make clean
make
python -m cocotb_tools.check_results results.xml
```

The test dependencies are listed in [`test/requirements.txt`](../test/requirements.txt).
The test CI workflow installs Icarus Verilog and those Python packages, runs
the same RTL suite, and checks `results.xml` so failed Cocotb tests fail CI.

### What the current tests check

| Test(s) | Current check |
|---------|---------------|
| `F01` | Asserts that reset clears the program counter, accumulator, instruction register, and halted flag. |
| `F02` | Asserts that eight sequential program loads write the expected words to program memory. |
| `F03` | Checks the first four loaded words, then exercises reset and additional loads; the later memory observations are logged but not asserted. |
| `F04` | Loads a program containing `HALT` and runs it, but its halt and program-counter assertions are commented out. |
| `F05` | Holds `prog_load` high across multiple edges and logs memory; it currently has no assertions. |
| `F06` | Asserts that all eight loaded words are stored at the expected addresses. |
| `F07` | Asserts that the ninth load wraps around and overwrites address zero. |
| `F08` | Attempts program loading while `run` is asserted, but currently has no assertions. |

[`rtl_tb/test_alu.py`](../test/rtl_tb/test_alu.py) contains a separate `F09`
diagnostic test. It is not in the Makefile's `COCOTB_TEST_MODULES` list and
logs internal accumulator values without asserting expected results. Thus,
the configured RTL suite does not yet provide assertion-based coverage for
each ALU operation or branch behavior.

## Gate-level simulation

After hardening, the local gate-level test uses the powered netlist and GF180
standard-cell models:

```sh
cd test
cp ../runs/wokwi/final/pnl/tt_um_yappingnoises_TCPU16.pnl.v gate_level_netlist.v
make clean
make GATES=yes
python -m cocotb_tools.check_results results.xml
```

`PDK_ROOT` defaults to `~/ttsetup/pdk`; set `PDK_ROOT=/path/to/pdk` if your
installation is elsewhere. The gate-level test in `gl_tb/F01.py` currently
drives reset, loading, and execution, but its value-checking assertions are
commented out. Treat it as a simulation/build smoke test, not yet as an
assertion-based functional gate-level test.

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

The local outputs in `runs/wokwi/` record source commit `34ee4c8` (as noted in
`runs/wokwi/final/commit_id.json`), not the current checkout. These generated
outputs are not tracked by Git and may not be present on another clone. The
flow log ends with `Flow complete`, and generated GDS and powered-netlist
artifacts are present in this workspace. For this snapshot:

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
