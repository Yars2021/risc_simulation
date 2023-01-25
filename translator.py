#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

"""Транслятор asm в машинный код"""

import sys

from isa import Opcode, AddrMode, args_number, write_code, Term

# Словарь символов, непосредственно транслируемых в машинный код
symbol2opcode = {
    "data": Opcode.DATA,
    "rd": Opcode.RD,
    "wr": Opcode.WR,
    "wrn": Opcode.WRN,
    "nop": Opcode.NOP,
    "mov": Opcode.MOV,
    "add": Opcode.ADD,
    "sub": Opcode.SUB,
    "mul": Opcode.MUL,
    "div": Opcode.DIV,
    "mod": Opcode.MOD,
    "cmp": Opcode.CMP,
    "jmp": Opcode.JMP,
    "jg": Opcode.JG,
    "jl": Opcode.JL,
    "je": Opcode.JE,
    "jng": Opcode.JNG,
    "jnl": Opcode.JNL,
    "jne": Opcode.JNE,
    "hlt": Opcode.HLT
}

register_symbols = {
    "%reg0": "%reg0",
    "%reg1": "%reg1",
    "%reg2": "%reg2",
    "%reg3": "%reg3",
    "%reg4": "%reg4",
    "%reg5": "%reg5",

    "%rax": "%reg0",
    "%rbx": "%reg1",
    "%rcx": "%reg2",
    "%rdx": "%reg3",
    "%rsi": "%reg4",
    "%rdi": "%reg5",

    "%rin": "%reg0",
    "%rou": "%reg5"
}

registers2indexes = {
    "%reg0": 0,
    "%reg1": 1,
    "%reg2": 2,
    "%reg3": 3,
    "%reg4": 4,
    "%reg5": 5
}


def translate(text):
    line_ctr = 0
    terms = []
    instr = []
    labels = {}
    variables = {}
    data_section = False

    instr.append("jmp")
    terms.append(Term(line_ctr, ".start", 0, 0, 0))
    line_ctr += 1

    for line in text.split("\n"):
        tokens = line.split()

        # Пропускаем пустые строки и комментарии
        if len(tokens) == 0:
            continue
        if tokens[0][0] == ';':
            continue
        for i in range(len(tokens)):
            tokens[i] = str(tokens[i])
            if tokens[i][0] == ';':
                tokens = tokens[0:i]
                break

        assert len(tokens) <= 3, "Invalid command format, too many arguments!"

        # Обрабатываем метку, если это она
        if len(tokens) == 1 and tokens[0][0] == '.' and tokens[0][len(tokens[0]) - 1] == ':':
            assert tokens[0][0:len(tokens[0]) - 1] not in labels.keys(), "Label already exists!"
            labels[tokens[0][0:len(tokens[0]) - 1]] = line_ctr
            # Смотрим, влияет ли метка на секцию
            data_section = bool(tokens[0] == '.data:')
            continue

        # Обрабатываем объявления переменных и команды
        if data_section:
            assert len(tokens) == 2, "Wrong variable format!"
            assert tokens[0][0] != '%', "Registers cannot be accessed from data section!"
            assert tokens[0] not in variables.keys(), "Variables already exists!"
            variables[tokens[0]] = line_ctr
            instr.append("data")
            # Символьные значения выделяются двойными кавычками
            if len(tokens[1]) == 3 and tokens[1][0] == '\"' and tokens[1][2] == '\"':
                terms.append(Term(line_ctr, ord(tokens[1][1]), 0, AddrMode.LIT.value, 0))
            else:
                terms.append(Term(line_ctr, tokens[1], 0, AddrMode.LIT.value, 0))
        else:
            assert tokens[0] in symbol2opcode.keys(), "Undefined instruction: " + tokens[0] + "!"
            assert len(tokens) - 1 == args_number[tokens[0]], "Invalid number of arguments!"
            instr.append(tokens[0])
            # Заполняем отсутствующие аргументы
            while len(tokens) < 3:
                tokens.append(0)
            # Приводим написание регистров к единому формату
            if tokens[1] in register_symbols.keys():
                tokens[1] = register_symbols[tokens[1]]
            if tokens[2] in register_symbols.keys():
                tokens[2] = register_symbols[tokens[2]]
            assert args_number[tokens[0]] < 2 or \
                   (args_number[tokens[0]] == 2 and
                    (tokens[1] in
                     variables.keys() or
                     tokens[1] in
                     register_symbols.keys())), "First operand of a 2-arg command must be a variable or a register!"
            terms.append(Term(line_ctr, tokens[1], tokens[2], 0, 0))

        line_ctr += 1

    assert '.start' in labels.keys(), "No starting label found!"

    code = []

    # Финальная обработка с раскрытием меток и переменных и указанием типа адресации
    for i in range(len(terms)):
        # Раскрытие для 1 аргумента
        if terms[i].arg1 in labels.keys():
            terms[i] = Term(terms[i].line, labels[terms[i].arg1], terms[i].arg2, AddrMode.PTR, 0)
        elif terms[i].arg1 in variables.keys():
            terms[i] = Term(terms[i].line, variables[terms[i].arg1], terms[i].arg2, AddrMode.PTR, 0)
        elif terms[i].arg1 in register_symbols.keys():
            terms[i] = Term(terms[i].line, registers2indexes[terms[i].arg1], terms[i].arg2, AddrMode.REG, 0)
        else:
            terms[i] = Term(terms[i].line, int(terms[i].arg1), terms[i].arg2, AddrMode.LIT, 0)

        # Раскрытие для 2 аргумента
        if terms[i].arg2 in labels.keys():
            terms[i] = Term(terms[i].line, terms[i].arg1, labels[terms[i].arg2], terms[i].mode1, AddrMode.PTR)
        elif terms[i].arg2 in variables.keys():
            terms[i] = Term(terms[i].line, terms[i].arg1, variables[terms[i].arg2], terms[i].mode1, AddrMode.PTR)
        elif terms[i].arg2 in register_symbols.keys():
            terms[i] = Term(terms[i].line, terms[i].arg1, registers2indexes[terms[i].arg2], terms[i].mode1, AddrMode.REG)
        else:
            terms[i] = Term(terms[i].line, terms[i].arg1, int(terms[i].arg2), terms[i].mode1, AddrMode.LIT)

        code.append({"opcode": symbol2opcode[instr[i]], "term": terms[i]})

    return code


def main(args):
    assert len(args) == 2, "Wrong arguments: translator.py <input_file> <target_file>"
    source, target = args

    with open(source, "rt", encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    print("source LoC:", len(source.split("\n")), "| code instr:", len(code))
    write_code(target, code)


if __name__ == '__main__':
    main(sys.argv[1:])
