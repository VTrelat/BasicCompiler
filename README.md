- [About this project](#about-this-project)
- [Our language](#our-language)
- [Simple compiler](#simple-compiler)
  - [Formatting](#formatting)
  - [Using the compiler](#using-the-compiler)
  - [Functionality](#functionality)

---

# About this project

This project was carried out as part of a 2nd year advanced compilation course at the Ecole des Mines de Nancy.

# Our language

Our language is a simplified version of C with fewer commands. It is strongly and statically typed and the user can choose among a large variety of types (`int` and `char`). Some commands may vary, such as `printf` (`putOnScreen`), `return` (`giveMeBack`) and `scanf` (`getMeVar`).

Single line comments `//` and multiline comments `(*` `*)` are supported.

Pointers and multi-pointers are supported with and declared with the `*` operator just like in C, one may also dereference their variable with the `&` operator.

> Arithmetic of pointers does not work though.

# Simple compiler

Our language uses a C-like syntax. The compiler is written in Python and uses Lark to parse the input file.
The compiler produces ASM code that needs to be compiled and linked using nasm and gcc (for example).
The compiler works on MacOS and Linux systems. Windows has not been implemented.

## Formatting

An input file can be prettified with respect to the Lark grammar with the function `prettify` defined in `compiler.py`. When compiling a file, it is automatically formatted.

## Using the compiler

-   Compiling and formatting

    -   compile : `./compiler.py [inputFile] -o [asmOutputFile]` or
        `python3 compiler.py [inputFile] [asmOutputFile]`
    -   help : `./compiler.py -h` or `python3 compiler.py -h`
    -   format input file : `./compiler.py [inputFile] -p` or `python3 compiler.py [inputFile] -p`

-   Compile the generated ASM code:

    -   Linux : `nasm -f elf64 [asmOutputFile] && gcc -no-pie [asmOutputFile].o -o [executableFile]`
    -   MacOS : `nasm -f macho64 [asmOutputFile] && gcc -no-pie -fno-pie [asmOutputFile].o -o [executableFile]`

## Functionality

> **DISCLAIMER**: There is no check before compiling the code. As long as an expression is valid, it will be compiled. We might implement a checker later, but for now, the programmer is responsible for making sensible code. One could for instance dereference a variable, but the outcome will be undefined.

-   functions: One can write and call functions within the code. The function calls use 32bit convention (variables are put on the stack and the function is then called).

-   pointers: for now, arithmetic of pointers does not work (the size of what the pointer points to is not detected, but the programmer might still do the maths themselves). However one can get references to variables and dereference pointers (just like in C).

    > TODO: arithmetic of pointers.

-   typing: basic types are present (char, int) and should be taken into consideration in the generated ASM code. The following types are present:
    -   int: 64bit integer
    -   char: 8bit integer
