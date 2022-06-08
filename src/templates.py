LINUX_TEMPLATE = """extern printf, atoi, scanf
global main
default rel
section .data

fmt :
   db "%ld", 10, 0
read :
   db "%ld", 0
VAR_DECL

section .text

FUN_DECL"""

DARWIN_TEMPLATE = """extern _printf, _atoi, _scanf
global _main
default rel
section .data

fmt :
   db "%ld", 10, 0
read :
   db "%ld", 0
VAR_DECL

section .text

FUN_DECL"""
