import cocotb

from coros.bench import (
    ADD,
    HALT,
    LOAD,
    accumulator,
    drive,
    expect_acc,
    expect_next,
    instruction,
    load_program,
    read_resolvable,
    rtl_loader,
    start,
    tick,
)


@cocotb.test(name="F44a")
async def test_f44_run_and_load_synchronizer_latency(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 13)] + [instruction(ADD, 1)] * 7,
    )
    loader = rtl_loader(dut)
    await drive(dut, prog_load=1)
    dut.ui_in.value = instruction(LOAD, 14)
    for cycle, expected_address in ((1, 0), (2, 0), (3, 1)):
        await tick(dut)
        if loader is not None:
            assert read_resolvable(
                loader.load_addr, f"F44 load address edge {cycle}"
            ) == expected_address
    await drive(dut, prog_load=0)
    await tick(dut, 4)
    await drive(dut, run=1)
    await tick(dut)
    await expect_acc(dut, 0, "F44 run latency edge 1")
    await tick(dut)
    await expect_acc(dut, 0, "F44 run latency edge 2")
    await expect_next(dut, 14, "F44 run latency edge 3")


@cocotb.test(name="F44b")
async def test_f44_reset_synchronizer_latency(dut):
    await start(dut)
    await load_program(
        dut,
        [instruction(LOAD, 13)] + [instruction(HALT)] * 7,
    )
    await drive(dut, run=1)
    await tick(dut, 4)
    await expect_acc(dut, 13, "F44 establish nonzero accumulator")
    await drive(dut, run=0)
    await tick(dut, 3)
    paused_acc = await accumulator(dut)
    dut.rst_n.value = 0
    await tick(dut)
    await expect_acc(dut, paused_acc, "F44 reset latency edge 1")
    await tick(dut)
    await expect_acc(dut, paused_acc, "F44 reset latency edge 2")
    await tick(dut)
    await expect_acc(dut, 0, "F44 reset latency edge 3")
