import argparse
import tempfile
import os
from enum import IntEnum
from enum import Enum

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class TokenType(Enum):
    KEYWORD = 0
    SYMBOL = 1
    IDENTIFIER = 2
    INT_CONST = 3
    STRING_CONST = 4

class Kind(IntEnum):
    STATIC = 0
    FIELD = 1
    ARG = 2
    VAR = 3

class JackTokenizer:
    SYMBOLS = ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~']
    KEYWORDS = ['class',
            'constructor',
            'function',
            'method',
            'field',
            'static',
            'var',
            'int',
            'char',
            'boolean',
            'void',
            'true',
            'false',
            'null',
            'this',
            'let',
            'do',
            'if',
            'else',
            'while',
            'return']

    def __init__(self, source_file):
        self.tokens = []
        lines = []
        with open(source_file) as f:
            in_comment = False
            for line in f:
                l = ' '.join(line.split())
                comment_position = l.find("//")
                if comment_position != -1:
                    l = l[0:comment_position]
                if in_comment == False:
                    start_comment_position = l.find("/*")
                    if start_comment_position != -1:
                        in_comment = True
                if in_comment:
                    end_comment_position = l.find("*/")
                    if end_comment_position != -1:
                        l = l[end_comment_position+2:]
                        in_comment = False
                    else:
                        start_comment_position = l.find("/*")
                        if start_comment_position != -1:
                            l = l[0:start_comment_position]
                        else:
                            l = ""
                lines.append(l)
        lines = filter(None, lines)
        self.tokenizeLines('\n'.join(lines))

    def addToken(self, token):
        if token.strip() != "":
            self.tokens.append(token)

    def tokenizeLines(self, lines):
        """
        0 = searching
        1 = in string
        2 = in int
        3 = identifier/keyword
        """
        state = 0
        current_token = ""
        for c in lines:
            if state == 1:
                if c == '"':
                    state = 0
                    self.addToken(current_token + c)
                    current_token = ""
                elif c == '\n':
                    print("Your string has a newline in it")
                    exit()
                else:
                    current_token += c
                continue;
            if c == ' ' or c == '\n':
                state = 0
                self.addToken(current_token)
                current_token = ""
                continue;
            if c in self.SYMBOLS:
                state = 0
                self.addToken(current_token)
                self.addToken(c)
                current_token = ""
                continue;
            if state == 3:
                current_token += c
                continue;
            if c == "\"":
                if state != 0:
                    print("Your int is touching the string")
                    exit()
                state = 1
                self.addToken(current_token)
                current_token = c
                continue;
            if state == 2:
                if not c.isdigit():
                    print("Your int isn't an int")
                    exit()
                current_token += c
                continue;
            if c.isdigit():
                state = 2
                self.addToken(current_token)
                current_token = ""
            state = 3
            current_token += c

    def hasMoreTokens(self):
        return len(self.tokens) > 0

    def advance(self):
        if self.hasMoreTokens():
            self.current_token = self.tokens.pop(0)

    def tokenType(self):
        if self.current_token[0] == '"' and self.current_token[-1] == '"':
            return TokenType.STRING_CONST
        if self.current_token in self.SYMBOLS:
            return TokenType.SYMBOL
        if isInt(self.current_token):
            return TokenType.INT_CONST
        if self.current_token in self.KEYWORDS:
            return TokenType.KEYWORD
        return TokenType.IDENTIFIER

    def keyword(self):
        if self.tokenType() != TokenType.KEYWORD:
            return
        return self.current_token

    def symbol(self):
        if self.tokenType() != TokenType.SYMBOL:
            return
        if self.current_token  == ">":
            return "&gt;"
        elif self.current_token == "<":
            return "&lt;"
        elif self.current_token == "&":
            return "&amp;"

        return self.current_token

    def identifier(self):
        if self.tokenType() != TokenType.IDENTIFIER:
            return
        return self.current_token

    def intVal(self):
        if self.tokenType() != TokenType.INT_CONST:
            return
        return int(self.current_token)

    def stringVal(self):
        if self.tokenType() != TokenType.STRING_CONST:
            return
        t = self.current_token[self.current_token.find('"')+1:]
        return t[:-1]

    def token(self):
        if self.tokenType() == TokenType.KEYWORD:
            return self.keyword()
        elif self.tokenType() == TokenType.SYMBOL:
            return self.symbol()
        elif self.tokenType() == TokenType.IDENTIFIER:
            return self.identifier()
        elif self.tokenType() == TokenType.INT_CONST:
            return self.intVal()
        elif self.tokenType() == TokenType.STRING_CONST:
            return self.stringVal()

    def writeTokens(self, output_file):
        with open(output_file, "w") as f:
            f.write("<tokens>\n")
            while self.hasMoreTokens():
                self.advance()
                token_type = self.tokenType()
                if token_type == TokenType.KEYWORD:
                    f.write("<keyword> " + self.keyword() + " </keyword>\n")
                elif token_type == TokenType.SYMBOL:
                    f.write("<symbol> " + self.symbol() + " </symbol>\n")
                elif token_type == TokenType.IDENTIFIER:
                    f.write("<identifier> " + self.identifier() + " </identifier>\n")
                elif token_type == TokenType.INT_CONST:
                    f.write("<integerConstant> " + str(self.intVal()) + " </integerConstant>\n")
                elif token_type == TokenType.STRING_CONST:
                    f.write("<stringConstant> " + self.stringVal() + " </stringConstant>\n")
            f.write("</tokens>")
        return f

class CompilationEngine:
    OPERATORS = {"+": "add",
            "-": "sub",
            "*": "",
            "/": "",
            "&amp;": "and",
            "|": "or",
            "&lt;": "lt",
            "&gt;": "gt",
            "=": "eq"}

    UNARY_OPERATORS = {"-": "neg", "~": "not"}
    SEGMENTS = ["static", "this", "argument", "local"]

    def __init__(self, tokenizer, vm_writer, symbol_table):
        self.tokenizer = tokenizer
        self.vm_writer = vm_writer
        self.symbol_table = symbol_table
        self.name = ""
        self.loops = 0
        self.ifs = 0
        self.compileClass()

    def next(self):
        self.tokenizer.advance()

    def compileClass(self):
        self.next()
        self.next()
        self.name = self.tokenizer.token()
        self.next()
        self.next()
        
        while self.tokenizer.keyword() == "field" or self.tokenizer.keyword() == "static":
            self.compileClassVarDec()

        while self.tokenizer.keyword() == "function" or self.tokenizer.keyword() == "method" or self.tokenizer.keyword() == "constructor":
            self.compileSubroutine()

        self.vm_writer.close()

    def compileClassVarDec(self):
        category = self.tokenizer.keyword()
        self.next()
        t = self.tokenizer.token()
        self.next()
        kind = 0 
        if category == "static":
            kind = Kind.STATIC
        elif category == "field":
            kind = Kind.FIELD
        self.symbol_table.define(self.tokenizer.identifier(), t, kind)
        self.next()
        while self.tokenizer.symbol() != ";":
            if self.tokenizer.symbol() != ",":
                self.symbol_table.define(self.tokenizer.identifier(), t, kind)
            self.next()
        self.next()

    def compileSubroutine(self):
        function_kind = self.tokenizer.keyword()
        self.next()
        self.next()
        self.symbol_table.startSubroutine()
        function_name = self.name + "." + self.tokenizer.identifier()
        if function_kind == "method":
            self.symbol_table.define("instance", self.name, Kind.ARG)
        self.next()
        self.next()
        self.compileParameterList()
        self.next()
        self.next()
        while self.tokenizer.keyword() == "var":
            self.compileVarDec()

        self.vm_writer.writeFunction(function_name, self.symbol_table.varCount(Kind.VAR))
        if function_kind == "constructor":
            self.vm_writer.writePush("constant", self.symbol_table.varCount(Kind.FIELD))
            self.vm_writer.writeCall("Memory.alloc", 1)
            self.vm_writer.writePop("pointer", 0)
        elif function_kind == "method":
            #pop first argument into this pointer
            self.vm_writer.writePush("argument", 0)
            self.vm_writer.writePop("pointer", 0)
        self.compileStatements()  
        self.next()

    def compileParameterList(self):
        if self.tokenizer.symbol() == ")":
            return;
        t = self.tokenizer.token()
        self.next()
        self.symbol_table.define(self.tokenizer.identifier(), t, Kind.ARG)
        self.next()

        while self.tokenizer.symbol() != ")":
            self.next()
            if self.tokenizer.tokenType() == TokenType.KEYWORD:
                t = self.tokenizer.keyword()
            elif self.tokenizer.tokenType() == TokenType.IDENTIFIER:
                t = self.tokenizer.identifier()
            self.next()
            self.symbol_table.define(self.tokenizer.identifier(), t, Kind.ARG)
            self.next()

    def compileVarDec(self):
        self.next()
        t = self.tokenizer.token()
        self.next()
        self.symbol_table.define(self.tokenizer.identifier(), t, Kind.VAR)
        self.next()
        while self.tokenizer.symbol() != ";":
            if self.tokenizer.symbol() != ",":
                self.symbol_table.define(self.tokenizer.identifier(), t, Kind.VAR)
            self.next()
        self.next()

    def compileStatements(self):
        while self.tokenizer.symbol() != "}":
            if self.tokenizer.keyword() == "do":
                self.compileDo()
            elif self.tokenizer.keyword() == "let":
                self.compileLet()
            elif self.tokenizer.keyword() == "while":
                self.compileWhile()
            elif self.tokenizer.keyword() == "return":
                self.compileReturn()
            elif self.tokenizer.keyword() == "if":
                self.compileIf()

    def compileDo(self):
        self.next()
        self.compileCall("")
        #return value is being ignored
        self.vm_writer.writePop("temp", 0)
        self.next()
        
    def compileLet(self):
        array_assignment = False
        self.next()
        var_name = self.tokenizer.token()
        var_segment = self.SEGMENTS[self.symbol_table.kindOf(var_name)]
        var_index = self.symbol_table.indexOf(var_name)
        self.next()
        if self.tokenizer.symbol() == "[":
            array_assignment = True
            self.next()
            self.compileExpression()
            self.vm_writer.writePush(var_segment, var_index)
            self.vm_writer.writeArithmetic("add")
            self.next()
        self.next()
        self.compileExpression()
        if array_assignment:
            self.vm_writer.writePop("temp", 0)
            self.vm_writer.writePop("pointer", 1)
            self.vm_writer.writePush("temp", 0)
            self.vm_writer.writePop("that", 0)
        else:
            self.vm_writer.writePop(var_segment, var_index)
        self.next()

    def compileWhile(self):
        myloops = self.loops
        self.loops += 1
        self.next()
        self.next()
        self.vm_writer.writeLabel("WHILE_EXP" + str(myloops))
        self.compileExpression()
        self.vm_writer.writeArithmetic("not")
        self.vm_writer.writeIf("WHILE_END" + str(myloops))
        self.next()
        self.next()
        self.compileStatements()
        self.next()
        self.vm_writer.writeGoto("WHILE_EXP" + str(myloops))
        self.vm_writer.writeLabel("WHILE_END" + str(myloops))

    def compileReturn(self):
        self.next()
        if self.tokenizer.symbol() != ";":
            self.compileExpression()
        else:
            self.vm_writer.writePush("constant", 0)
        self.next()
        self.vm_writer.writeReturn()
    
    def compileIf(self):
        myifs = self.ifs
        self.ifs += 1
        else_statement = False
        self.next()
        self.next()
        self.compileExpression()
        self.vm_writer.writeIf("IF_TRUE" + str(myifs))
        self.vm_writer.writeGoto("IF_FALSE" + str(myifs))
        self.vm_writer.writeLabel("IF_TRUE" + str(myifs))
        self.next()
        self.next()
        self.compileStatements()
        self.next()
        if self.tokenizer.keyword() == "else":
            else_statement = True
            self.vm_writer.writeGoto("IF_END" + str(myifs))
            self.vm_writer.writeLabel("IF_FALSE" + str(myifs))
            self.next()
            self.next()
            self.compileStatements()
            self.next()
        if else_statement:
            self.vm_writer.writeLabel("IF_END" + str(myifs))
        else:
            self.vm_writer.writeLabel("IF_FALSE" + str(myifs))

    def compileExpressionList(self):
        args = 0
        if self.tokenizer.symbol() != ")":
            self.compileExpression()
            args += 1
        
        while self.tokenizer.symbol() == ",":
            self.next()
            self.compileExpression()
            args += 1
        
        return args
        
    def compileExpression(self):
        self.compileTerm()
        while self.tokenizer.symbol() in self.OPERATORS:
            operator = self.tokenizer.symbol()
            self.next()
            self.compileTerm()
            if operator == "*":
                self.vm_writer.writeCall("Math.multiply", 2)
            elif operator == "/":
                self.vm_writer.writeCall("Math.divide", 2)
            else:
                self.vm_writer.writeArithmetic(self.OPERATORS[operator])

    def compileTerm(self):
        if self.tokenizer.symbol() == "-" or self.tokenizer.symbol() == "~":
            operator = self.tokenizer.symbol()
            self.next()
            self.compileTerm()
            self.vm_writer.writeArithmetic(self.UNARY_OPERATORS[operator])
        elif self.tokenizer.symbol() == "(":
            self.next()
            self.compileExpression()
            self.next()
        elif self.tokenizer.tokenType() == TokenType.INT_CONST:
            self.vm_writer.writePush("constant", self.tokenizer.intVal())
            self.next()
        elif self.tokenizer.tokenType() == TokenType.STRING_CONST:
            string_const = self.tokenizer.stringVal()
            self.vm_writer.writePush("constant", len(string_const))
            self.vm_writer.writeCall("String.new", 1)
            for c in string_const:
                self.vm_writer.writePush("constant", ord(c))
                self.vm_writer.writeCall("String.appendChar", 2)
            self.next()
        elif self.tokenizer.tokenType() == TokenType.KEYWORD:
            if self.tokenizer.keyword() == "this":
                self.vm_writer.writePush("pointer", 0)
            else:
                self.vm_writer.writePush("constant", 0)
                if self.tokenizer.keyword() == "true":
                    self.vm_writer.writeArithmetic("not")
            self.next()
        else:
            temp = self.tokenizer.token()
            self.next()
            if self.tokenizer.symbol() == "(" or self.tokenizer.symbol() == ".":
                self.compileCall(temp)
            else:
                array_access = False
                var_segment = self.SEGMENTS[self.symbol_table.kindOf(temp)]
                var_index = self.symbol_table.indexOf(temp)
                if self.tokenizer.symbol() == "[":
                    array_access = True
                    self.next()
                    self.compileExpression()
                    self.vm_writer.writePush(var_segment, var_index)
                    self.vm_writer.writeArithmetic("add")
                    self.next()
                if array_access:
                    self.vm_writer.writePop("pointer", 1)
                    self.vm_writer.writePush("that", 0)
                else:
                    self.vm_writer.writePush(var_segment, var_index)

    def compileCall(self, start_buffer):
        temp_buffer = start_buffer
        while self.tokenizer.symbol() != "(":
            temp_buffer += self.tokenizer.token()
            self.next()

        subroutine_name = ""
        before_dot = ""
        func_name = ""
        args = 0
        if "." in temp_buffer:
            before_dot = temp_buffer[0:temp_buffer.find(".")]
            subroutine_name = temp_buffer[(temp_buffer.find(".") + 1):]
            func_name = before_dot + "." + subroutine_name
            if self.symbol_table.inTable(before_dot):
                self.vm_writer.writePush(self.SEGMENTS[self.symbol_table.kindOf(before_dot)], self.symbol_table.indexOf(before_dot))
                func_name = self.symbol_table.typeOf(before_dot) + "." + subroutine_name
                args += 1
        else:
            subroutine_name = temp_buffer
            func_name = self.name + "." + subroutine_name
            self.vm_writer.writePush("pointer", 0)
            args += 1
        self.next()
        args += self.compileExpressionList()
        self.next()

        self.vm_writer.writeCall(func_name, args)

class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.var_counts = [0, 0, 0, 0]

    def startSubroutine(self):
        self.var_counts[int(Kind.VAR)] = 0
        self.var_counts[int(Kind.ARG)] = 0
        self.subroutine_scope.clear()
    
    def define(self, name, t, kind):
        if kind == Kind.STATIC:
            self.class_scope[name] = (t, kind, self.var_counts[kind])
            self.var_counts[kind] += 1
        elif kind == Kind.FIELD:
            self.class_scope[name] = (t, kind, self.var_counts[kind])
            self.var_counts[kind] += 1
        elif kind == Kind.ARG:
            self.subroutine_scope[name] = (t, kind, self.var_counts[kind])
            self.var_counts[kind] += 1
        elif kind == Kind.VAR:
            self.subroutine_scope[name] = (t, kind, self.var_counts[kind])
            self.var_counts[kind] += 1

    def varCount(self, kind):
        return self.var_counts[kind]

    def kindOf(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][1]
        elif name in self.class_scope:
            return self.class_scope[name][1]
        else:
            return None

    def typeOf(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][0]
        elif name in self.class_scope:
            return self.class_scope[name][0]
        else:
            return None

    def indexOf(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][2]
        elif name in self.class_scope:
            return self.class_scope[name][2]
        else:
            return None

    def inTable(self, name):
        return (name in self.subroutine_scope or name in self.class_scope)

class VMWriter:
    def __init__(self, output_file_name):
        self.output_file = open(output_file_name, "w")

    def write(self, line):
        self.output_file.write(line + '\n')

    def writePush(self, segment, index):
        self.write("push " + segment + " " + str(index))

    def writePop(self, segment, index):
        self.write("pop " + segment + " " + str(index))

    def writeArithmetic(self, command):
        self.write(command)

    def writeLabel(self, label):
        self.write("label " + label)

    def writeGoto(self, label):
        self.write("goto " + label)

    def writeIf(self, label):
        self.write("if-goto " + label)

    def writeCall(self, name, nArgs):
        self.write("call " + name + " " + str(nArgs))
    
    def writeFunction(self, name, nLocals):
        self.write("function " + name + " " + str(nLocals))

    def writeReturn(self):
        self.write("return")

    def close(self):
        self.output_file.close()

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("source")
args = arg_parser.parse_args()

output_file = ""

sources = []
if os.path.isdir(args.source):
    sources = [os.path.join(args.source, f) for f in os.listdir(args.source) if os.path.isfile(os.path.join(args.source, f)) and f.endswith('.jack')]
else:
    if args.source.endswith('.jack'):
        sources.append(args.source)
    else:
        print("Wrong File Extension")
        exit()

for s in sources:
    tokenizer = JackTokenizer(s)
    vm_writer = VMWriter(s[0:-5] + ".vm")
    symbol_table = SymbolTable()
    compilation_engine = CompilationEngine(tokenizer, vm_writer, symbol_table)
