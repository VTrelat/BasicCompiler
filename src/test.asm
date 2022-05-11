extern _printf
global _main
section .data ; global variables

hello :
db 'Hello World!', 0 ; db = data byte ; dw : word 2 octets ; dd : doubleword 4 octets ; dq : quadword 8 octets

section .text ; instructions

_main :
push rsi
mov rsi, 12 ; rsi = 12
mov rdi, hello ; rdi = hello
xor rax, rax ; rax = 0
call _printf
pop rsi
ret