import random

from coros.bench import (
    PROGRAM_WORDS,
    drive,
    load_program,
    read_resolvable,
    reset,
    rtl_cpu,
    settle_time,
    start,
    tick,
)

import cocotb
from cocotb.triggers import Timer

from coros.reference_model import advance, new_state

@cocotb.test()
async def test_vplan_random_reference_model(dut):
    await start(dut)
    rng = random.Random(0x16C0C07)
    cpu = rtl_cpu(dut)

    # F35: 1000 complete programs, 64 edges per program, randomized run input.
    # The reference model includes the two-stage run synchronizer.
    for program_index in range(1000):
        await reset(dut)
        program = [rng.randrange(256) for _ in range(PROGRAM_WORDS)]
        await load_program(dut, program)
        model = new_state()

        for edge_index in range(64):
            run = rng.randrange(2)
            await drive(dut, run=run)
            await tick(dut)
            advance(program, model, run)

            low = read_resolvable(dut.uo_out, "F35 ACC low byte")
            assert low == (model["acc"] & 0xFF), (
                f"F35 program {program_index}, edge {edge_index}: "
                f"low byte expected 0x{model['acc'] & 0xFF:02X}, got 0x{low:02X}"
            )
            await drive(dut, byte_sel=1)
            await Timer(settle_time(dut), unit="ns")
            high = read_resolvable(dut.uo_out, "F35 ACC high byte")
            assert high == ((model["acc"] >> 8) & 0xFF), (
                f"F35 program {program_index}, edge {edge_index}: "
                f"high byte expected 0x{model['acc'] >> 8:02X}, got 0x{high:02X}"
            )
            await drive(dut, byte_sel=0)

            if cpu is not None:
                for signal_name, expected in (
                    ("pc", model["pc"]),
                    ("acc", model["acc"]),
                    ("ir", model["ir"]),
                    ("halted", model["halted"]),
                ):
                    actual = read_resolvable(
                        getattr(cpu, signal_name),
                        f"F35 {signal_name}",
                    )
                    assert actual == expected, (
                        f"F35 program {program_index}, edge {edge_index}: "
                        f"{signal_name} expected {expected:#x}, got {actual:#x}"
                    )
        if program_index % 100 == 99:
            cocotb.log.info("F35 reference-model programs completed: %d", program_index + 1)
