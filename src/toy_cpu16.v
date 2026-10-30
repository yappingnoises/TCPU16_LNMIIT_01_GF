
module toy_cpu16(
    input wire clk,
    input wire rst_n,
    input wire [7:0] prog_data,
    input wire prog_load,
    input wire run,
    input wire byte_sel,
    output wire [7:0] acc_out
);

/*-----------------------------------------------------------------------
    Mode O input synchronizers (SYNC_STAGES = 2)
    Two-flop synchronizers for run, prog_load and rst_n.
    No reset, no logic between stages (spec 4.2).
    prog_data and byte_sel are NOT synchronized:
    - prog_data is held stable by the load protocol (spec 2.1)
    - byte_sel is combinational only and never sampled by a flop
----------------------------------------------------------------------- */

reg run_s1,      run_sync;
reg pl_s1,       pl_sync;
reg rst_s1,      rst_sync;

always @(posedge clk) begin
    run_s1   <= run;       run_sync  <= run_s1;
    pl_s1    <= prog_load; pl_sync   <= pl_s1;
    rst_s1   <= rst_n;     rst_sync  <= rst_s1;
end

/*A == declared for verification visibility*/
reg [2:0] pc; //current pointer of program counter
reg [15:0] acc; //accumulator register
reg [7:0] ir; //current instruction |||| A
reg halted; //halted flag

//B intermediate signals 
wire execute; //enable signal for PC
wire [2:0] load_addr; //instruction memory load address
wire write_en; //load_pulse 
wire jump_en; //jump enable
wire [2:0] jump_addr; //jump address

wire [7:0] instr; //instruction read from memory
wire [2:0] pc_next; //next PC value from PC module
wire [15:0] alu_acc_out; //ALU computed accumulator
wire alu_acc_wr; //ALU writes to ACC
wire alu_halted; //ALU halt detected
wire [7:0] ir_val; //IR registered instruction


assign execute = run_sync & ~halted;

//B

prog_loader u_prog_loader (
    .clk(clk),
    .rst_n(rst_sync),
    .i_prog_load(pl_sync),
    .i_run(run_sync),
    .o_load_addr(load_addr),
    .o_write_en(write_en)
);

prog_mem #(
    .WIDTH(8),
    .WORD_SIZE(8)
) u_prog_mem (
    .clk(clk),
    .i_write_en(write_en),
    .i_write_addr(load_addr),
    .i_read_addr(pc),
    .i_write_data(prog_data),
    .o_read_data(instr)
);

IR u_IR (
    .clk(clk),
    .rst_n(rst_sync),
    .i_instr(instr),
    .i_execute(execute),
    .o_ir(ir_val)
);

ALU u_ALU (
    .i_instr(instr),
    .i_acc(acc),
    .o_acc(alu_acc_out),
    .o_jump_addr(jump_addr),
    .o_jump_en(jump_en),
    .o_acc_wr(alu_acc_wr),
    .o_halted(alu_halted)
);

PC u_PC (
    .clk(clk),
    .rst_n(rst_sync),
    .i_jump_en(jump_en),
    .i_en(execute),
    .i_jump_addr(jump_addr),
    .o_pc(pc_next)
); //B

always @(posedge clk) begin
    if(!rst_sync) begin
        acc    <= 16'h0000;
        pc     <= 3'b000;
        ir     <= 8'h00;
        halted <= 1'b0;
    end else if(execute) begin
        pc     <= pc_next;
        ir     <= instr;
        halted <= alu_halted;
        if(alu_acc_wr) begin
            acc <= alu_acc_out;
        end
    end
end

assign acc_out = byte_sel ? acc[15:8] : acc[7:0];


endmodule //toy_cpu16
