extern _printf, _atoi
global _main
default rel
section .data

fmt :
db "%d", 10, 0
VAR_DECL

section .text
_main :
   push rbp
   mov rbp, rsp
   push rdi
   push rsi

VAR_INIT
BODY
RETURN
   
   mov rdi, fmt
   mov rsi, rax
   xor rax, rax
   call _printf
   add rsp, 16
   pop rbp
   ret
