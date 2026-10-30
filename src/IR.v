
module IR(
    input wire clk,
    input wire rst_n,
    input wire [7:0] i_instr,
    input wire i_execute,
    output wire [7:0] o_ir
);

/*for debug purposes, to make a copy of the instructions*/

reg [7:0] ir;

always @(posedge clk) begin
    if(!rst_n) begin
        ir <= 8'h00;
    end else if(i_execute) begin
        ir <= i_instr;
    end
end

assign o_ir = ir;
    
endmodule //IR
