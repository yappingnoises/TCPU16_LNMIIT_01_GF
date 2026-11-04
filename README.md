# TCPU-16

TCPU-16 is a small, single-cycle 16-bit accumulator CPU designed for a 1x1
Tiny Tapeout tile using the GF180MCU process. It has an 8-bit instruction
format, an 8-word program memory, and a serial program-loading interface.

The CPU implements `LOAD`, `ADD`, `SUB`, `SHL`, `XOR`, `JMP`, `JZ`, and
`HALT`. Its 16-bit accumulator is read one byte at a time through the output
pins. See the [Tiny Tapeout project datasheet](docs/info.md) for the full
architecture, instruction set, pin mapping, and programming example.

## Project status

The repository includes RTL and Cocotb testbenches for RTL and gate-level
simulation, along with Tiny Tapeout workflows for testing, GF180 hardening,
precheck, gate-level testing, and the results viewer. Locally generated
hardening artifacts are from an earlier source commit; see
[verification and implementation status](docs/verification.md) before relying
on their results.

## Run RTL tests

Install Icarus Verilog and the Python packages in
[`test/requirements.txt`](test/requirements.txt), then run:

```sh
cd test
make clean
make
python -m cocotb_tools.check_results results.xml
```

For local GF180 gate-level simulation, first follow the
[Tiny Tapeout local hardening guide](https://www.tinytapeout.com/guides/local-hardening/)
and install the PDK. Then run from `test/`:

```sh
make clean
make GATES=yes
python -m cocotb_tools.check_results results.xml
```

The gate-level flow uses `~/ttsetup/pdk` by default. Override it with
`PDK_ROOT=/path/to/pdk` if needed. See the [test instructions](test/README.md)
and [verification notes](docs/verification.md) for details and coverage
limitations.

## Repository map

- [`src/`](src/) — CPU RTL and Tiny Tapeout wrapper.
- [`test/`](test/) — Cocotb testbenches and simulation setup.
- [`docs/info.md`](docs/info.md) — datasheet content consumed by Tiny Tapeout.
- [`docs/verification.md`](docs/verification.md) — how to run tests, what they
  currently check, CI workflows, and hardening evidence.
- `runs/wokwi/` — local hardening logs and generated artifacts when a flow has
  been run; these outputs are not tracked in the repository.

## Tiny Tapeout resources

- [Tiny Tapeout](https://tinytapeout.com/)
- [Local hardening guide](https://www.tinytapeout.com/guides/local-hardening/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
