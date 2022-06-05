# BasicCompiler

Our language uses a C-like syntax. The compiler is written in python and using Lark to parse the input.
The compiler produces ASM code, that needs to be compiled and linked using nasm and gcc (for example).
The compiler works on macs and linux systems. Windows has not been implemented.

## Using the compiler
`./compiler.py [inputFile] [asmOutputFile]` or
`python3 compiler.py [inputFile] [asmOutputFile]`

compiling the generated ASM code: `nasm -f elf64 [asmOutputFile] && gcc -no-pie [asmOutputFile].o -o [executableFile]`


## Functionality

DISCLAIMER: There is no check before compiling the code. As long as an expression is valid, it will be compiled. We might implement a checker later, but for now, the programmer is responsible for making sensible code.

functions: You can write and call functions within the code. The function calls use 32bit convention (we put the variables on the stack and then call the function)

pointers: for now pointer arithmetics doesn't work (we are not detecting the size of what the pointer points to, but you can always do the maths yourself).
However you can get dereference variables and follow pointers (just like in C)
> TODO: pointer arithmetics

typing: basic types are present (char, int) and should be taken into consideration in the generated ASM code.
