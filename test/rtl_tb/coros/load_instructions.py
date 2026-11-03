import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


async def load_instructions(dut, input_instr,delay):
    cocotb.log.info("Start program load")
    
    for i in range(len(input_instr)):
    
        dut.uio_in[0].value = 1
        dut.ui_in.value = input_instr[i]
        await ClockCycles(dut.clk, delay)
        dut.uio_in[0].value = 0
        await ClockCycles(dut.clk, delay)
    
    #programs loaded
    cocotb.log.info("Instructions loaded")


