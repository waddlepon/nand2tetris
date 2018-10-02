// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
(RESET)
@SCREEN
D=A
@pixel
M=D

@8192
D=A+D
@maxpixels
M=D

(CHECK)
@KBD
D=M
@BLACK
D;JNE
@WHITE
0;JMP

(BLACK)
@color
M=-1
@WRITE
0;JMP

(WHITE)
@color
M=0
@WRITE
0;JMP

(WRITE)
@color
D=M
@pixel
A=M
M=D
@pixel
M=M+1
D=M
@maxpixels
D=M-D
@RESET
D;JLE
@CHECK
0;JMP
