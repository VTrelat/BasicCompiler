extern _printf
global _main
section .data 
    x: dq 0
    y: dq 0 
section .text 
_main: 
    mov rax, [x] 
    mov [z], rax
if_0:
    mov rax, [y] 
    push rax
    mov rax, [x] 
    pop rbx
    pop rax
    cmp rax, rbx
    sete al
    movzb rax, al
    push rax
    cmp rax, 0
    je endif_0
    mov rax, 1 
    mov [z], rax
    jmp endif_0
    mov rax, 0 
    mov [z], rax
endif_0
 
return: 
    mov rax, [z] 
    ret