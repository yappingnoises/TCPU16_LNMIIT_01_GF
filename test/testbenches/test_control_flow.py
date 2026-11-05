import cocotb

from coros.bench import (
    HALT,
    JMP,
    JZ,
    LOAD,
    PROGRAM_WORDS,
    SHL,
    SUB,
    expect_acc,
    expect_next,
    instruction,
    load_program,
    read_resolvable,
    reset,
    rtl_cpu,
    start,
    start_running,
    tick,
)

@cocotb.test()
async def test_vplan_control_flow(dut):
    await start(dut)
    cpu = rtl_cpu(dut)

    # F24: each of the eight jump targets is reachable.
    for target in range(PROGRAM_WORDS):
        await reset(dut)
        words = [instruction(JMP, target)] + [
            instruction(LOAD, 10 + address)
            for address in range(1, PROGRAM_WORDS)
        ]
        await load_program(dut, words)
        await start_running(dut)
        await tick(dut)
        if cpu is not None:
            assert read_resolvable(cpu.pc, f"F24 PC target {target}") == target
        if target == 0:
            await expect_acc(dut, 0, "F24 jump target 0")
        else:
            await expect_next(dut, 10 + target, f"F24 jump target {target}")

    # F25: ignored JMP/JZ fields and HALT operands do not alter decoding.
    await reset(dut)
    await load_program(
        dut,
        [instruction(JMP, 0b11000 | 3)]
        + [instruction(LOAD, 0)] * 2
        + [instruction(LOAD, 17)]
        + [instruction(HALT, 31)] * 4
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 17, "F25 JMP ignored fields")

    await reset(dut)
    await load_program(
        dut,
        [instruction(JZ, 0b11000 | 5)]
        + [instruction(LOAD, 0)] * 4
        + [instruction(LOAD, 19)]
        + [instruction(HALT, 31)] * 2
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 19, "F25 JZ ignored fields")

    # F26: JZ is taken when ACC is zero.
    await reset(dut)
    await load_program(
        dut,
        [instruction(JZ, 6)]
        + [instruction(LOAD, 1)] * 5
        + [instruction(LOAD, 22)]
        + [instruction(HALT)]
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 22, "F26")

    # F27: JZ falls through when ACC is nonzero.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 5),
            instruction(JZ, 6),
            instruction(LOAD, 7),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(LOAD, 22),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    await expect_next(dut, 5, "F27 LOAD")
    await expect_next(dut, 5, "F27 JZ")
    await expect_next(dut, 7, "F27 fallthrough")

    # F28: JZ checks every accumulator bit, not only the low byte.
    for bit in range(16):
        await reset(dut)
        shifts = [7] * (bit // 7)
        if bit % 7:
            shifts.append(bit % 7)
        words = [instruction(LOAD, 1)]
        words.extend(instruction(SHL, amount) for amount in shifts)
        words.append(instruction(JZ, 6))
        fallthrough = len(words)
        words.extend([instruction(LOAD, 31)] * (6 - len(words)))
        words.append(instruction(LOAD, 22))
        words.append(instruction(HALT))
        assert len(words) == PROGRAM_WORDS
        await load_program(dut, words)
        await start_running(dut)
        for _ in range(fallthrough + 1):
            await tick(dut)
        await expect_acc(dut, 31, f"F28 accumulator bit {bit}")

    # F29: a JZ immediately after SUB sees the newly committed result.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 1),
            instruction(SUB, 1),
            instruction(JZ, 6),
            instruction(LOAD, 5),
            instruction(HALT),
            instruction(HALT),
            instruction(LOAD, 23),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    await expect_next(dut, 1, "F29 LOAD")
    await expect_next(dut, 0, "F29 SUB")
    await tick(dut)
    await expect_next(dut, 23, "F29 JZ uses SUB result")
