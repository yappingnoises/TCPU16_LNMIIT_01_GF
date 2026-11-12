# TCPU-16 testbench

The Cocotb testbench drives the TCPU-16 Tiny Tapeout wrapper for RTL and
gate-level simulation. For general Cocotb testing guidance, see the
[Tiny Tapeout testing guide](https://tinytapeout.com/hdl/testing/).

The verification-plan tests are split by behavior into separate modules and
share setup and driver coroutines from `testbenches/coros/`. The same tests run
against RTL and gate-level simulations. For the coverage summary, CI
workflows, and hardening evidence, see the
[project verification notes](../docs/verification.md) and
[design documentation](../docs/design.md).

## Prerequisites

Install Icarus Verilog and the Python packages listed in
[`requirements.txt`](requirements.txt).

## RTL simulation

Run from this directory:

```sh
make clean
make
python -m cocotb_tools.check_results results.xml
```

The Makefile selects the test modules in `testbenches/` for RTL simulation.
The 44 Cocotb tests cover F01–F43, the Mode O synchronizer-latency checks, and
a deterministic reference-model test over 1,000 fully initialized programs
with 64 randomized run-control edges each. RTL runs also compare the
architectural registers to the reference model when those internal signals are
available. Each verification case is reported independently.

## Gate-level simulation

First harden the current RTL. The Tiny Tapeout flow writes the powered GF180
netlist to `runs/wokwi/final/pnl/{top_module}.pnl.v`. Do not reuse a netlist
from an older RTL revision. From this directory, copy the newly generated
TCPU-16 netlist and run the test:

```sh
cp ../runs/wokwi/final/pnl/tt_um_yappingnoises_TCPU16.pnl.v gate_level_netlist.v
make clean
make GATES=yes
python -m cocotb_tools.check_results results.xml
```

The Makefile defaults `PDK_ROOT` to `~/ttsetup/pdk`. Override it if the PDK
is installed elsewhere:

```sh
make GATES=yes PDK_ROOT=/path/to/pdk
```

Gate-level simulations use the same test module. Functional checks use the
Tiny Tapeout pins and allow standard-cell delays to settle before sampling
outputs; internal-register checks are performed only when RTL hierarchy is
available.

In this workspace, `gate_level_netlist.v` was regenerated from the current
checkout (`a47cac1`) and all 44 tests pass in gate-level simulation.
The older hardening snapshot under `runs/wokwi/` is intentionally preserved;
do not copy its netlist over the current test netlist.

## View the waveform

The simulator writes `tb.fst` by default. Open it with GTKWave:

```sh
gtkwave tb.fst tb.gtkw
```

Or use Surfer:

```sh
surfer tb.fst
```

## Per-test waveforms

Generate a matching FST waveform and GTKWave save file for every Cocotb test,
with each test run in its own simulation. The save file opens the signals
relevant to that test:

```sh
python generate_waveforms.py
```

RTL waveform and GTKWave pairs are written to `waveforms/rtl/` and are checked
in with the project. Open a pair from that directory:

```sh
cd ../waveforms/rtl
gtkwave F09.fst F09.gtkw
```

To capture the same per-test traces from the gate-level netlist:

```sh
python generate_waveforms.py --gates
```

The gate-level option requires the current `gate_level_netlist.v` and GF180
PDK setup described above. Gate-level FSTs use public pin signals; RTL FSTs
also show internal CPU state.
