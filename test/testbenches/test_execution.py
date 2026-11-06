import cocotb

from coros.bench import (
    ADD,
    HALT,
    LOAD,
    PROGRAM_WORDS,
    SHL,
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


@cocotb.test(name="F30")
async def test_f30_halt_freezes_execution(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 17), instruction(HALT, 31)]
        + [instruction(ADD, 1)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 17, "F30 LOAD")
    await expect_next(dut, 17, "F30 HALT")
    cpu = rtl_cpu(dut)
    halt_state = architectural_state(cpu)
    await tick(dut, 10)
    await expect_acc(dut, 17, "F30 halted freeze")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, (
            "F30 architectural state changed after HALT"
        )
    await drive(dut, run=0)
    await tick(dut, 3)
    await expect_acc(dut, 17, "F30 halted with run low")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, (
            "F30 run-low toggle changed halted state"
        )
    await drive(dut, run=1)
    await tick(dut, 5)
    await expect_acc(dut, 17, "F30 halted with run high")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, (
            "F30 run-high toggle changed halted state"
        )


@cocotb.test(name="F31")
async def test_f31_halt_stays_sticky_until_reset(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 17), instruction(HALT, 31)]
        + [instruction(ADD, 1)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 17, "F31 LOAD")
    await expect_next(dut, 17, "F31 HALT")
    await drive(dut, run=0)
    await tick(dut, 3)
    await load_word(dut, instruction(LOAD, 23))
    await drive(dut, run=1)
    await tick(dut, 5)
    await expect_acc(dut, 17, "F31 halt remains sticky")
    await reset(dut)
    await start_running(dut)
    await expect_next(dut, 23, "F31 reset releases HALT")


@cocotb.test(name="F32")
async def test_f32_pause_holds_cpu_state(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7,
    )
    await start_running(dut)
    await expect_next(dut, 5, "F32 LOAD")
    await expect_next(dut, 6, "F32 first ADD")
    await drive(dut, run=0)
    await tick(dut, 3)
    paused_value = await accumulator(dut)
    cpu = rtl_cpu(dut)
    paused_state = architectural_state(cpu)
    await tick(dut, 5)
    assert await accumulator(dut) == paused_value, "F32 paused ACC changed"
    if cpu is not None:
        assert architectural_state(cpu) == paused_state, (
            "F32 architectural state changed while paused"
        )


@cocotb.test(name="F33")
async def test_f33_resume_continues_at_held_pc(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7,
    )
    await start_running(dut)
    await expect_next(dut, 5, "F33 LOAD")
    await expect_next(dut, 6, "F33 first ADD")
    await drive(dut, run=0)
    await tick(dut, 3)
    paused_value = await accumulator(dut)
    await tick(dut, 5)
    assert await accumulator(dut) == paused_value, "F33 paused ACC changed"
    await drive(dut, run=1)
    await tick(dut, 2)
    await expect_next(dut, paused_value + 1, "F33 resume from held PC")


@cocotb.test(name="F34")
async def test_f34_sequential_execution_wraps_pc(dut):
    await start(dut)
    await load_program(dut, [instruction(ADD, 1)] * PROGRAM_WORDS)
    await start_running(dut)
    for step in range(1, 10):
        await expect_next(dut, step, f"F34 PC wrap step {step}")
        cpu = rtl_cpu(dut)
        if cpu is not None:
            assert read_resolvable(cpu.pc, f"F34 PC after step {step}") == step % 8


@cocotb.test(name="F39")
async def test_f39_run_blocks_program_load(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7,
    )
    await start_running(dut)
    await expect_next(dut, 5, "F39 initial LOAD")
    await drive(dut, prog_load=1)
    dut.ui_in.value = instruction(HALT)
    await tick(dut, 4)
    await drive(dut, prog_load=0)
    await tick(dut, 4)
    await expect_acc(dut, 5, "F39 run blocks load at wrapped PC")


@cocotb.test(name="F40")
async def test_f40_held_load_across_reset_release_does_not_write(dut):
    await start(dut)
    await load_program(dut, [instruction(HALT)] * PROGRAM_WORDS)
    await start_running(dut)
    await drive(dut, prog_load=1)
    dut.ui_in.value = instruction(LOAD, 29)
    await tick(dut, 5)
    dut.rst_n.value = 0
    await tick(dut, 5)
    dut.rst_n.value = 1
    await tick(dut, 5)
    await drive(dut, prog_load=0, run=0)
    await tick(dut, 5)
    await start_running(dut)
    await expect_next(dut, 0, "F40 held load did not overwrite halted word")


@cocotb.test(name="F41")
async def test_f41_program_can_be_written_while_halted(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 11), instruction(HALT)]
        + [instruction(ADD, 1)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 11, "F41 LOAD")
    await expect_next(dut, 11, "F41 HALT")
    cpu = rtl_cpu(dut)
    halt_state = architectural_state(cpu)
    await drive(dut, run=0)
    await tick(dut, 3)
    await load_word(dut, instruction(LOAD, 25))
    await expect_acc(dut, 11, "F41 write while halted")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, (
            "F41 program write resumed halted CPU"
        )
    await reset(dut)
    await start_running(dut)
    await expect_next(dut, 25, "F41 written word executes after reset")


@cocotb.test(name="F42")
async def test_f42_reset_during_load_resets_address_not_prior_memory(dut):
    await start(dut)
    await load_word(dut, instruction(LOAD, 1))
    await load_word(dut, instruction(LOAD, 2))
    await load_word(dut, instruction(LOAD, 3))
    await reset(dut)
    await load_word(dut, instruction(LOAD, 24))
    await start_running(dut)
    await expect_next(dut, 24, "F42 word zero replaced after reset")
    await expect_next(dut, 2, "F42 word one retained")
    await expect_next(dut, 3, "F42 word two retained")


@cocotb.test(name="F43")
async def test_f43_zero_shift_and_xor_commit_results(dut):
    await start(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 21),
            instruction(SHL, 0),
            instruction(XOR, 0),
            instruction(ADD, 3),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ],
    )
    await start_running(dut)
    await expect_next(dut, 21, "F43 LOAD")
    await expect_next(dut, 21, "F43 SHL 0")
    cpu = rtl_cpu(dut)
    if cpu is not None:
        assert read_resolvable(cpu.ir, "F43 IR after SHL 0") == instruction(SHL, 0)
    await expect_next(dut, 21, "F43 XOR 0")
    if cpu is not None:
        assert read_resolvable(cpu.ir, "F43 IR after XOR 0") == instruction(XOR, 0)
    await expect_next(dut, 24, "F43 next instruction committed")
