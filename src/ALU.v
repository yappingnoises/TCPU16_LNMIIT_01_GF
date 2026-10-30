module ALU(
    input wire [7:0] i_instr,
    input wire [15:0] i_acc,
    output reg [15:0] o_acc, //unsigned, underflow in SUB just goes BOOM (why no support for this?)
    output reg [2:0] o_jump_addr,
    output reg o_jump_en,
    output reg o_acc_wr,
    output reg o_halted
);

/* decodes and performs operations based on the decoded opcode */

wire [4:0] imm;
wire [2:0] opcode;

assign imm = i_instr[4:0];
assign opcode = i_instr[7:5];

always @(*) begin

    //defaults to avoid latches, and to avoid accidental jumps or halts
    o_acc       = i_acc;
    o_jump_en   = 0;
    o_jump_addr = 3'b000;
    o_acc_wr    = 0;
    o_halted    = 0;
    
    case(opcode) 

    3'b000: begin //LOAD imm
        o_acc    = {11'b0, imm};
        o_acc_wr = 1;
    end
    3'b001: begin //ADD imm
        o_acc    = i_acc + {11'b0, imm};
        o_acc_wr = 1;
    end
    3'b010: begin //SUB imm
        o_acc    = i_acc - {11'b0, imm};
        o_acc_wr = 1;
    end
    3'b011: begin //SHL sh (shift left)
        o_acc    = i_acc << imm[2:0]; //only 7 possible shifts, so only use 3 bits of imm
        o_acc_wr = 1;
    end
    3'b100: begin //XOR imm
        o_acc    = i_acc ^ {11'b0, imm};
        o_acc_wr = 1;
    end
    3'b101: begin //JUMP adr
        o_jump_en   = 1;
        o_jump_addr = imm[2:0]; //only 7 memory locations, so only use 3 bits of imm
    end
    3'b110: begin //JUMPZ adr
        if(i_acc == 16'h0000) begin
            o_jump_en   = 1;
            o_jump_addr = imm[2:0];
        end
    end
    3'b111: begin //HALT
        o_halted = 1;
    end

    endcase

end
    
endmodule //ALU
