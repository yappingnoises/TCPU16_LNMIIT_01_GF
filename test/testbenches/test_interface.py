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

@cocotb.test()
async def test_vplan_interface_and_defined_outputs(dut):
    await start(dut)

    # F37: verify the Tiny Tapeout pin names and widths.
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

    # F38: after reset and a complete load, the output and architectural state
    # are defined. RTL runs also check the internal architectural registers.
    await load_program(
        dut,
        [instruction(LOAD, 0), instruction(ADD, 1)]
        + [instruction(HALT)] * 6
    )
    await start_running(dut)
    await expect_next(dut, 0, "F38 initialized output")
    cpu = rtl_cpu(dut)
    if cpu is not None:
        for signal_name in ("pc", "acc", "ir", "halted"):
            signal = getattr(cpu, signal_name)
            read_resolvable(signal, f"F38 {signal_name}")
