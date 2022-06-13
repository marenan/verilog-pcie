#!/usr/bin/env python
"""
Generates a PCIe TLP BAR demux wrapper with the specified number of ports
"""

import argparse
from jinja2 import Template


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('-p', '--ports',  type=int, default=4, help="number of ports")
    parser.add_argument('-n', '--name',   type=str, help="module name")
    parser.add_argument('-o', '--output', type=str, help="output file name")

    args = parser.parse_args()

    try:
        generate(**args.__dict__)
    except IOError as ex:
        print(ex)
        exit(1)


def generate(ports=4, name=None, output=None):
    n = ports

    if name is None:
        name = "pcie_tlp_demux_bar_wrap_{0}".format(n)

    if output is None:
        output = name + ".v"

    print("Generating {0} port PCIe TLP demux (BAR ID) wrapper {1}...".format(n, name))

    cn = (n-1).bit_length()

    t = Template(u"""/*

Copyright (c) 2022 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/

// Language: Verilog 2001

`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * PCIe TLP {{n}} port demux (BAR ID) (wrapper)
 */
module {{name}} #
(
    // TLP data width
    parameter TLP_DATA_WIDTH = 256,
    // TLP strobe width
    parameter TLP_STRB_WIDTH = TLP_DATA_WIDTH/32,
    // TLP header width
    parameter TLP_HDR_WIDTH = 128,
    // Sequence number width
    parameter SEQ_NUM_WIDTH = 6,
    // TLP segment count
    parameter TLP_SEG_COUNT = 1,
    // Base BAR
    parameter BAR_BASE = 0,
    // BAR stride
    parameter BAR_STRIDE = 1,
    // Explicit BAR numbers (set to 0 to use base/stride)
    parameter BAR_IDS = 0
)
(
    input  wire                                    clk,
    input  wire                                    rst,

    /*
     * TLP input
     */
    input  wire [TLP_DATA_WIDTH-1:0]               in_tlp_data,
    input  wire [TLP_STRB_WIDTH-1:0]               in_tlp_strb,
    input  wire [TLP_SEG_COUNT*TLP_HDR_WIDTH-1:0]  in_tlp_hdr,
    input  wire [TLP_SEG_COUNT*SEQ_NUM_WIDTH-1:0]  in_tlp_seq,
    input  wire [TLP_SEG_COUNT*3-1:0]              in_tlp_bar_id,
    input  wire [TLP_SEG_COUNT*8-1:0]              in_tlp_func_num,
    input  wire [TLP_SEG_COUNT*4-1:0]              in_tlp_error,
    input  wire [TLP_SEG_COUNT-1:0]                in_tlp_valid,
    input  wire [TLP_SEG_COUNT-1:0]                in_tlp_sop,
    input  wire [TLP_SEG_COUNT-1:0]                in_tlp_eop,
    output wire                                    in_tlp_ready,

    /*
     * TLP outputs
     */
{%- for p in range(n) %}
    output wire [TLP_DATA_WIDTH-1:0]               out{{'%02d'%p}}_tlp_data,
    output wire [TLP_STRB_WIDTH-1:0]               out{{'%02d'%p}}_tlp_strb,
    output wire [TLP_SEG_COUNT*TLP_HDR_WIDTH-1:0]  out{{'%02d'%p}}_tlp_hdr,
    output wire [TLP_SEG_COUNT*SEQ_NUM_WIDTH-1:0]  out{{'%02d'%p}}_tlp_seq,
    output wire [TLP_SEG_COUNT*3-1:0]              out{{'%02d'%p}}_tlp_bar_id,
    output wire [TLP_SEG_COUNT*8-1:0]              out{{'%02d'%p}}_tlp_func_num,
    output wire [TLP_SEG_COUNT*4-1:0]              out{{'%02d'%p}}_tlp_error,
    output wire [TLP_SEG_COUNT-1:0]                out{{'%02d'%p}}_tlp_valid,
    output wire [TLP_SEG_COUNT-1:0]                out{{'%02d'%p}}_tlp_sop,
    output wire [TLP_SEG_COUNT-1:0]                out{{'%02d'%p}}_tlp_eop,
    input  wire                                    out{{'%02d'%p}}_tlp_ready,
{% endfor %}
    /*
     * Control
     */
    input  wire                                    enable
);

pcie_tlp_demux_bar #(
    .PORTS({{n}}),
    .TLP_DATA_WIDTH(TLP_DATA_WIDTH),
    .TLP_STRB_WIDTH(TLP_STRB_WIDTH),
    .TLP_HDR_WIDTH(TLP_HDR_WIDTH),
    .TLP_SEG_COUNT(TLP_SEG_COUNT),
    .BAR_BASE(BAR_BASE),
    .BAR_STRIDE(BAR_STRIDE),
    .BAR_IDS(BAR_IDS)
)
pcie_tlp_demux_bar_inst (
    .clk(clk),
    .rst(rst),

    /*
     * TLP input
     */
    .in_tlp_data(in_tlp_data),
    .in_tlp_strb(in_tlp_strb),
    .in_tlp_hdr(in_tlp_hdr),
    .in_tlp_seq(in_tlp_seq),
    .in_tlp_bar_id(in_tlp_bar_id),
    .in_tlp_func_num(in_tlp_func_num),
    .in_tlp_error(in_tlp_error),
    .in_tlp_valid(in_tlp_valid),
    .in_tlp_sop(in_tlp_sop),
    .in_tlp_eop(in_tlp_eop),
    .in_tlp_ready(in_tlp_ready),

    /*
     * TLP output
     */
    .out_tlp_data({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_data{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_strb({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_strb{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_hdr({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_hdr{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_seq({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_seq{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_bar_id({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_bar_id{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_func_num({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_func_num{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_error({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_error{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_valid({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_valid{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_sop({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_sop{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_eop({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_eop{% if not loop.last %}, {% endif %}{% endfor %} }),
    .out_tlp_ready({ {% for p in range(n-1,-1,-1) %}out{{'%02d'%p}}_tlp_ready{% if not loop.last %}, {% endif %}{% endfor %} }),

    /*
     * Control
     */
    .enable(enable)
);

endmodule

`resetall

""")

    print(f"Writing file '{output}'...")

    with open(output, 'w') as f:
        f.write(t.render(
            n=n,
            cn=cn,
            name=name
        ))
        f.flush()

    print("Done")


if __name__ == "__main__":
    main()
