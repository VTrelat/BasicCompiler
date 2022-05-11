extern printf
global main
section .data ; global variables

hello :
db 'Hello World!', 0 ; db = data byte ; dw : word 2 octets ; dd : doubleword 4 octets ; dq : quadword 8 octets

section .text ; instructions

mov rsi, 12 ; rsi = 12
mov rdi, hello ; rdi = hello
xor rax, rax ; rax = 0
call printf
ret