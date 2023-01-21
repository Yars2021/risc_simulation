#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import sys

from enum import Enum
from isa import Opcode, AddrMode, Term, read_code


class SelOptions(int, Enum):
    INP = 0
    ALU = 1
    MEM = 2
    ARG = 3


class ALUOperations(int, Enum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3


class DataPath:
    def __init__(self, memory_size, input_buffer, data):
        assert memory_size > 0, "Memory size should be non-zero"
        assert len(data) < memory_size, "Not enough memory to contain this much data"
        self.memory_size = memory_size
        self.memory = data + [0] * (memory_size - len(data))
        self.gp_regs = [0] * 6
        self.addr_reg = 0
        self.buf_reg = 0
        self.out_reg = 0
        self.alu = 0
        self.arg = 0
        self.flag_neg = 0
        self.flag_zero = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

    def put_arg(self, value):
        self.arg = value

    def read_l_reg(self, l_sel):
        assert 0 <= l_sel <= 6, "The machine only has 6 registers (r0 - r5)"
        return self.gp_regs[l_sel]

    def read_r_reg(self, r_sel):
        assert 0 <= r_sel <= 6, "The machine only has 6 registers (r0 - r5)"
        return self.gp_regs[r_sel]

    def latch_reg(self, w_reg, sel_src: SelOptions):
        assert 0 <= w_reg <= 5, "The machine only has 6 registers (r0 - r5)"
        if sel_src is SelOptions.MEM:
            self.gp_regs[w_reg] = self.memory[self.addr_reg]
        elif sel_src is SelOptions.ALU:
            self.gp_regs[w_reg] = self.alu
        elif sel_src is SelOptions.INP:
            self.gp_regs[w_reg] = ord(self.input_buffer.pop(0)[0])

    def latch_addr(self, sel_addr: SelOptions):
        if sel_addr is SelOptions.ALU:
            self.addr_reg = self.alu
        elif sel_addr is SelOptions.ARG:
            self.addr_reg = self.arg

    def latch_out(self):
        self.out_reg = self.alu

    def latch_buf(self):
        self.buf_reg = self.alu

    def upd_flags(self):
        if self.alu == 0:
            self.flag_zero = 1
        else:
            self.flag_zero = 0

        if self.alu < 0:
            self.flag_neg = 1
        else:
            self.flag_neg = 0

    def wr(self):
        self.memory[self.addr_reg] = self.buf_reg

    def calculate(self, left, right, op: ALUOperations):
        if op is ALUOperations.ADD:
            self.alu = left + right
        elif op is ALUOperations.SUB:
            self.alu = left - right
        elif op is ALUOperations.MUL:
            self.alu = left * right
        elif op is ALUOperations.SUB:
            self.alu = left / right
        else:
            self.alu = left

        self.upd_flags()

    def output(self):
        self.output_buffer.append(chr(self.out_reg))


class ControlUnit:
    def __repr__(self):
        return 0


def main(args):
    assert len(args) == 2, "Wrong arguments: machine.py <code_file> <input_file>"
    code_file, input_file = args

    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
