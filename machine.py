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
        self.reg_block_l = 0
        self.reg_block_r = 0

        self.left = 0
        self.right = 0
        self.alu = 0

        self.arg = 0
        self.l_arg = 0
        self.r_arg = 0

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

    def flag_neg(self):
        return self.buf_reg < 0

    def flag_zero(self):
        return self.buf_reg == 0

    def rd(self):
        return self.memory[self.addr_reg]["term"][1]

    def wr(self):
        new_term = Term(self.memory[self.addr_reg]["term"][0],
                        self.buf_reg,
                        self.memory[self.addr_reg]["term"][2],
                        self.memory[self.addr_reg]["term"][3],
                        self.memory[self.addr_reg]["term"][4])
        self.memory[self.addr_reg] = {"opcode": self.memory[self.addr_reg]["opcode"], "term": new_term}

    def select_left(self, l_src: SelOptions):
        if l_src is SelOptions.MEM:
            self.left = self.rd()
        elif l_src is SelOptions.REG:
            self.left = self.reg_block_l
        elif l_src is SelOptions.ARG:
            self.left = self.l_arg

    def select_right(self, r_src: SelOptions):
        if r_src is SelOptions.MEM:
            self.right = self.rd()
        elif r_src is SelOptions.REG:
            self.right = self.reg_block_r
        elif r_src is SelOptions.ARG:
            self.right = self.r_arg

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
    def __init__(self, data_path: DataPath):
        self.program = data_path.memory
        self.data_path = data_path
        self.instr_ptr = 0
        self._tick = 0

    def tick(self):
        self._tick += 1

    def get_tick(self):
        return self._tick

    def latch_ip(self, inc):
        if inc:
            self.instr_ptr += 1
        else:
            instr = self.program[self.instr_ptr]
            self.instr_ptr = instr["term"][1]

    def decode_and_execute_instruction(self):
        instr = self.program[self.instr_ptr]
        opcode = instr["opcode"]

        if opcode is Opcode.HLT:
            raise StopIteration

        if opcode is Opcode.NOP:
            self.latch_ip(True)
            self.tick()

        if opcode is Opcode.RD:
            w_sel = 0  # Данные при вводе попадают в %rax
            self.data_path.latch_reg(w_sel, SelOptions.INP)
            self.latch_ip(True)
            self.tick()

        if opcode is Opcode.WR:
            l_sel = 5  # Данные на вывод берутся из %rdi
            self.data_path.read_l_reg(l_sel)
            self.data_path.select_left(SelOptions.REG)
            self.data_path.calculate(ALUOperations.MOV)
            self.data_path.latch_buf()
            self.tick()

            self.data_path.output()
            self.latch_ip(True)
            self.tick()

        if opcode is Opcode.JMP:
            self.latch_ip(False)
            self.tick()

        if opcode is Opcode.JE:
            if self.data_path.flag_zero():
                self.latch_ip(False)
            else:
                self.latch_ip(True)
            self.tick()

        if opcode is Opcode.JNE:
            if self.data_path.flag_zero():
                self.latch_ip(True)
            else:
                self.latch_ip(False)
            self.tick()

        if opcode is Opcode.JG:
            if self.data_path.flag_zero() or self.data_path.flag_neg():
                self.latch_ip(True)
            else:
                self.latch_ip(False)
            self.tick()

        if opcode is Opcode.JL:
            if self.data_path.flag_neg():
                self.latch_ip(False)
            else:
                self.latch_ip(True)
            self.tick()

        if opcode is Opcode.JNG:
            if self.data_path.flag_zero() or self.data_path.flag_neg():
                self.latch_ip(False)
            else:
                self.latch_ip(True)
            self.tick()

        if opcode is Opcode.JNL:
            if self.data_path.flag_neg():
                self.latch_ip(True)
            else:
                self.latch_ip(False)
            self.tick()

        """         
        mov REG REG
        mov REG VAR
        mov REG ARG
        mov VAR REG
        mov VAR VAR
        mov VAR ARG
        """
        if opcode is Opcode.MOV:
            assert not (instr["term"][3] is AddrMode.LIT), "Invalid mov arguments!"

            if instr["term"][4] is AddrMode.REG:
                self.data_path.read_l_reg(instr["term"][2])
                self.data_path.select_left(SelOptions.REG)
            elif instr["term"][4] is AddrMode.PTR:
                self.data_path.arg = instr["term"][2]
                self.data_path.latch_addr(SelOptions.ARG)
                self.data_path.select_left(SelOptions.MEM)
            elif instr["term"][4] is AddrMode.LIT:
                self.data_path.l_arg = instr["term"][2]
                self.data_path.select_left(SelOptions.ARG)

            self.data_path.calculate(ALUOperations.MOV)
            self.data_path.latch_buf()
            self.tick()

            if instr["term"][3] is AddrMode.REG:
                w_sel = instr["term"][1]
                self.data_path.latch_reg(w_sel, SelOptions.BUF)
            elif instr["term"][3] is AddrMode.PTR:
                self.data_path.arg = instr["term"][1]
                self.data_path.latch_addr(SelOptions.ARG)
                self.data_path.wr()

            self.latch_ip(True)
            self.tick()

        """
        op REG REG
        op REG VAR
        op REG ARG
        op VAR REG
        op VAR ARG
        
        op VAR VAR нет, т.к. архитектура не позволяет
        """
        if opcode in {Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV, Opcode.CMP}:
            assert not (instr["term"][3] is AddrMode.PTR
                        and instr["term"][4] is AddrMode.PTR), "Operation VAR x VAR is not possible!"
            assert not (instr["term"][3] is AddrMode.LIT
                        and instr["term"][4] is AddrMode.LIT), "Operation LIT x LIT is not possible!"

            if instr["term"][3] is AddrMode.REG:
                self.data_path.read_l_reg(instr["term"][1])
                self.data_path.select_left(SelOptions.REG)
            elif instr["term"][3] is AddrMode.PTR:
                self.data_path.arg = instr["term"][1]
                self.data_path.latch_addr(SelOptions.ARG)
                self.data_path.select_left(SelOptions.MEM)
            elif instr["term"][3] is AddrMode.LIT:
                self.data_path.l_arg = instr["term"][1]
                self.data_path.select_left(SelOptions.ARG)

            if instr["term"][4] is AddrMode.REG:
                self.data_path.read_r_reg(instr["term"][2])
                self.data_path.select_right(SelOptions.REG)
            elif instr["term"][4] is AddrMode.PTR:
                self.data_path.arg = instr["term"][2]
                self.data_path.latch_addr(SelOptions.ARG)
                self.data_path.select_right(SelOptions.MEM)
            elif instr["term"][4] is AddrMode.LIT:
                self.data_path.l_arg = instr["term"][2]
                self.data_path.select_right(SelOptions.ARG)

            if opcode is Opcode.ADD:
                self.data_path.calculate(ALUOperations.ADD)
            elif opcode in {Opcode.SUB, Opcode.CMP}:
                self.data_path.calculate(ALUOperations.SUB)
            elif opcode is Opcode.MUL:
                self.data_path.calculate(ALUOperations.MUL)
            elif opcode is Opcode.DIV:
                self.data_path.calculate(ALUOperations.DIV)

            self.data_path.latch_buf()
            self.tick()

            if not (opcode is Opcode.CMP):
                if instr["term"][3] is AddrMode.REG:
                    w_sel = instr["term"][1]
                    self.data_path.latch_reg(w_sel, SelOptions.BUF)
                elif instr["term"][3] is AddrMode.PTR:
                    self.data_path.arg = instr["term"][1]
                    self.data_path.latch_addr(SelOptions.ARG)
                    self.data_path.wr()

            self.latch_ip(True)
            self.tick()

    def __repr__(self):
        state = "{{TICK: {}, IP: {}, ADDR: {}, BUF: {}, REG0 (RAX): {}, REG1 (RBX): {}, " \
                "REG2 (RCX): {}, REG3 (RDX): {}, REG4 (RSI): {}, REG5 (RDI): {}, N: {}, Z: {}}}".format(
            self._tick,
            self.instr_ptr,
            self.data_path.addr_reg,
            self.data_path.buf_reg,
            self.data_path.gp_regs[0],
            self.data_path.gp_regs[1],
            self.data_path.gp_regs[2],
            self.data_path.gp_regs[3],
            self.data_path.gp_regs[4],
            self.data_path.gp_regs[5],
            self.data_path.flag_neg(),
            self.data_path.flag_zero()
        )

        return state


def simulation(code, memory_size, input_buffer, limit):
    data_path = DataPath(memory_size, input_buffer, code)
    control_unit = ControlUnit(data_path)
    instr_counter = 0

    control_unit.__repr__()
    logging.debug('%s', control_unit)
    try:
        while True:
            assert limit > instr_counter, "Limit exceeded!"
            control_unit.decode_and_execute_instruction()
            control_unit.__repr__()
            instr_counter += 1
            logging.debug('%s', control_unit)
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        print("Iteration stopped (HLT)")
        pass
    logging.info("output_buffer: %s", repr(''.join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.get_tick()


def main(args):
    assert len(args) == 2, "Wrong arguments: machine.py <code_file> <input_file>"
    code_file, input_file = args

    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, instr_counter, ticks = simulation(code, memory_size=128, input_buffer=[], limit=1024)

    print(''.join(output))
    print("executed instructions:", instr_counter, "\nticks:", ticks, "\n--------------------")
    print("output buffer:\n", output)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    #main(sys.argv[1:])
    main(["/home/yars/PycharmProjects/virtual_m/tests/test_instr.ins",
          "/home/yars/PycharmProjects/virtual_m/tests/test_instr.ins"])
