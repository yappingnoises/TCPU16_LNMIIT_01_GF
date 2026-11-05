import cocotb

from coros.bench import (
    ADD,
    HALT,
    LOAD,
    SHL,
    SUB,
    XOR,
    drive,
    expect_next,
    instruction,
    load_program,
    read_resolvable,
    reset,
    settle_time,
    start,
    start_running,
)

from cocotb.triggers import Timer

@cocotb.test()
async def test_vplan_alu_and_outputs(dut):
    await start(dut)

    # F09: every immediate zero-extends, including after a nonzero result.
    for immediate in range(32):
        await reset(dut)
        await load_program(
        dut,
            [instruction(LOAD, 31), instruction(LOAD, immediate)]
            + [instruction(HALT)] * 6
        )
        await start_running(dut)
        await expect_next(dut, 31, "F09 precondition")
        await expect_next(dut, immediate, f"F09 immediate {immediate}")

    # F10: immediate addition.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5), instruction(ADD, 3)]
        + [instruction(HALT)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 5, "F10 LOAD")
    await expect_next(dut, 8, "F10 ADD")

    # F11: carry from bit 7 into the high byte.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 31),
            instruction(SHL, 3),
            instruction(ADD, 6),
            instruction(ADD, 5),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    for value in (31, 0x00F8, 0x00FE, 0x0103):
        await expect_next(dut, value, "F11")

    # F12: arithmetic is modulo 65536.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 31),
            instruction(SHL, 5),
            instruction(ADD, 31),
            instruction(SHL, 5),
            instruction(ADD, 31),
            instruction(SHL, 1),
            instruction(ADD, 1),
            instruction(ADD, 1),
        ]
    )
    await start_running(dut)
    for value in (31, 0x03E0, 0x03FF, 0x7FE0, 0x7FFF, 0xFFFE, 0xFFFF, 0):
        await expect_next(dut, value, "F12")

    # F13: subtraction.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 10), instruction(SUB, 3)]
        + [instruction(HALT)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 10, "F13 LOAD")
    await expect_next(dut, 7, "F13 SUB")

    # F14: borrow across the byte boundary.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 2),
            instruction(SHL, 7),
            instruction(SUB, 1),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    for value in (2, 0x0100, 0x00FF):
        await expect_next(dut, value, "F14")

    # F15: subtraction underflow wraps modulo 65536.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 0), instruction(SUB, 1)]
        + [instruction(HALT)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 0, "F15 LOAD")
    await expect_next(dut, 0xFFFF, "F15 SUB")

    # F16: each low-three-bit shift amount is tested from the same ACC value.
    for amount in range(8):
        await reset(dut)
        await load_program(
        dut,
            [instruction(LOAD, 3), instruction(SHL, amount)]
            + [instruction(HALT)] * 6
        )
        await start_running(dut)
        await expect_next(dut, 3, f"F16 shift {amount} LOAD")
        await expect_next(dut, 3 << amount, f"F16 shift {amount}")

    # F17: high bits shifted out are discarded, not rotated.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 31),
            instruction(SHL, 7),
            instruction(SHL, 7),
            instruction(SHL, 2),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    for value in (31, 0x0F80, 0xC000, 0):
        await expect_next(dut, value, "F17")

    # F18: operand bits 4:3 of SHL are ignored.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 19),
            instruction(SHL, 0),
            instruction(SHL, 8),
            instruction(SHL, 16),
            instruction(SHL, 24),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    for _ in range(5):
        await expect_next(dut, 19, "F18")

    # F19/F20: XOR uses a zero-extended immediate and preserves upper bits.
    await reset(dut)
    await load_program(
        dut,
        [
            instruction(LOAD, 31),
            instruction(SHL, 7),
            instruction(SHL, 7),
            instruction(XOR, 31),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
            instruction(HALT),
        ]
    )
    await start_running(dut)
    for value in (31, 0x0F80, 0xC000, 0xC01F):
        await expect_next(dut, value, "F19/F20")

    # F21/F22/F23: both output bytes, asynchronous byte select, and no
    # additional output-register cycle after ACC commits.
    await reset(dut)
    await load_program(
        dut,
        [instruction(LOAD, 31), instruction(SHL, 7)]
        + [instruction(HALT)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 31, "F21/F23 LOAD")
    await expect_next(dut, 0x0F80, "F21/F23 SHL")
    await drive(dut, byte_sel=0)
    assert read_resolvable(dut.uo_out, "F22 low byte") == 0x80
    await drive(dut, byte_sel=1)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F22 high byte") == 0x0F
    await drive(dut, byte_sel=0)
    await Timer(settle_time(dut), unit="ns")
