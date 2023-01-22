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
    BUF = 1
    MEM = 2
    ARG = 3
    REG = 4

class ALUOperations(int, Enum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3
    MOV = 4


class DataPath:
    def __init__(self, memory_size, input_buffer, data):
        assert memory_size > 0, "Memory size should be non-zero"
        assert len(data) < memory_size, "Not enough memory to contain this much data"
        self.memory_size = memory_size
        self.memory = data + [0] * (memory_size - len(data))

        self.gp_regs = [0] * 6
        self.addr_reg = 0
        self.buf_reg = 0
        self.ip_reg = 0
        self.reg_block_l = 0
        self.reg_block_r = 0

        self.left = 0
        self.right = 0
        self.alu = 0

        self.arg = 0
        self.ip = 0

        self.input_buffer = input_buffer
        self.output_buffer = []

    def read_l_reg(self, l_sel):
        assert 0 <= l_sel <= 6, "The machine only has 6 registers (r0 - r5)"
        self.reg_block_l = self.gp_regs[l_sel]

    def read_r_reg(self, r_sel):
        assert 0 <= r_sel <= 6, "The machine only has 6 registers (r0 - r5)"
        self.reg_block_r = self.gp_regs[r_sel]

    def latch_reg(self, w_sel, sel_src: SelOptions):
        assert 0 <= w_sel <= 5, "The machine only has 6 registers (r0 - r5)"
        if sel_src is SelOptions.MEM:
            self.gp_regs[w_sel] = self.memory[self.addr_reg]
        elif sel_src is SelOptions.BUF:
            self.gp_regs[w_sel] = self.buf_reg
        elif sel_src is SelOptions.INP:
            self.gp_regs[w_sel] = ord(self.input_buffer.pop(0)[0])

    def latch_addr(self, sel_addr: SelOptions):
        if sel_addr is SelOptions.BUF:
            self.addr_reg = self.buf_reg
        elif sel_addr is SelOptions.ARG:
            self.addr_reg = self.arg

    def latch_buf(self):
        self.buf_reg = self.alu

    def latch_ip(self):
        self.ip_reg = self.ip

    def flag_neg(self):
        return self.buf_reg < 0

    def flag_zero(self):
        return self.buf_reg == 0

    def rd(self):
        return self.memory[self.addr_reg]

    def wr(self):
        self.memory[self.addr_reg] = self.buf_reg

    def select_left(self, l_src: SelOptions):
        if l_src is SelOptions.MEM:
            self.left = self.rd()
        elif l_src is SelOptions.REG:
            self.left = self.reg_block_l

    def select_right(self, r_src: SelOptions):
        if r_src is SelOptions.MEM:
            self.right = self.rd()
        elif r_src is SelOptions.REG:
            self.right = self.reg_block_r

    def calculate(self, operation: ALUOperations):
        if operation is ALUOperations.ADD:
            self.alu = self.left + self.right
        elif operation is ALUOperations.SUB:
            self.alu = self.left - self.right
        elif operation is ALUOperations.MUL:
            self.alu = self.left * self.right
        elif operation is ALUOperations.DIV:
            self.alu = self.left / self.right
        elif operation is ALUOperations.MOV:
            self.alu = self.left

    def output(self):
        self.output_buffer.append(chr(self.buf_reg))


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
