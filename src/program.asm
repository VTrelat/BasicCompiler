extern _printf, _atoi
global _main
default rel
section .data

fmt :
db "%d", 10, 0


section .text

_main:
   push rbp
   mov rbp, rsp
   sub rsp, 40
   push rdi
   push rsi
   mov rax, 1
   mov [rbp-24], rax
   pop rdi
   pop rsi
   add rsp, 40
   mov rax, [rbp-32]
   pop rbp
   ret



