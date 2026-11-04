# TCPU-16 testbench

The Cocotb testbench drives the TCPU-16 Tiny Tapeout wrapper for RTL and
gate-level simulation. For general Cocotb testing guidance, see the
[Tiny Tapeout testing guide](https://tinytapeout.com/hdl/testing/).

For test coverage, CI workflows, and hardening evidence, see the
[project verification notes](../docs/verification.md).

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

The Makefile selects `F01_rtl`–`F04_rtl` and `test_prog_loader` for RTL
simulation.

## Gate-level simulation

First harden the design. The Tiny Tapeout flow writes the powered GF180
netlist to `runs/wokwi/final/pnl/{top_module}.pnl.v`. From this directory,
copy the TCPU-16 netlist and run the test:

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

Gate-level netlists do not guarantee that RTL-internal hierarchy is available.
Tests should check top-level pins and allow standard-cell delays to settle
before sampling outputs.

## View the waveform

The simulator writes `tb.fst` by default. Open it with GTKWave:

```sh
gtkwave tb.fst tb.gtkw
```

Or use Surfer:

```sh
surfer tb.fst
```
