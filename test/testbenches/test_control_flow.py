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


@cocotb.test(name="F24")
async def test_f24_all_jump_targets_are_reachable(dut):
    await start(dut)
    cpu = rtl_cpu(dut)
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


@cocotb.test(name="F25a")
async def test_f25_jmp_ignored_fields_do_not_change_decode(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(JMP, 0b11000 | 3)]
        + [instruction(LOAD, 0)] * 2
        + [instruction(LOAD, 17)]
        + [instruction(HALT, 31)] * 4,
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 17, "F25 JMP ignored fields")


@cocotb.test(name="F25b")
async def test_f25_jz_ignored_fields_do_not_change_decode(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(JZ, 0b11000 | 5)]
        + [instruction(LOAD, 0)] * 4
        + [instruction(LOAD, 19)]
        + [instruction(HALT, 31)] * 2,
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 19, "F25 JZ ignored fields")


@cocotb.test(name="F26")
async def test_f26_jz_taken_when_accumulator_is_zero(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(JZ, 6)]
        + [instruction(LOAD, 1)] * 5
        + [instruction(LOAD, 22)]
        + [instruction(HALT)],
    )
    await start_running(dut)
    await tick(dut)
    await expect_next(dut, 22, "F26")


@cocotb.test(name="F27")
async def test_f27_jz_falls_through_when_accumulator_nonzero(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    await expect_next(dut, 5, "F27 LOAD")
    await expect_next(dut, 5, "F27 JZ")
    await expect_next(dut, 7, "F27 fallthrough")


@cocotb.test(name="F28")
async def test_f28_jz_checks_every_accumulator_bit(dut):
    await start(dut)
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


@cocotb.test(name="F29")
async def test_f29_jz_observes_new_subtraction_result(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    await expect_next(dut, 1, "F29 LOAD")
    await expect_next(dut, 0, "F29 SUB")
    await tick(dut)
    await expect_next(dut, 23, "F29 JZ uses SUB result")
