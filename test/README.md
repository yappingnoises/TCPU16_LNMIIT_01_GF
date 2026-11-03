# Sample testbench for a Tiny Tapeout project

This is a sample testbench for a Tiny Tapeout project. It uses [cocotb](https://docs.cocotb.org/en/stable/) to drive the DUT and check the outputs.
See below to get started or for more information, check the [website](https://tinytapeout.com/hdl/testing/).

## Setting up

1. Edit [Makefile](Makefile) and modify `PROJECT_SOURCES` to point to your Verilog files.
2. Edit [tb.v](tb.v) and replace `tt_um_example` with your module name.

## How to run

The Cocotb test modules are organized by simulation type: `rtl_tb/test.py` is
selected for RTL, and `gl_tb/test2.py` is selected for gate-level simulation.
The Makefile adds the corresponding folder to Python's module search path.

To run the RTL simulation:

```sh
make -B
```

To run gate-level simulation, first harden your project.

The current Tiny Tapeout hardening flow writes the powered GF180 netlist to
`runs/wokwi/final/pnl/{top_module}.pnl.v`. From this `test` directory, copy it
with:

```sh
cp ../runs/wokwi/final/pnl/tt_um_yappingnoises_TCPU16.pnl.v gate_level_netlist.v
```

The Makefile defaults `PDK_ROOT` to `~/ttsetup/pdk`, matching the local
hardening guide setup. Run the gate-level simulation with:

```sh
make -B GATES=yes
```

If your PDK is installed elsewhere, override the default:

```sh
make -B GATES=yes PDK_ROOT=/path/to/pdk
```

Gate-level netlists do not guarantee that RTL-internal hierarchy is available.
Tests used for gate-level simulation should check the top-level pins, and allow
time for the standard-cell delays to settle before sampling outputs.

If you wish to save the waveform in VCD format instead of FST format, edit tb.v to use `$dumpfile("tb.vcd");` and then run:

```sh
make -B FST=
```

This will generate `tb.vcd` instead of `tb.fst`.

## How to view the waveform file

Using GTKWave

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer

```sh
surfer tb.fst
```
