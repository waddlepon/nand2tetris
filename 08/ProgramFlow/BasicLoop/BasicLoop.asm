@256
D=A
@SP
M=D
@Sys.initretaddr0
D=A
@SP
A=M
M=D
@SP
M=M+1
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
@THAT
D=M
@SP
A=M
M=D
@SP
M=M+1
@Sys.init
0;JMP
(Sys.initretaddr0)
@0
D=A
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@13
M=D
@0
D=A
@LCL
A=M
A=A+D
D=A
@14
M=D
@13
D=M
@14
A=M
M=D
($LOOP_START)
@0
D=A
@ARG
A=M
A=A+D
D=M
@SP
A=M
M=D
@SP
M=M+1
@0
D=A
@LCL
A=M
A=A+D
D=M
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=D+M
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@13
M=D
@0
D=A
@LCL
A=M
A=A+D
D=A
@14
M=D
@13
D=M
@14
A=M
M=D
@0
D=A
@ARG
A=M
A=A+D
D=M
@SP
A=M
M=D
@SP
M=M+1
@1
D=A
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@SP
M=M-1
A=M
D=M-D
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@13
M=D
@0
D=A
@ARG
A=M
A=A+D
D=A
@14
M=D
@13
D=M
@14
A=M
M=D
@0
D=A
@ARG
A=M
A=A+D
D=M
@SP
A=M
M=D
@SP
M=M+1
@SP
M=M-1
A=M
D=M
@$LOOP_START
D;JNE
@0
D=A
@LCL
A=M
A=A+D
D=M
@SP
A=M
M=D
@SP
M=M+1