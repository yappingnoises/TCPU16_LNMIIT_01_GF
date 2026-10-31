import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# ============ test F01 ============== 
@cocotb.test
async def F01(dut):
    cocotb.log.info("Starting Test")

    # Set the clock period to 1 us (1 MHz)
    clock = Clock(dut.clk, 1, unit="us")
    cocotb.start_soon(clock.start())

    cocotb.log.info("Reset")
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.uio_in[1].value = 0 #run = 0 
    await ClockCycles(dut.clk, 4) #waiting for 4 edges to wait for synchronise. 3 is minimum
    dut.rst_n.value = 1 #rst_n deassert
    await ClockCycles(dut.clk,3)

    cocotb.log.info("Start program load")
    #instr1
    dut.uio_in[0].value = 1
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr2
    dut.uio_in[0].value = 1
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr3
    dut.uio_in[0].value = 1
    dut.ui_in.value = 2
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr4
    dut.uio_in[0].value = 1
    dut.ui_in.value = 3
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr5
    dut.uio_in[0].value = 1
    dut.ui_in.value = 4
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr6
    dut.uio_in[0].value = 1
    dut.ui_in.value = 5
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr7
    dut.uio_in[0].value = 1
    dut.ui_in.value = 6
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #instr8
    dut.uio_in[0].value = 1
    dut.ui_in.value = 7
    await ClockCycles(dut.clk, 3)
    dut.uio_in[0].value = 0
    await ClockCycles(dut.clk, 3)

    #programs loaded
    cocotb.log.info("Instructions loaded")

    #running for 4 cycles then resetting to test
    dut.uio_in[1].value = 1 #deasserting run
    await ClockCycles(dut.clk,3) #pc starts running

    await ClockCycles(dut.clk,4) #ticks for 4 cycles
    dut.rst_n.value = 0 #reset the cpu
    await ClockCycles(dut.clk,4) #checking values after 4 cycles of reset


    ##===== output checking =========
    # assert int(dut.tcpu.cpu.pc.value) == 0 #pc value
    # assert int(dut.tcpu.cpu.acc.value) == 0 #acc value
    # assert int(dut.tcpu.cpu.ir.value) == 0 #ir
    # assert int(dut.tcpu.cpu.halted.value) == 0 #halted

    await ClockCycles(dut.clk,1)
    dut.uio_in[2].value = 0 ##byte 0
    assert dut.uo_out.value == 0

    await ClockCycles(dut.clk,1)
    dut.uio_in[2].value = 1 ##byte 1
    assert dut.uo_out.value == 0
    







