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

@cocotb.test()
async def test_vplan_halt_pause_and_wrap(dut):
    await start(dut)

    # F30: HALT freezes execution across clock edges and run toggles.
    await load_program(
        dut,
        [instruction(LOAD, 17), instruction(HALT, 31)]
        + [instruction(ADD, 1)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 17, "F30 LOAD")
    await expect_next(dut, 17, "F30 HALT")
    cpu = rtl_cpu(dut)
    halt_state = architectural_state(cpu)
    await tick(dut, 10)
    await expect_acc(dut, 17, "F30 halted freeze")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, "F30 architectural state changed after HALT"
    await drive(dut, run=0)
    await tick(dut, 3)
    await expect_acc(dut, 17, "F30 halted with run low")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, "F30 run-low toggle changed halted state"
    await drive(dut, run=1)
    await tick(dut, 5)
    await expect_acc(dut, 17, "F30 halted with run high")
    if cpu is not None:
        assert architectural_state(cpu) == halt_state, "F30 run-high toggle changed halted state"

    # F31: run toggles do not clear HALT; reset does.
    await drive(dut, run=0)
    await tick(dut, 3)
    await load_word(dut, instruction(LOAD, 23))
    await drive(dut, run=1)
    await tick(dut, 5)
    await expect_acc(dut, 17, "F31 halt remains sticky")
    await reset(dut)
    await start_running(dut)
    await expect_next(dut, 23, "F31 reset releases HALT")

    # F32/F33: pausing holds state; resuming continues at the held PC.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7
    )
    await start_running(dut)
    await expect_next(dut, 5, "F32/F33 LOAD")
    await expect_next(dut, 6, "F32/F33 first ADD")
    await drive(dut, run=0)
    await tick(dut, 3)
    paused_value = await accumulator(dut)
    cpu = rtl_cpu(dut)
    paused_state = architectural_state(cpu)
    await tick(dut, 5)
    assert await accumulator(dut) == paused_value, "F32 paused ACC changed"
    if cpu is not None:
        assert architectural_state(cpu) == paused_state, "F32 architectural state changed while paused"
    await drive(dut, run=1)
    await tick(dut, 2)
    await expect_next(dut, paused_value + 1, "F33 resume from held PC")

    # F34: sequential execution wraps from PC 7 to PC 0.
    await reset(dut)
    await load_program(dut, [instruction(ADD, 1)] * PROGRAM_WORDS)
    await start_running(dut)
    for step in range(1, 10):
        await expect_next(dut, step, f"F34 PC wrap step {step}")
        cpu = rtl_cpu(dut)
        if cpu is not None:
            assert read_resolvable(cpu.pc, f"F34 PC after step {step}") == step % 8

@cocotb.test()
async def test_vplan_run_load_reset_edges(dut):
    await start(dut)

    # F39: a load strobe coincident with run is rejected.
    await load_program(
        dut,
        [instruction(LOAD, 5)] + [instruction(ADD, 1)] * 7
    )
    await start_running(dut)
    await expect_next(dut, 5, "F39 initial LOAD")
    await drive(dut, prog_load=1)
    dut.ui_in.value = instruction(HALT)
    await tick(dut, 4)
    await drive(dut, prog_load=0)
    await tick(dut, 4)
    await expect_acc(dut, 5, "F39 run blocks load at wrapped PC")

    # F40: a level held across reset release must not create another write.
    await reset(dut)
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

    # F41: program memory can be written while halted, without resuming CPU.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 11), instruction(HALT)]
        + [instruction(ADD, 1)] * 6
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
        assert architectural_state(cpu) == halt_state, "F41 program write resumed halted CPU"
    await reset(dut)
    await start_running(dut)
    await expect_next(dut, 25, "F41 written word executes after reset")

    # F42: reset during loading resets the address, but preserves earlier words.
    await reset(dut)
    await load_word(dut, instruction(LOAD, 1))
    await load_word(dut, instruction(LOAD, 2))
    await load_word(dut, instruction(LOAD, 3))
    await reset(dut)
    await load_word(dut, instruction(LOAD, 24))
    await start_running(dut)
    await expect_next(dut, 24, "F42 word zero replaced after reset")
    await expect_next(dut, 2, "F42 word one retained")
    await expect_next(dut, 3, "F42 word two retained")

    # F43: zero-shift and zero-XOR commit without changing ACC.
    await reset(dut)
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
        ]
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
