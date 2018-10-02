import argparse
import tempfile
import os
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
    OPERATORS = ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "=",]

    def __init__(self, tokenizer, output_file_name):
        self.output_file = open(output_file_name, "w")
        self.tokenizer = tokenizer
        self.indentation = 0
        self.compileClass()
        self.output_file.close()

    def write(self, line):
        self.output_file.write("  "*self.indentation + line + '\n')

    def indent(self):
        self.indentation += 1

    def unindent(self):
        if self.indentation != 0:
            self.indentation -= 1

    def write_token(self):
        token_type = self.tokenizer.tokenType()
        if token_type == TokenType.KEYWORD:
            self.write("<keyword> " + self.tokenizer.keyword() + " </keyword>")
        elif token_type == TokenType.IDENTIFIER:
            self.write("<identifier> " + self.tokenizer.identifier() + " </identifier>")
        elif token_type == TokenType.SYMBOL:
            self.write("<symbol> " + self.tokenizer.symbol() + " </symbol>")
        elif token_type == TokenType.INT_CONST:
            self.write("<integerConstant> " + str(self.tokenizer.intVal()) + " </integerConstant>")
        elif token_type == TokenType.STRING_CONST:
            self.write("<stringConstant> " + self.tokenizer.stringVal() + " </stringConstant>")

    def next(self):
        self.tokenizer.advance()

    def compileClass(self):
        self.write("<class>")
        self.indent()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        
        while self.tokenizer.keyword() == "field" or self.tokenizer.keyword() == "static":
            self.compileClassVarDec()

        while self.tokenizer.keyword() == "function" or self.tokenizer.keyword() == "method" or self.tokenizer.keyword() == "constructor":
            self.compileSubroutine()

        self.write_token()
        self.unindent()
        self.write("</class>")

    def compileClassVarDec(self):
        self.write("<classVarDec>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        while self.tokenizer.symbol() != ";":
            self.write_token()
            self.next()
        self.write_token()
        self.next()
        self.unindent()
        self.write("</classVarDec>")

    def compileSubroutine(self):
        self.write("<subroutineDec>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.compileParameterList()
        self.write_token()
        self.next()
        self.write("<subroutineBody>")
        self.indent()
        self.write_token()
        self.next()
        while self.tokenizer.keyword() == "var":
            self.compileVarDec()
        self.compileStatements()  
        self.write_token()
        self.next()
        self.unindent()
        self.write("</subroutineBody>")
        self.unindent()
        self.write("</subroutineDec>")

    def compileParameterList(self):
        self.write("<parameterList>")
        self.indent()
        if self.tokenizer.symbol() == ")":
            self.unindent()
            self.write("</parameterList>")
            return;
        else:
            self.write_token()
            self.next()
            self.write_token()
            self.next()

        while self.tokenizer.symbol() != ")":
            self.write_token()
            self.next()
            self.write_token()
            self.next()
            self.write_token()
            self.next()

        self.unindent()
        self.write("</parameterList>")

    def compileVarDec(self):
        self.write("<varDec>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        while self.tokenizer.symbol() != ";":
            self.write_token()
            self.next()
        self.write_token()
        self.next()
        self.unindent()
        self.write("</varDec>")

    def compileStatements(self):
        self.write("<statements>")
        self.indent()
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
        self.unindent()
        self.write("</statements>")

    def compileDo(self):
        self.write("<doStatement>")
        self.indent()
        self.write_token()
        self.next()

        while self.tokenizer.symbol() != "(":
            self.write_token()
            self.next()

        self.write_token()
        self.next()
        self.compileExpressionList()
        self.write_token()
        self.next()

        self.write_token()
        self.next()
        self.unindent()
        self.write("</doStatement>")

    def compileLet(self):
        self.write("<letStatement>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        if self.tokenizer.symbol() == "[":
            self.write_token()
            self.next()
            self.compileExpression()
            self.write_token()
            self.next()
        self.write_token()
        self.next()
        self.compileExpression()
        self.write_token()
        self.next()
        self.unindent()
        self.write("</letStatement>")

    def compileWhile(self):
        self.write("<whileStatement>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.compileExpression()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.compileStatements()
        self.write_token()
        self.next()
        self.unindent()
        self.write("</whileStatement>")

    def compileReturn(self):
        self.write("<returnStatement>")
        self.indent()
        self.write_token()
        self.next()
        if self.tokenizer.symbol() != ";":
            self.compileExpression()
        self.write_token()
        self.next()
        self.unindent()
        self.write("</returnStatement>")
    
    def compileIf(self):
        self.write("<ifStatement>")
        self.indent()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.compileExpression()
        self.write_token()
        self.next()
        self.write_token()
        self.next()
        self.compileStatements()
        self.write_token()
        self.next()
        if self.tokenizer.keyword() == "else":
            self.write_token()
            self.next()
            self.write_token()
            self.next()
            self.compileStatements()
            self.write_token()
            self.next()
        self.unindent()
        self.write("</ifStatement>")

    def compileExpressionList(self):
        self.write("<expressionList>")
        self.indent()

        if self.tokenizer.symbol() != ")":
            self.compileExpression()
        
        while self.tokenizer.symbol() == ",":
            self.write_token()
            self.next()
            self.compileExpression()
        self.unindent()
        self.write("</expressionList>")
        
    def compileExpression(self):
        self.write("<expression>")
        self.indent()
        self.compileTerm()
        while self.tokenizer.symbol() in self.OPERATORS:
            self.write_token()
            self.next()
            self.compileTerm()
        self.unindent()
        self.write("</expression>")

    def compileTerm(self):
        self.write("<term>")
        self.indent()

        if self.tokenizer.symbol() == "-" or self.tokenizer.symbol() == "~":
            self.write_token()
            self.next()
            self.compileTerm()
        elif self.tokenizer.symbol() == "(":
            self.write_token()
            self.next()
            self.compileExpression()
            self.write_token()
            self.next()
        else:
            self.write_token()
            self.next()
            if self.tokenizer.symbol() == "(":
                self.write_token()
                self.next()
                self.compileExpressionList()
                self.write_token()
                self.next()
            elif self.tokenizer.symbol() == ".":
                self.write_token()
                self.next()
                self.write_token()
                self.next()
                self.write_token()
                self.next()
                self.compileExpressionList()
                self.write_token()
                self.next()
            elif self.tokenizer.symbol() == "[":
                self.write_token()
                self.next()
                self.compileExpression()
                self.write_token()
                self.next()
        self.unindent()
        self.write("</term>")

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
    compilation_engine = CompilationEngine(tokenizer, s[:-5] + "C.xml")
