
module prog_loader(
    /*
        This module is used to load the program into the memory. It does so by using a data stream of 8 bit data and a load pulse.
    */
    input wire clk,
    input wire rst_n,
    input wire i_prog_load,
    input wire i_run,
    output wire [2:0] o_load_addr,
    output wire o_write_en
);
    

/* A
    == load_pulse == 
        - In case the i_prog_load is high for multiple cycle, you want to avoid load the same data multiple times. 
        So, we use a register pl_q to store the previous state of i_prog_load.
        load_pulse is asserted, on the first instance, and in further case, if the previous state and current state are same, load_pulse becomes low. 
        - This loads the data only once. 
*/


reg pl_q;

// pl_q has NO reset: it must sample prog_load at every edge including
// during reset (spec 4.2). rst_n here is already the synchronized signal.
always @(posedge clk) begin
    pl_q <= i_prog_load;
end

wire load_pulse;

assign load_pulse = i_prog_load & ~pl_q & ~i_run; //A 


//B (an address counter that ticks at rising edge of load_pulse)

reg [2:0] load_addr;

always @(posedge clk) begin
    if(rst_n == 0) begin
        load_addr <= 3'b000;
    end else if(load_pulse) begin
        load_addr <= load_addr + 1;
    end
end //B


assign o_load_addr = load_addr; //wasnt sure how to increment the address directly, so used a register and incremented it and then assigned it to the output.
assign o_write_en = load_pulse;

endmodule //prog_loader
