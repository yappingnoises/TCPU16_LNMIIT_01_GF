import cocotb

from coros.bench import (
    ADD,
    HALT,
    LOAD,
    SHL,
    SUB,
    XOR,
    accumulator,
    architectural_state,
    drive,
    expect_acc,
    expect_next,
    instruction,
    load_program,
    load_word,
    read_resolvable,
    reset,
    rtl_cpu,
    start,
    start_running,
    tick,
)


@cocotb.test(name="F01")
async def test_f01_reset_clears_state_and_byte_select_is_live(dut):
    await start(dut)
    await expect_acc(dut, 0, "F01")
    cpu = rtl_cpu(dut)
    if cpu is not None:
        for signal_name in ("pc", "acc", "ir", "halted"):
            assert read_resolvable(
                getattr(cpu, signal_name), f"F01 {signal_name}"
            ) == 0


@cocotb.test(name="F02")
async def test_f02_reset_preserves_program_and_execution_trace(dut):
    await start(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 5),
            instruction(ADD, 3),
            instruction(SHL, 1),
            instruction(ADD, 1),
            instruction(SUB, 2),
            instruction(XOR, 7),
            instruction(ADD, 4),
            instruction(SHL, 2),
        ],
    )
    await start_running(dut)
    cpu = rtl_cpu(dut)
    trace_before = []
    state_trace_before = []
    for _ in range(6):
        await tick(dut)
        trace_before.append(await accumulator(dut))
        state_trace_before.append(architectural_state(cpu))

    await reset(dut)
    await start_running(dut)
    trace_after = []
    state_trace_after = []
    for _ in range(6):
        await tick(dut)
        trace_after.append(await accumulator(dut))
        state_trace_after.append(architectural_state(cpu))
    assert trace_after == trace_before, "F02 reset changed the retained program trace"
    if cpu is not None:
        assert state_trace_after == state_trace_before, (
            "F02 reset changed the architectural execution trace"
        )


@cocotb.test(name="F03")
async def test_f03_reset_during_loading_restarts_write_address(dut):
    await start(dut)
    await load_word(dut, instruction(LOAD, 1))
    await load_word(dut, instruction(LOAD, 2))
    await load_word(dut, instruction(LOAD, 3))
    await reset(dut)
    words = [instruction(LOAD, value) for value in (21, 22, 23, 24, 25, 26, 27, 28)]
    await load_program(dut, words)
    await start_running(dut)
    await expect_next(dut, 21, "F03")
    await expect_next(dut, 22, "F03")


@cocotb.test(name="F05")
async def test_f05_held_load_level_writes_one_word(dut):
    await start(dut)
    words = [instruction(LOAD, value) for value in (10, 1, 2, 3, 4, 5, 6, 7)]
    await drive(dut, prog_load=1)
    dut.ui_in.value = words[0]
    await tick(dut, 5)
    await drive(dut, prog_load=0)
    await tick(dut, 4)
    for word in words[1:]:
        await load_word(dut, word)
    await start_running(dut)
    for index, value in enumerate((10, 1, 2, 3, 4, 5, 6, 7)):
        await expect_next(dut, value, f"F05 word {index}")


@cocotb.test(name="F06")
async def test_f06_load_pulses_fill_program_memory_in_order(dut):
    await start(dut)
    words = [instruction(LOAD, value) for value in (3, 5, 7, 9, 11, 13, 15, 17)]
    await load_program(dut, words)
    await start_running(dut)
    for index, value in enumerate((3, 5, 7, 9, 11, 13, 15, 17)):
        await expect_next(dut, value, f"F06 word {index}")


@cocotb.test(name="F07")
async def test_f07_ninth_load_wraps_to_word_zero(dut):
    await start(dut)
    words = [instruction(LOAD, value) for value in (1, 2, 3, 4, 5, 6, 7, 8)]
    await load_program(dut, words)
    await load_word(dut, instruction(LOAD, 31))
    await start_running(dut)
    for index, value in enumerate((31, 2, 3, 4, 5, 6, 7, 8)):
        await expect_next(dut, value, f"F07 word {index}")


@cocotb.test(name="F08")
async def test_f08_load_is_rejected_while_running(dut):
    await start(dut)
    words = [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7
    await load_program(dut, words)
    await start_running(dut)
    await expect_next(dut, 5, "F08 initial LOAD")
    await drive(dut, prog_load=1)
    dut.ui_in.value = instruction(HALT)
    await tick(dut, 4)
    await drive(dut, prog_load=0)
    await tick(dut, 4)
    await expect_acc(dut, 5, "F08 load blocked while running")
