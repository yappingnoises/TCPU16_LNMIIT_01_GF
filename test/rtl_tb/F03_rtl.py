import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# ============ test F03 ============== 
@cocotb.test
async def F03(dut):
    cocotb.log.info("Starting Test")

    # Set the clock period to 1 us (1 MHz)
    clock = Clock(dut.clk, 1, unit="us")
    cocotb.start_soon(clock.start())

    ## ====== input loading ======

    cocotb.log.info("Reset")
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.uio_in[1].value = 0 #run = 0 
    dut.uio_in[2].value = 0 #byte_sel = 0
    dut.uio_in[0].value = 0 #prog_load = 0
    await ClockCycles(dut.clk, 4) #waiting for 4 edges to wait for synchronise. 3 is minimum
    dut.rst_n.value = 1 #rst_n deassert
    await ClockCycles(dut.clk,4)


    input_instr = [0,1,2,3,4,5,6,7]

    cocotb.log.info("Start program load")

    for i in range(4):
        dut.uio_in[0].value = 1
        dut.ui_in.value = input_instr[i]
        await ClockCycles(dut.clk, 3)
        dut.uio_in[0].value = 0
        await ClockCycles(dut.clk, 3)

    for i in range(4):
        out_memory_val = dut.tcpu.cpu.u_prog_mem.mem[i].value
        assert out_memory_val == input_instr[i]
        cocotb.log.info(out_memory_val)

    #rst mid run
    cocotb.log.info("Resetting mid run")

    dut.rst_n.value = 0 #reset the cpu
    await ClockCycles(dut.clk,4) #checking values after 4 cycles of reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk,4)

    for i in range(5,8):
        dut.uio_in[0].value = 1
        dut.ui_in.value = input_instr[i]
        await ClockCycles(dut.clk, 3)
        dut.uio_in[0].value = 0
        await ClockCycles(dut.clk, 3)


    ##===== output checking =========


    for i in range(0,8):
        out_memory_val = dut.tcpu.cpu.u_prog_mem.mem[i].value
        #assert out_memory_val == input_instr[i]
        cocotb.log.info(out_memory_val)

    
    







