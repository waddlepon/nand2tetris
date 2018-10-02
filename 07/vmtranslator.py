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
        elif self.current_command[0:2] == "if":
            return CommandType.C_IF
        else:
            return CommandType.C_ARITHMETIC

    def arg1(self):
        if self.commandType() == CommandType.C_RETURN:
            return
        elif self.commandType() == CommandType.C_ARITHMETIC:
            return self.current_command
        return self.current_command.split(' ')[1]

    def arg2(self):
        if self.commandType() == CommandType.C_PUSH or self.commandType() == CommandType.C_POP or self.commandType() == CommandType.C_FUNCTION or self.commandType() == CommandType.C_CALL:
            try:
                return int(self.current_command.split(' ')[2])
            except IndexError:
                return ""

class VMCodeWriter:
    def setFileName(self, file_name, prog_name):
        self.test_jump = 0
        self.output_file = open(file_name, "w")
        self.prog_name = prog_name

    def writeArithmetic(self, command):
        self.output_file.write("@SP\nM=M-1\nA=M\nD=M\n")
        if command != "neg" and command != "not":
            self.output_file.write("@SP\nM=M-1\nA=M\n")
        if command == "add":
            self.output_file.write("D=D+M\n")
        elif command == "sub":
            self.output_file.write("D=M-D\n")            
        elif command == "neg":
            self.output_file.write("D=-D\n")
        elif command == "and":
            self.output_file.write("D=D&M\n")
        elif command == "or":
            self.output_file.write("D=D|M\n")
        elif command == "not":
            self.output_file.write("D=!D\n")
        elif command =="eq" or command == "gt" or command == "lt":
            self.output_file.write("D=M-D\n")
            self.output_file.write("@TRUE" + str(self.test_jump) +"\n")
            if command == "eq":
                self.output_file.write("D;JEQ\n")
            elif command == "gt":
                self.output_file.write("D;JGT\n")
            elif command == "lt":
                self.output_file.write("D;JLT\n")
            self.output_file.write("D=0\n")
            self.output_file.write("@ENDTEST"+ str(self.test_jump) + "\n")
            self.output_file.write("0;JMP\n")
            self.output_file.write("(TRUE" + str(self.test_jump) + ")\n")
            self.output_file.write("D=-1\n")
            self.output_file.write("(ENDTEST" + str(self.test_jump) + ")\n")
            self.test_jump += 1
        self.output_file.write("@SP\nA=M\nM=D\n@SP\nM=M+1\n")

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
                self.output_file.write("@" + str(index + 5) + "\nD=M\n")
            elif segment == "constant":
                self.output_file.write("@" + str(index) + "\nD=A\n")
            elif segment == "pointer":
                if index > 1:
                    print("Error: Push to pointer segment out of bounds")
                    exit()
                self.output_file.write("@" + str(index + 3) + "\nD=M\n")
            elif segment == "static":
                self.output_file.write("@" + self.prog_name + '.' + str(index) + "\nD=M\n")
            else:
                self.output_file.write("@" + str(index) + "\nD=A\n")
                self.output_file.write("@" + s + "\nA=M\nA=A+D\nD=M\n")
            self.output_file.write("@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        elif command == CommandType.C_POP:
            self.output_file.write("@SP\nM=M-1\nA=M\nD=M\n")
            if segment == "temp":
                if index > 7:
                    print("Error: Pop to temp segment out of bounds")
                    exit()
                self.output_file.write("@" + str(index + 5) + "\nM=D\n")
            elif segment == "constant":
                return
            elif segment == "pointer":
                if index > 1:
                    print("Error: Pop to pointer segment out of bounds")
                    exit()
                self.output_file.write("@" + str(index + 3) + "\nM=D\n")
            elif segment == "static":
                self.output_file.write("@" + self.prog_name + '.' + str(index) + "\nM=D\n")
            else:
                self.output_file.write("@13\nM=D\n@" + str(index)  + "\nD=A\n@" + s + "\nA=M\nA=A+D\nD=A\n@14\nM=D\n@13\nD=M\n@14\nA=M\nM=D\n")

    def close(self):
        self.output_file.close()


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("source")
args = arg_parser.parse_args()

sources = []
if os.path.isdir(args.source):
    sources = [os.path.join(args.source, f) for f in os.listdir(args.source) if os.path.isfile(os.path.join(args.source, f)) and f.endswith('.vm')]
else:
    if args.source.endswith('.vm'):
        sources.append(args.source)
    else:
        print("Wrong File Extension")
        exit()

code_writer = VMCodeWriter()
for s in sources:
    parser = VMParser(s)
    code_writer.setFileName(s.split('.')[0] + ".asm", s.split('.')[1])
    while parser.hasMoreCommands():
        parser.advance()
        if parser.commandType() == CommandType.C_ARITHMETIC:
            code_writer.writeArithmetic(parser.arg1()) 
        elif parser.commandType() == CommandType.C_PUSH or parser.commandType() == CommandType.C_POP:
            code_writer.writePushPop(parser.commandType(), parser.arg1(), parser.arg2())

code_writer.close()
