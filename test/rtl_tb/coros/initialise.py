import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

async def initialise(dut):
    
    cocotb.log.info("Starting Test")

    # Set the clock period to 1 us (1 MHz)
    clock = Clock(dut.clk, 1, unit="us")
    cocotb.start_soon(clock.start())

    ## ====== input loading ======

    cocotb.log.info("Reset")
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.uio_in.value = 0  # prog_load=0, run=0, byte_sel=0
    await ClockCycles(dut.clk, 4) #waiting for 4 edges to wait for synchronise. 3 is minimum
    dut.rst_n.value = 1 #rst_n deassert
    await ClockCycles(dut.clk,3)

    