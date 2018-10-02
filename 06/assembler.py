import argparse
from enum import Enum

class Command_Type(Enum):
    A_COMMAND = 0
    C_COMMAND = 1
    L_COMMAND = 2

class AsmParser:
    def __init__(self, input_file):
        self.commands = []
        with open(input_file) as f:
            for line in f:
                command = ''.join(line.split())
                comment_position = command.find("//")
                if comment_position != -1:
                    command = command[0:comment_position]
                if command != "":
                    self.commands.append(command)

    def hasMoreCommands(self):
        return len(self.commands) > 0

    def advance(self):
        if self.hasMoreCommands():
            self.current_command = self.commands.pop(0)
            if self.current_command[0] == '@':
                self.command_type = Command_Type.A_COMMAND
            elif self.current_command[0] == '(' and self.current_command[len(self.current_command)-1] == ')':
                self.command_type = Command_Type.L_COMMAND
            else:
                self.command_type = Command_Type.C_COMMAND

    def commandType(self):
        return self.command_type

    def symbol(self):
        if self.command_type == Command_Type.L_COMMAND:
            return self.current_command[1:len(self.current_command)-1]
        elif self.command_type == Command_Type.A_COMMAND:
            return self.current_command[1:len(self.current_command)]

    def dest(self):
        if self.command_type == Command_Type.C_COMMAND:
            equals_position = self.current_command.find('=')
            if equals_position != -1:
                return self.current_command[0:equals_position]
            return "null"

    def comp(self):
        if self.command_type == Command_Type.C_COMMAND:
            semi_position = self.current_command.find(';')
            c = self.current_command
            if semi_position != -1:
                c = c[0:semi_position]
            equals_position = c.find('=')
            if equals_position != -1:
                return c[equals_position+1:]
            return c


    def jump(self):
        if self.command_type == Command_Type.C_COMMAND:
            semi_position = self.current_command.find(';')
            if semi_position != -1:
                return self.current_command[semi_position+1:]
            return "null"

class AsmCode:
    def dest(self, code):
        out = list("000")
        if 'M' in code:
            out[2] = '1'
        if 'D' in code:
            out[1] = '1'
        if 'A' in code:
            out[0] = '1'
        return "".join(out)

    def comp(self, code):
        out = ""
        out = out + ('1' if 'M' in code else '0')
        comps = {
                "0": "101010",
                "1": "111111",
                "-1": "111010",
                "D": "001100",
                "A": "110000",
                "M": "110000",
                "!D": "001101",
                "!A": "110001",
                "!M": "110001",
                "-D": "001111",
                "-A": "110011",
                "-M": "110011",
                "D+1": "011111",
                "A+1": "110111",
                "M+1": "110111",
                "D-1": "001110",
                "A-1": "110010",
                "M-1": "110010",
                "D+A": "000010",
                "D+M": "000010",
                "D-A": "010011",
                "D-M": "010011",
                "A-D": "000111",
                "M-D": "000111",
                "D&A": "000000",
                "D&M": "000000",
                "D|A": "010101",
                "D|M": "010101"
                }
        return out + comps[code]

    def jump(self, code):
        jumps = {
                "null": "000",
                "JGT": "001",
                "JEQ": "010",
                "JGE": "011",
                "JLT": "100",
                "JNE": "101",
                "JLE": "110",
                "JMP": "111"
                }
        return jumps[code]

class SymbolTable:
    def __init__(self):
        self.symbols = {
                "SP": 0,
                "LCL": 1,
                "ARG": 2,
                "THIS": 3,
                "THAT": 4,
                "R0": 0,
                "R1": 1,
                "R2": 2,
                "R3": 3,
                "R4": 4,
                "R5": 5,
                "R6": 6,
                "R7": 7,
                "R8": 8,
                "R9": 9,
                "R10": 10,
                "R11": 11,
                "R12": 12,
                "R13": 13,
                "R14": 14,
                "R15": 15,
                "SCREEN": 16384,
                "KBD": 24576
                }

    def addEntry(self, symbol, address):
        self.symbols[symbol] = address

    def contains(self, symbol):
        return symbol in self.symbols 

    def GetAddress(self, symbol):
        return self.symbols[symbol]

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("-o", nargs=1, required=False)
args = parser.parse_args()

try:
    ext = args.file.split('.')[1]
    if ext != "asm":
        raise
except:
    print("Invalid file extension, should be .asm")
    exit()

output_file = ""

if args.o is not None:
    output_file = ''.join(args.o)
else:
    output_file = args.file.split('.')[0] + '.hack'

symbol_table = SymbolTable()
firstpass = AsmParser(args.file)

command_number = 0
while firstpass.hasMoreCommands():
    firstpass.advance()
    if firstpass.commandType() == Command_Type.A_COMMAND or firstpass.commandType() == Command_Type.C_COMMAND:
        command_number += 1
    else:
        symbol_table.addEntry(firstpass.symbol(), command_number)

secondpass = AsmParser(args.file)
asm_code = AsmCode()
variable_number = 16

with open(output_file, "w") as f:
    while secondpass.hasMoreCommands():
        secondpass.advance()
        if secondpass.commandType() == Command_Type.A_COMMAND:
            s = secondpass.symbol()
            if isInt(s):
                f.write('0' + '{0:015b}'.format(int(s)) + '\n')
            elif symbol_table.contains(s):
                f.write('0' + '{0:015b}'.format(symbol_table.GetAddress(s)) + '\n')
            else:
                symbol_table.addEntry(s, variable_number)
                variable_number += 1
                f.write('0' + '{0:015b}'.format(symbol_table.GetAddress(s)) + '\n')
        elif secondpass.commandType() == Command_Type.C_COMMAND:
           out = '111' 
           out += asm_code.comp(secondpass.comp())
           out += asm_code.dest(secondpass.dest())
           out += asm_code.jump(secondpass.jump())
           f.write(out + '\n')
