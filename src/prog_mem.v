
module prog_mem #(
    parameter WIDTH = 8,
    parameter WORD_SIZE = 8
) (
    input wire clk,
    input wire i_write_en,
    input wire [2:0] i_write_addr,
    input wire [2:0] i_read_addr,
    input wire [WIDTH-1:0] i_write_data,
    output wire [WIDTH-1:0] o_read_data
);

/*
    8x8 memory block
    no reset
    combinational persistent read
    written by loader
    initially undefined values in memory until written
*/

reg [WIDTH-1:0] mem [0:WORD_SIZE-1];

always @(posedge clk) begin
    if(i_write_en) begin
        mem[i_write_addr] <= i_write_data;
    end
end

assign o_read_data = mem[i_read_addr];

endmodule
