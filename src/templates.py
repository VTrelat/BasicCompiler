LINUX_TEMPLATE = """extern printf, atoi, __isoc99_scanf
global main
default rel
section .data

fmt :
   db "%d", 10, 0
read :
   db "%d", 0
VAR_DECL

section .text

FUN_DECL"""

DARWIN_TEMPLATE = """extern _printf, _atoi, __isoc99_scanf
global _main
default rel
section .data

fmt :
   db "%d", 10, 0
read :
   db "%d", 0
VAR_DECL

section .text

FUN_DECL"""
