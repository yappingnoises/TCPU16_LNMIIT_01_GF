import cocotb
from cocotb.triggers import RisingEdge,FallingEdge
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from coros.initialise import initialise
from coros.load_instructions import load_instructions

# test F09
@cocotb.test()
async def F09(dut):
    await initialise(dut)

    instructions = ["00001000","00011111", "00000000"]

    await load_instructions(dut, instructions,3)

    run = dut.tcpu.cpu.run
    acc_out = dut.tcpu.cpu.acc_out
    byte_sel = dut.tcpu.cpu.byte_sel
    acc = dut.tcpu.cpu.acc

    run.value = 1 #start running
    await ClockCycles(dut.clk, 3)

    for i in range(len(instructions)):
        byte_sel.value = 0
        await RisingEdge(dut.clk)
        
        
        cocotb.log.info(f"acc_out: {acc_out.value}, acc: {acc.value}, byte_sel: {byte_sel.value}")
        cocotb.log.info("----")
        byte_sel.value = 1
        await FallingEdge(dut.clk)
        
        cocotb.log.info(f"acc_out: {acc_out.value}, acc: {acc.value}, byte_sel: {byte_sel.value}")
        cocotb.log.info("======================")
    
