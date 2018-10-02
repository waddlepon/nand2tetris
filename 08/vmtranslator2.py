import argparse
import os
from enum import Enum

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class CommandType(Enum):
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2
    C_LABEL = 3
    C_GOTO = 4
    C_IF = 5
    C_FUNCTION = 6
    C_RETURN = 7
    C_CALL = 8

class VMParser:
    def __init__(self, source_file):
        self.commands = []
        with open(source_file) as f:
            for line in f:
                command = ' '.join(line.split())
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

    def commandType(self):
        if self.current_command[0:8] == "function":
            return CommandType.C_FUNCTION
        elif self.current_command[0:6] == "return":
            return CommandType.C_RETURN
        elif self.current_command[0:5] == "label":
            return CommandType.C_LABEL
        elif self.current_command[0:4] == "push":
            return CommandType.C_PUSH
        elif self.current_command[0:4] == "goto":
            return CommandType.C_GOTO
        elif self.current_command[0:4] == "call":
            return CommandType.C_CALL
        elif self.current_command[0:3] == "pop":
            return CommandType.C_POP
        elif self.current_command[0:7] == "if-goto":
            return CommandType.C_IF
        else:
            return CommandType.C_ARITHMETIC

    def arg1(self):
        if self.commandType() == CommandType.C_RETURN:
            return
        elif self.commandType() == CommandType.C_ARITHMETIC:
            return self.current_command.strip()
        return self.current_command.split(' ')[1]

    def arg2(self):
        if self.commandType() == CommandType.C_PUSH or self.commandType() == CommandType.C_POP or self.commandType() == CommandType.C_FUNCTION or self.commandType() == CommandType.C_CALL:
            try:
                return int(self.current_command.split(' ')[2])
            except IndexError:
                return ""

class VMCodeWriter:
    def __init__(self, file_name, bootstrap):
        self.test_jump = 0
        self.ret_addr = 0
        self.output_file = open(file_name, "w")
        self.function_name = ""
        if bootstrap:
            self.writeInit()

    def setProgName(self, prog_name):
        self.prog_name = prog_name

    def write(self, command):
        self.output_file.write(command + '\n')

    def writeInit(self):
        self.write("@256")
        self.write("D=A")
        self.write("@SP")
        self.write("M=D")
        self.writeCall("Sys.init", 0)

    def writeLabel(self, label):
        if label[0].isdigit():
            print("Error: Label begins with digit")
            exit()
        self.write("(" + self.function_name + "$" + label + ")")
    
    def writeGoto(self, label):
        self.write("@" + self.function_name + "$" + label)
        self.write("0;JMP")

    def writeIf(self, label):
        self.writePopD()
        self.write("@" + self.function_name + "$" + label)
        self.write("D;JNE")

    def writeCall(self, functionName, numArgs):
        self.write("@retaddr" + str(self.ret_addr))
        self.write("D=A")
        self.writePushD()
        for s in ["@LCL", "@ARG", "@THIS", "@THAT"]:
            self.write(s)
            self.write("D=M")
            self.writePushD()
        self.write("@SP")
        self.write("D=M")
        self.write("@LCL")
        self.write("M=D")
        self.write("@" + str(numArgs + 5))
        self.write("D=D-A")
        self.write("@ARG")
        self.write("M=D")
        self.write("@" + functionName)
        self.write("0;JMP")
        self.write("(retaddr" + str(self.ret_addr) + ")")
        self.ret_addr += 1

    def writeReturn(self):
        #R13 = FRAME, R14 = RET
        self.write("@LCL")
        self.write("D=M")
        self.write("@R13")
        self.write("M=D")
        self.write("@R13")
        self.write("D=M")
        self.write("@5")
        self.write("A=D-A")
        self.write("D=M")
        self.write("@R14")
        self.write("M=D")
        self.writePopD()
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")
        self.write("@ARG")
        self.write("D=M")
        self.write("@SP")
        self.write("M=D+1")
        for i, s in enumerate(["@THAT", "@THIS", "@ARG", "@LCL"], start = 1):
            self.write("@R13")
            self.write("D=M")
            self.write("@" + str(i))
            self.write("A=D-A")
            self.write("D=M")
            self.write(s)
            self.write("M=D")
        self.write("@R14")
        self.write("A=M")
        self.write("0;JMP")
 
    def writeFunction(self, functionName, numLocals):
        self.function_name = functionName
        self.write("(" + functionName + ")")
        for i in range(0, numLocals):
            self.write("D=0")
            self.writePushD()

    def writeArithmetic(self, command):
        self.writePopD()
        if command != "neg" and command != "not":
            self.write("@SP")
            self.write("M=M-1")
            self.write("A=M")
        if command == "add":
            self.write("D=D+M")
        elif command == "sub":
            self.write("D=M-D")            
        elif command == "neg":
            self.write("D=-D")
        elif command == "and":
            self.write("D=D&M")
        elif command == "or":
            self.write("D=D|M")
        elif command == "not":
            self.write("D=!D")
        elif command =="eq" or command == "gt" or command == "lt":
            self.write("D=M-D")
            self.write("@TRUE" + str(self.test_jump))
            if command == "eq":
                self.write("D;JEQ")
            elif command == "gt":
                self.write("D;JGT")
            elif command == "lt":
                self.write("D;JLT")
            self.write("D=0")
            self.write("@ENDTEST"+ str(self.test_jump))
            self.write("0;JMP")
            self.write("(TRUE" + str(self.test_jump) + ")")
            self.write("D=-1")
            self.write("(ENDTEST" + str(self.test_jump) + ")")
            self.test_jump += 1
        self.writePushD()

    def writePushD(self):
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")
        self.write("@SP")
        self.write("M=M+1")

    def writePopD(self):
        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")

    def writePushPop(self, command, segment, index):
        segments = {
                "local": "LCL",
                "argument": "ARG",
                "this": "THIS",
                "that": "THAT",
                "temp": "temp",
                "constant": "constant",
                "pointer": "pointer",
                "static": "static",
                }
        s = segments[segment]
        if command == CommandType.C_PUSH:
            if segment == "temp":
                if index > 7:
                    print("Error: Push to temp segment out of bounds")
                    exit()
                self.write("@" + str(index + 5))
                self.write("D=M")
            elif segment == "constant":
                self.write("@" + str(index))
                self.write("D=A")
            elif segment == "pointer":
                if index > 1:
                    print("Error: Push to pointer segment out of bounds")
                    exit()
                self.write("@" + str(index + 3))
                self.write("D=M")
            elif segment == "static":
                self.write("@" + self.prog_name + '.' + str(index))
                self.write("D=M")
            else:
                self.write("@" + s)
                self.write("D=M")
                self.write("@" + str(index))
                self.write("A=A+D")
                self.write("D=M")
            self.writePushD()
        elif command == CommandType.C_POP:
            if segment == "temp":
                if index > 7:
                    print("Error: Pop to temp segment out of bounds")
                    exit()
                self.writePopD()
                self.write("@" + str(index + 5))
                self.write("M=D")
            elif segment == "constant":
                return
            elif segment == "pointer":
                if index > 1:
                    print("Error: Pop to pointer segment out of bounds")
                    exit()
                self.writePopD()
                self.write("@" + str(index + 3))
                self.write("M=D")
            elif segment == "static":
                self.writePopD()
                self.write("@" + self.prog_name + '.' + str(index))
                self.write("M=D")
            else:
                self.write("@" + s)
                self.write("D=M")
                self.write("@" + str(index))
                self.write("A=D+A")
                self.write("D=A")
                self.write("@R15")
                self.write("M=D")
                self.writePopD()
                self.write("@R15")
                self.write("A=M")
                self.write("M=D")
                
    def close(self):
        self.output_file.close()


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("source")
args = arg_parser.parse_args()

output_file = ""

sources = []
if os.path.isdir(args.source):
    sources = [os.path.join(args.source, f) for f in os.listdir(args.source) if os.path.isfile(os.path.join(args.source, f)) and f.endswith('.vm')]
    output_file = args.source
    if not args.source.endswith('/'):
        output_file += '/'
    output_file = args.source
    output_file += output_file.split('/')[-2] + ".asm"
else:
    if args.source.endswith('.vm'):
        sources.append(args.source)
        output_file = args.source[0:-3] + ".asm"
    else:
        print("Wrong File Extension")
        exit()

code_writer = VMCodeWriter(output_file, len(sources) > 1)
for s in sources:
    parser = VMParser(s)
    if "/" in s:
        code_writer.setProgName(s.split('/')[-1][0:-3])
    else:
        code_writer.setProgName(s[0:-3])
    while parser.hasMoreCommands():
        parser.advance()
        code_writer.write("//" + parser.current_command)
        if parser.commandType() == CommandType.C_ARITHMETIC:
            code_writer.writeArithmetic(parser.arg1()) 
        elif parser.commandType() == CommandType.C_PUSH or parser.commandType() == CommandType.C_POP:
            code_writer.writePushPop(parser.commandType(), parser.arg1(), parser.arg2())
        elif parser.commandType() == CommandType.C_LABEL:
            code_writer.writeLabel(parser.arg1())
        elif parser.commandType() == CommandType.C_GOTO:
            code_writer.writeGoto(parser.arg1())
        elif parser.commandType() == CommandType.C_IF:
            code_writer.writeIf(parser.arg1())
        elif parser.commandType() == CommandType.C_FUNCTION:
            code_writer.writeFunction(parser.arg1(), parser.arg2())
        elif parser.commandType() == CommandType.C_RETURN:
            code_writer.writeReturn()
        elif parser.commandType() == CommandType.C_CALL:
            code_writer.writeCall(parser.arg1(), parser.arg2())

code_writer.close()
