#!/usr/bin/env python3
"""Run every Cocotb test separately and save one FST waveform per test."""

import argparse
import ast
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "test"
BENCH_DIR = TEST_DIR / "testbenches"
WAVEFORM_DIR = ROOT / "waveforms"


def gtk_signals(module, gates):
    scalars = ["tb.clk", "tb.rst_n"]
    vectors = [
        "tb.ui_in[7:0]",
        "tb.uio_in[7:0]",
        "tb.uo_out[7:0]",
    ]

    if gates:
        return scalars, vectors

    cpu = "tb.tcpu.cpu."
    if module == "test_alu":
        scalars.extend(
            [
                f"{cpu}execute",
                f"{cpu}alu_acc_wr",
                f"{cpu}jump_en",
                f"{cpu}halted",
            ]
        )
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}ir[7:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}instr[7:0]",
                f"{cpu}u_ALU.opcode[2:0]",
                f"{cpu}u_ALU.imm[4:0]",
                f"{cpu}alu_acc_out[15:0]",
                f"{cpu}jump_addr[2:0]",
            ]
        )
    elif module in ("test_reset_loading", "test_execution"):
        scalars.extend(
            [
                f"{cpu}execute",
                f"{cpu}run_sync",
                f"{cpu}pl_sync",
                f"{cpu}rst_sync",
                f"{cpu}halted",
                f"{cpu}u_prog_loader.load_pulse",
                f"{cpu}u_prog_loader.pl_q",
            ]
        )
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}ir[7:0]",
                f"{cpu}instr[7:0]",
                f"{cpu}u_prog_loader.load_addr[2:0]",
            ]
        )
    elif module == "test_control_flow":
        scalars.extend(
            [
                f"{cpu}execute",
                f"{cpu}jump_en",
                f"{cpu}halted",
            ]
        )
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}ir[7:0]",
                f"{cpu}instr[7:0]",
                f"{cpu}jump_addr[2:0]",
                f"{cpu}u_ALU.opcode[2:0]",
                f"{cpu}u_ALU.imm[4:0]",
            ]
        )
    elif module == "test_interface":
        scalars.extend([f"{cpu}byte_sel", f"{cpu}halted"])
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}ir[7:0]",
            ]
        )
    elif module == "test_reference_model":
        scalars.extend(
            [
                f"{cpu}run_sync",
                f"{cpu}execute",
                f"{cpu}halted",
            ]
        )
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}ir[7:0]",
                f"{cpu}instr[7:0]",
            ]
        )
    elif module == "test_synchronizer":
        scalars.extend(
            [
                f"{cpu}run_s1",
                f"{cpu}run_sync",
                f"{cpu}pl_s1",
                f"{cpu}pl_sync",
                f"{cpu}rst_s1",
                f"{cpu}rst_sync",
                f"{cpu}u_prog_loader.load_pulse",
            ]
        )
        vectors.extend(
            [
                f"{cpu}pc[2:0]",
                f"{cpu}acc[15:0]",
                f"{cpu}u_prog_loader.load_addr[2:0]",
            ]
        )

    return scalars, vectors


def write_gtkw(path, fst_path, module, gates):
    scalars, vectors = gtk_signals(module, gates)
    signals = "\n".join(
        ["@28", *scalars, "@22", *vectors]
    )
    path.write_text(
        "\n".join(
            [
                "[*]",
                "[*] GTKWave Analyzer",
                f'[dumpfile] "{fst_path.name}"',
                f'[savefile] "{path.name}"',
                "[timestart] 0",
                "[treeopen] tb.",
                "[treeopen] tb.tcpu.",
                "[treeopen] tb.tcpu.cpu.",
                "[signals_width] 220",
                "[sst_expanded] 1",
                signals,
                "",
            ]
        ),
        encoding="utf-8",
    )


def cocotb_test_names():
    for path in sorted(BENCH_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "cocotb"
                    and decorator.func.attr == "test"
                ):
                    test_name = node.name
                    for keyword in decorator.keywords:
                        if keyword.arg == "name":
                            test_name = ast.literal_eval(keyword.value)
                            break
                    yield path.stem, test_name
                    break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gates",
        action="store_true",
        help="run gate-level tests (requires gate_level_netlist.v and the PDK)",
    )
    args = parser.parse_args()

    mode = "gates" if args.gates else "rtl"
    output_dir = WAVEFORM_DIR / mode
    output_dir.mkdir(parents=True, exist_ok=True)

    tests = list(cocotb_test_names())
    if not tests:
        parser.error(f"no Cocotb tests found under {BENCH_DIR}")

    for module, test_name in tests:
        output_path = output_dir / f"{test_name}.fst"
        command = [
            "make",
            "-C",
            str(TEST_DIR),
            f"COCOTB_TEST_FILTER={test_name}$",
            f"COCOTB_PLUSARGS=+WAVEFORM={output_path}",
        ]
        if args.gates:
            command.append("GATES=yes")
        print(f"Generating {output_path.relative_to(ROOT)}", flush=True)
        subprocess.run(command, check=True)
        write_gtkw(
            output_path.with_suffix(".gtkw"),
            output_path,
            module,
            args.gates,
        )

    print(
        f"Generated {len(tests)} {mode} FST/GTKWave pairs in {output_dir}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
