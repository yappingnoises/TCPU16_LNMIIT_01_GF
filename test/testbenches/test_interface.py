import cocotb

from coros.bench import (
    ADD,
    HALT,
    LOAD,
    expect_next,
    instruction,
    load_program,
    read_resolvable,
    rtl_cpu,
    start,
    start_running,
)


@cocotb.test(name="F37")
async def test_f37_tiny_tapeout_interface_widths_and_defined_pins(dut):
    await start(dut)
    for pin_name, width in (
        ("ui_in", 8),
        ("uo_out", 8),
        ("uio_in", 8),
        ("uio_out", 8),
        ("uio_oe", 8),
        ("ena", 1),
        ("clk", 1),
        ("rst_n", 1),
    ):
        assert len(getattr(dut, pin_name)) == width, (
            f"F37 {pin_name} must be {width} bit(s)"
        )
    assert read_resolvable(dut.uio_out, "F37 uio_out") == 0
    assert read_resolvable(dut.uio_oe, "F37 uio_oe") == 0


@cocotb.test(name="F38")
async def test_f38_outputs_and_architectural_state_are_defined(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 0), instruction(ADD, 1)]
        + [instruction(HALT)] * 6,
    )
    await start_running(dut)
    await expect_next(dut, 0, "F38 initialized output")
    cpu = rtl_cpu(dut)
    if cpu is not None:
        for signal_name in ("pc", "acc", "ir", "halted"):
            signal = getattr(cpu, signal_name)
            read_resolvable(signal, f"F38 {signal_name}")
