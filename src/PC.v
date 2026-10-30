
module PC(
    input wire clk,
    input wire rst_n,
    input wire i_jump_en,
    input wire i_en, //the execute input is being fed (execute = run & ~halted)
    input wire [2:0] i_jump_addr,
    output wire [2:0] o_pc
);
    
reg [2:0] current_pc;

always @(posedge clk) begin
    if(~rst_n) begin
        current_pc <= 3'b000;
    end else if(i_en) begin
        current_pc <= i_jump_en ? i_jump_addr : (current_pc + 1'b1); //increment pc if not halted and not jumping
    end
end

assign o_pc = current_pc;

endmodule //PC
