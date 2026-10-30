<!--

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

TCPU-16 is a single-cycle accumulator CPU with a 16-bit accumulator, 8-bit instructions, and an 8-word program memory. One instruction is fetched, decoded, executed, and committed at each rising clock edge. The program is loaded through input ports before execution begins.

### Architecture

The design is built from the following blocks:

- **Program memory** — 8 × 8-bit flip-flop array (no reset). Loaded word-by-word before execution via `prog_data` and `prog_load`. Read combinationally: `instr = mem[pc]`.
- **Program loader** — Detects a rising edge on `prog_load` (while `run = 0`) using a one-flop edge detector (`pl_q`). Each detected edge writes `prog_data` to `mem[load_addr]` and increments `load_addr`. `load_addr` resets to 0 on `rst_n`.
- **ALU** — Pure combinational 16-bit unit. Decodes `instr[7:5]` as the opcode and `instr[4:0]` as the operand. Performs: LOAD (zero-extend immediate), ADD, SUB (both modulo 65536), SHL (logical left shift by `instr[2:0]`), XOR, and computes jump enable/address for JMP/JZ. Asserts `halted` for HALT.
- **PC** — 3-bit program counter. Increments by 1 each executing edge, or jumps to the ALU-supplied target for JMP/unconditional JZ. Holds on HALT.
- **IR** — 8-bit instruction register. Latches `instr` at every executing edge. Exists for RTL simulation visibility only; synthesis removes it as it has no fanout.
- **Execute enable** — `execute = run_sync & ~halted`. When `execute = 0`, PC, ACC, IR and `halted` hold their values.
- **Byte-select mux** — `acc_out = byte_sel ? acc[15:8] : acc[7:0]`. Purely combinational; no register between ACC and `acc_out`.
- **Input synchronizers (Mode O, SYNC_STAGES = 2)** — Two-flop synchronizers on `run`, `prog_load`, and `rst_n` (no reset, no logic between stages). Required because the Tiny Tapeout harness clock is independent of the host driving the input signals. `prog_data` and `byte_sel` are not synchronized: `prog_data` is held stable by the load protocol; `byte_sel` drives only the combinational output mux.

### Instruction Set

| Opcode | Mnemonic  | Operation                                   | PC after       |
|--------|-----------|---------------------------------------------|----------------|
| `000`  | LOAD imm  | `ACC ← {11'b0, imm}`                        | PC + 1         |
| `001`  | ADD imm   | `ACC ← (ACC + imm) mod 65536`               | PC + 1         |
| `010`  | SUB imm   | `ACC ← (ACC − imm) mod 65536`               | PC + 1         |
| `011`  | SHL sh    | `ACC ← (ACC << sh) mod 65536`, sh = imm[2:0]| PC + 1         |
| `100`  | XOR imm   | `ACC ← ACC ^ {11'b0, imm}`                  | PC + 1         |
| `101`  | JMP addr  | no ACC change                               | addr = imm[2:0]|
| `110`  | JZ  addr  | no ACC change                               | addr if ACC==0, else PC+1 |
| `111`  | HALT      | `halted ← 1`                                | PC (held)      |

The immediate `imm` is always unsigned and zero-extended to 16 bits. There are no flags.

### Clocking Mode

**Mode O (SYNC_STAGES = 2).** The Tiny Tapeout harness provides a free-running clock independent of the host MCU. All control inputs (`run`, `prog_load`, `rst_n`) are asynchronous and pass through two-flop synchronizers before use. `rst_n` must be held low for at least 3 edges on reset. All edge counts in the specification refer to the synchronized signal outputs, which lag the pins by 2 edges.

---

## How to test

### Pin mapping

| Harness pin | Signal       | Direction |
|-------------|--------------|-----------|
| `ui_in[7:0]`  | `prog_data[7:0]` | Input  |
| `uio_in[0]`   | `prog_load`      | Input  |
| `uio_in[1]`   | `run`            | Input  |
| `uio_in[2]`   | `byte_sel`       | Input  |
| `uo_out[7:0]` | `acc_out[7:0]`   | Output |
| `clk`         | clock            | Input  |
| `rst_n`       | active-low reset | Input  |

`uio_oe` is tied to `0x00` (all bidirectional pins used as inputs).

### Loading a program

1. Hold `rst_n = 0` for at least 3 clock edges with `run = 0`, then release (`rst_n = 1`). Keep `run = 0`.
2. Place the first instruction byte on `ui_in[7:0]` (`prog_data`).
3. Raise `uio_in[0]` (`prog_load`) — hold high for at least 2 edges so the synchronizer and edge detector capture the rising edge. Then lower it.
4. Repeat steps 2–3 for all 8 instruction words in order (address 0 to 7). All 8 words must be written before `run` is asserted; unwritten words have undefined content.
5. Raise `uio_in[1]` (`run = 1`). The CPU begins executing from `mem[0]` on the next rising clock edge.

### Reading the result

`acc_out` always reflects one byte of the accumulator, selected by `byte_sel`:

- Set `uio_in[2] = 0` → `uo_out` = `ACC[7:0]`  (low byte)
- Set `uio_in[2] = 1` → `uo_out` = `ACC[15:8]` (high byte)

For a coherent 16-bit read, sample both bytes while `run = 0` (after HALT), between host-generated clock pulses, or after the known number of execution edges has elapsed.

### Example program — compute 5 + 3

Assemble and load the following words in order (addresses 0–7):

| Addr | Instruction | Encoding | Notes              |
|------|-------------|----------|--------------------|
| 0    | LOAD 5      | `0x05`   | ACC ← 5            |
| 1    | ADD  3      | `0x23`   | ACC ← 8            |
| 2    | HALT        | `0xE0`   | stop               |
| 3–7  | HALT        | `0xE0`   | fill unused words  |

After 2 executing edges (`run = 1`), the CPU halts. Read `acc_out` with `byte_sel = 0` → `0x08`; with `byte_sel = 1` → `0x00`. Combined: `ACC = 0x0008`.

### Building a 16-bit constant

A single instruction can only load a 5-bit immediate (0–31). Use LOAD + SHL + ADD to build wider values:

```
LOAD a    ; ACC = a            (0 ≤ a ≤ 31)
SHL  s    ; ACC = a << s       (0 ≤ s ≤ 7)
ADD  b    ; ACC = (a << s) + b (0 ≤ b ≤ 31)
```

Example — load `0x0123` (291 = (18 << 4) + 3):
```
LOAD 18  ; 0x12
SHL  4   ; 0x64
ADD  3   ; 0x23
HALT     ; 0xE0
```

Every constant from 0 to 65535 is reachable in at most 5 instructions.

---

## External hardware

No external hardware is required. The CPU is driven entirely through the Tiny Tapeout harness input pins by a host microcontroller or testbench. No PMOD or additional peripherals are needed.
