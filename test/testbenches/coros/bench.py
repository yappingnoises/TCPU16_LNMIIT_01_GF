import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLOCK_PERIOD_NS = 100
RTL_SETTLE_NS = 2
GATE_SETTLE_NS = 20
PROGRAM_WORDS = 8
LOAD = 0b000
ADD = 0b001
SUB = 0b010
SHL = 0b011
XOR = 0b100
JMP = 0b101
JZ = 0b110
HALT = 0b111


def instruction(opcode, operand=0):
    return ((opcode & 0b111) << 5) | (operand & 0b11111)


def read_resolvable(signal, description):
    value = signal.value
    assert value.is_resolvable, f"{description} contains X/Z: {value}"
    return int(value)


def rtl_cpu(dut):
    wrapper = getattr(dut, "tcpu", None)
    return getattr(wrapper, "cpu", None) if wrapper is not None else None


def rtl_loader(dut):
    cpu = rtl_cpu(dut)
    return getattr(cpu, "u_prog_loader", None) if cpu is not None else None


def architectural_state(cpu):
    if cpu is None:
        return None
    return tuple(
        read_resolvable(getattr(cpu, name), f"architectural {name}")
        for name in ("pc", "acc", "ir", "halted")
    )


def settle_time(dut):
    return RTL_SETTLE_NS if rtl_cpu(dut) is not None else GATE_SETTLE_NS


async def settle(dut):
    await Timer(settle_time(dut), unit="ns")


async def drive(dut, *, prog_load=None, run=None, byte_sel=None):
    value = int(dut.uio_in.value)
    if prog_load is not None:
        value = (value & ~0b001) | int(bool(prog_load))
    if run is not None:
        value = (value & ~0b010) | (int(bool(run)) << 1)
    if byte_sel is not None:
        value = (value & ~0b100) | (int(bool(byte_sel)) << 2)
    dut.uio_in.value = value
    await Timer(1, unit="ns")


async def tick(dut, count=1):
    for _ in range(count):
        await RisingEdge(dut.clk)
        await settle(dut)


async def start(dut):
    dut.clk.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns").start())
    await tick(dut, 5)
    dut.rst_n.value = 1
    await tick(dut, 5)


async def reset(dut):
    await drive(dut, prog_load=0, run=0, byte_sel=0)
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await tick(dut, 5)
    dut.rst_n.value = 1
    await tick(dut, 5)


async def load_word(dut, word, high_cycles=4):
    await drive(dut, prog_load=1)
    dut.ui_in.value = word & 0xFF
    await tick(dut, high_cycles)
    await drive(dut, prog_load=0)
    await tick(dut, 4)


async def load_program(dut, words):
    assert len(words) == PROGRAM_WORDS, (
        f"program must initialize all {PROGRAM_WORDS} memory words"
    )
    await drive(dut, run=0, prog_load=0, byte_sel=0)
    for word in words:
        await load_word(dut, word)


async def start_running(dut):
    await drive(dut, run=1)
    await tick(dut, 2)


async def accumulator(dut):
    await drive(dut, byte_sel=0)
    await settle(dut)
    low = read_resolvable(dut.uo_out, "ACC low byte")
    await drive(dut, byte_sel=1)
    await settle(dut)
    high = read_resolvable(dut.uo_out, "ACC high byte")
    await drive(dut, byte_sel=0)
    await settle(dut)
    return (high << 8) | low


async def expect_acc(dut, expected, feature):
    actual = await accumulator(dut)
    assert actual == expected, (
        f"{feature}: expected ACC=0x{expected:04X}, got 0x{actual:04X}"
    )
    return actual


async def expect_next(dut, expected, feature):
    await tick(dut)
    return await expect_acc(dut, expected, feature)
