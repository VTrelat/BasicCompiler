# BasicCompiler

Our language uses a C-like syntax. The compiler is written in Python and uses Lark to parse the input file.
The compiler produces ASM code that needs to be compiled and linked using nasm and gcc (for example).
The compiler works on MacOS and Linux systems. Windows has not been implemented.

## Using the compiler
`./compiler.py [inputFile] [asmOutputFile]` or
`python3 compiler.py [inputFile] [asmOutputFile]`

Compile the generated ASM code:
* Linux : `nasm -f elf64 [asmOutputFile] && gcc -no-pie [asmOutputFile].o -o [executableFile]`
* MacOS : `nasm -f macho64 [asmOutputFile] && gcc -no-pie -fno-pie [asmOutputFile].o -o [executableFile]`

## Functionality

**DISCLAIMER**: There is no check before compiling the code. As long as an expression is valid, it will be compiled. We might implement a checker later, but for now, the programmer is responsible for making sensible code. One could for instance dereference a variable, but the outcome will be undefined.

* functions: One can write and call functions within the code. The function calls use 32bit convention (variables are put on the stack and the function is then called).

* pointers: for now, arithmetic of pointers does not work (the size of what the pointer points to is not detected, but the programmer might still do the maths themselves). However one can get references to variables and dereference pointers (just like in C).
> TODO: arithmetic of pointers.

* typing: basic types are present (char, int) and should be taken into consideration in the generated ASM code. The following types are present:
    * int: 64bit integer
    * char: 8bit integer
