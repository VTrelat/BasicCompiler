extern _printf, _atoi
global _main
default rel
section .data

fmt :
db "%d", 10, 0
y : dq 0
x : dq 0

section .text
_main :
   push rbp
   mov rbp, rsp
   push rdi
   push rsi

   mov rbx, [rbp-0x10]
   mov rdi, [rbx+8]
   call _atoi
   mov [x], rax
   mov rbx, [rbp-0x10]
   mov rdi, [rbx+16]
   call _atoi
   mov [y], rax

while0 :
   mov rax, 5
   push rax
   mov rax, [x]
   pop rbx
   sub rax, rbx

   cmp rax, 0
   jz endwhile0
   mov rax, [y]
   mov rdi, fmt
   mov rsi, rax
   xor rax, rax
   call _printf
   mov rax, 1
   push rax
   mov rax, [x]
   pop rbx
   sub rax, rbx

   mov [x], rax
   jmp while0
endwhile0 :

   mov rax, [y]
   
   mov rdi, fmt
   mov rsi, rax
   xor rax, rax
   call _printf
   add rsp, 16
   pop rbp
   ret
