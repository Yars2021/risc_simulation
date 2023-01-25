import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Коды операций"""

    DATA = "data"

    RD = "rd"
    WR = "wr"

    NOP = "nop"
    MOV = "mov"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"

    CMP = "cmp"
    JMP = "jmp"
    JG = "jg"
    JL = "jl"
    JE = "je"
    JNG = "jng"
    JNL = "jnl"
    JNE = "jne"

    HLT = "hlt"


args_number = {
    Opcode.DATA.value: 1,
    Opcode.NOP.value: 0,
    Opcode.RD.value: 0,
    Opcode.WR.value: 0,
    Opcode.MOV.value: 2,
    Opcode.ADD.value: 2,
    Opcode.SUB.value: 2,
    Opcode.MUL.value: 2,
    Opcode.DIV.value: 2,
    Opcode.MOD.value: 2,
    Opcode.CMP.value: 2,
    Opcode.JMP.value: 1,
    Opcode.JG.value: 1,
    Opcode.JL.value: 1,
    Opcode.JE.value: 1,
    Opcode.JNG.value: 1,
    Opcode.JNL.value: 1,
    Opcode.JNE.value: 1,
    Opcode.HLT.value: 0
}


class AddrMode(str, Enum):
    """Типы адресации"""

    PTR = "pointer"     # Указатель на ячейку памяти
    LIT = "literal"     # Константное значение
    REG = "register"    # Регистр


class Term(namedtuple('Term', 'line arg1 arg2 mode1 mode2')):
    """Описание выражения из исходного текста программы."""


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr['opcode'] = Opcode(instr['opcode'])
        if 'term' in instr:
            instr['term'] = Term(instr['term'][0], instr['term'][1], instr['term'][2],
                                 AddrMode(instr['term'][3]), AddrMode(instr['term'][4]))

    return code
