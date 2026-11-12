import cocotb
from cocotb.triggers import Timer

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


@cocotb.test(name="F09")
async def test_f09_load_zero_extends_immediate(dut):
    await start(dut)
    for immediate in range(32):
        await reset(dut)
        await load_program(
            dut,
            [instruction(LOAD, 31), instruction(LOAD, immediate)]
            + [instruction(HALT)] * 6,
        )
        await start_running(dut)
        await expect_next(dut, 31, "F09 precondition")
        await expect_next(dut, immediate, f"F09 immediate {immediate}")


@cocotb.test(name="F10")
async def test_f10_immediate_addition(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 5), instruction(ADD, 3)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 5, "F10 LOAD")
    await expect_next(dut, 8, "F10 ADD")


@cocotb.test(name="F11")
async def test_f11_addition_carry_into_high_byte(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (31, 0x00F8, 0x00FE, 0x0103):
        await expect_next(dut, value, "F11")


@cocotb.test(name="F12")
async def test_f12_arithmetic_wraps_modulo_65536(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (31, 0x03E0, 0x03FF, 0x7FE0, 0x7FFF, 0xFFFE, 0xFFFF, 0):
        await expect_next(dut, value, "F12")


@cocotb.test(name="F13")
async def test_f13_subtraction(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 10), instruction(SUB, 3)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 10, "F13 LOAD")
    await expect_next(dut, 7, "F13 SUB")


@cocotb.test(name="F14")
async def test_f14_subtraction_borrows_across_byte_boundary(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (2, 0x0100, 0x00FF):
        await expect_next(dut, value, "F14")


@cocotb.test(name="F15")
async def test_f15_subtraction_underflow_wraps(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 1), instruction(SUB, 2)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 1, "F15 LOAD")
    await expect_next(dut, 0xFFFF, "F15 SUB")


@cocotb.test(name="F16")
async def test_f16_shift_amounts(dut):
    await start(dut)
    for amount in range(8):
        await reset(dut)
        await load_program(
            dut,
            [instruction(LOAD, 3), instruction(SHL, amount)]
            + [instruction(HALT)] * 6,
        )
        await start_running(dut)
        await expect_next(dut, 3, f"F16 shift {amount} LOAD")
        await expect_next(dut, 3 << amount, f"F16 shift {amount}")


@cocotb.test(name="F17")
async def test_f17_shift_discards_high_bits(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (31, 0x0F80, 0xC000, 0):
        await expect_next(dut, value, "F17")


@cocotb.test(name="F18")
async def test_f18_shift_ignores_operand_bits_4_to_3(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for _ in range(5):
        await expect_next(dut, 19, "F18")


@cocotb.test(name="F19")
async def test_f19_xor_uses_zero_extended_immediate(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (31, 0x0F80, 0xC000, 0xC01F):
        await expect_next(dut, value, "F19")


@cocotb.test(name="F20")
async def test_f20_xor_preserves_accumulator_upper_bits(dut):
    await start(dut)
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
        ],
    )
    await start_running(dut)
    for value in (31, 0x0F80, 0xC000, 0xC01F):
        await expect_next(dut, value, "F20")


@cocotb.test(name="F21")
async def test_f21_output_exposes_both_accumulator_bytes(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 31), instruction(SHL, 7)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 31, "F21 LOAD")
    await expect_next(dut, 0x0F80, "F21 SHL")
    await drive(dut, byte_sel=0)
    assert read_resolvable(dut.uo_out, "F21 low byte") == 0x80
    await drive(dut, byte_sel=1)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F21 high byte") == 0x0F


@cocotb.test(name="F22")
async def test_f22_byte_select_is_asynchronous(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 31), instruction(SHL, 7)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 31, "F22 LOAD")
    await expect_next(dut, 0x0F80, "F22 SHL")
    await drive(dut, byte_sel=0)
    assert read_resolvable(dut.uo_out, "F22 initial low byte") == 0x80
    await drive(dut, byte_sel=1)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F22 selected high byte") == 0x0F
    await drive(dut, byte_sel=0)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F22 selected low byte") == 0x80


@cocotb.test(name="F23")
async def test_f23_output_updates_with_accumulator_commit(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 31), instruction(SHL, 7)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 31, "F23 LOAD")
    await expect_next(dut, 0x0F80, "F23 SHL commit")
    await drive(dut, byte_sel=0)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F23 low byte after ACC commit") == 0x80
    await drive(dut, byte_sel=1)
    await Timer(settle_time(dut), unit="ns")
    assert read_resolvable(dut.uo_out, "F23 high byte after ACC commit") == 0x0F
