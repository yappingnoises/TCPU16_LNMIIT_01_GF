import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import RisingEdge
from coros.initialise import initialise
from coros.load_instructions import load_instructions


# test F05
@cocotb.test()
async def F05(dut):
    # Prog_load held high for multiple edges must only write one word

    await initialise(dut) #initialising clock + resets

    input_instr = [0x0000, 0x0001]

    mem = dut.tcpu.cpu.u_prog_mem.mem

    for i in range(len(input_instr)):
    
        dut.uio_in[0].value = 1
        dut.ui_in.value = input_instr[i]
        for i in range(5):
            await RisingEdge(dut.clk)
            for j in range(4):
                cocotb.log.info(f"edge {i}, memory value: {mem[j].value}")
                cocotb.log.info("----")
        
        dut.uio_in[0].value = 0
        await ClockCycles(dut.clk, 3)



# test F06
@cocotb.test()
async def F06(dut):
    # ith pulse of Prog_load must write ith word to memory
    await initialise(dut)

    input_instr = [0,1,2,3,12,34,81,255]

    await load_instructions(dut, input_instr, 3)

    mem = dut.tcpu.cpu.u_prog_mem.mem
    for j in range(8):
        cocotb.log.info(f"memory value{j}: {mem[j].value}")
        assert mem[j].value == input_instr[j]
        cocotb.log.info("----")

#test F07 
@cocotb.test()
async def F07(dut):
    #9th load overwrites 0th word 
        await initialise(dut)
        
        input_instr = [0,1,2,3,12,34,81,255,99]
        
        await load_instructions(dut, input_instr, 3)
        
        mem = dut.tcpu.cpu.u_prog_mem.mem
        for j in range(1,9):
            cocotb.log.info(f"memory value{j%8}: {mem[j%8].value}")
            assert mem[j%8].value == input_instr[j]
            cocotb.log.info("----")

    
#test F08
@cocotb.test()
async def F08(dut):
     #words arent loaded when run = 1
    await initialise(dut)

    input_instr = [0,1,2,3,12,34,81,255]

    await initialise(dut)
    dut.tcpu.cpu.run.value = 1
    await load_instructions(dut, input_instr, 3)

    mem = dut.tcpu.cpu.u_prog_mem.mem

    for i in range(8):
        cocotb.log.info(f"memory value{i}: {mem[i].value}")
        #assert mem[i].value == "xxxxxxxx"
        cocotb.log.info("----")




