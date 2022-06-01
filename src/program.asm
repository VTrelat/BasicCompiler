extern _printf, _atoi
global _main
default rel
section .data

fmt :
db "%d", 10, 0
main : dq 0
x : dq 0
f1 : dq 0
a : dq 0
f2 : dq 0
b : dq 0
p : dq 0
z : dq 0

section .text

_f1:
   push rbp
   mov rbp, rsp
   push rdi
   push rsi

   FUNCTION BODY HERE

   pop rdi
   pop rsi
   add rsp, 16
   pop rbp
   ret

_f2:
   push rbp
   mov rbp, rsp
   push rdi
   push rsi

   FUNCTION BODY HERE

   pop rdi
   pop rsi
   add rsp, 16
   pop rbp
   ret

_main:
   push rbp
   mov rbp, rsp
   push rdi
   push rsi

   FUNCTION BODY HERE

   pop rdi
   pop rsi
   add rsp, 16
   pop rbp
   ret


