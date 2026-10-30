/*
 * Copyright (c) 2026 Toshi
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_yappingnoises_TCPU16 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire [7:0] acc_out;

  toy_cpu16 cpu (
      .clk(clk),
      .rst_n(rst_n),
      .prog_data(ui_in),
      .prog_load(uio_in[0]),
      .run(uio_in[1]),
      .byte_sel(uio_in[2]),
      .acc_out(acc_out)
  );

  assign uo_out  = acc_out;
  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  wire _unused = &{ena, uio_in[7:3], 1'b0};

endmodule
