import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge

# ============ test F04============== 
@cocotb.test
async def F04(dut):
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


    input_instr = [0,1,2,3,224,5,6,7] #11100000 = 224, it is the halted argument

    cocotb.log.info("Start program load")

    for i in range(len(input_instr)):
        
        dut.uio_in[0].value = 1
        dut.ui_in.value = input_instr[i]
        await ClockCycles(dut.clk, 3)
        dut.uio_in[0].value = 0
        await ClockCycles(dut.clk, 3)

    #programs loaded
    cocotb.log.info("Instructions loaded")

    halted = dut.tcpu.cpu.halted.value
    
    pc = int(dut.tcpu.cpu.pc.value)
   

    #running for 4 cycles then resetting to test
    dut.uio_in[1].value = 1 #deasserting run
    await ClockCycles(dut.clk,4) #pc starts running

    for i in range(20):
        await FallingEdge(dut.clk)
        #await ReadOnly()  # Pauses until all delta cycles and combinatorial propagation finish
        
        # Now signals like dut.pc.value reflect the stable, registered values
        cocotb.log.info(f" pc={pc}")
        #cocotb.log.info(halted)

    for i in range(8):
        out_memory_val = dut.tcpu.cpu.u_prog_mem.mem[i].value
        # assert out_memory_val == i
        cocotb.log.info(out_memory_val)

    # assert halted  == 1

    dut.rst_n.value = 0 #reset the cpu
    await ClockCycles(dut.clk,4) #checking values after 4 cycles of reset

    for i in range(10):
        await ClockCycles(dut.clk,1) #ticks for 1 cycles
        cocotb.log.info(pc)


    ##===== output checking =========


    



    
    
    







