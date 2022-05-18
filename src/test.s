	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 11, 0	sdk_version 12, 1
	.intel_syntax noprefix
	.globl	_main                           ## -- Begin function main
	.p2align	4, 0x90
_main:                                  ## @main
## %bb.0:
	push	rbp
	mov	rbp, rsp
	mov	dword ptr [rbp - 4], 0
	mov	dword ptr [rbp - 8], 3
	mov	dword ptr [rbp - 12], 0
	cmp	dword ptr [rbp - 8], 1
	jle	LBB0_2
## %bb.1:
	mov	eax, dword ptr [rbp - 8]
	mov	dword ptr [rbp - 12], eax
	jmp	LBB0_3
LBB0_2:
	mov	dword ptr [rbp - 12], 1
LBB0_3:
	mov	eax, dword ptr [rbp - 12]
	pop	rbp
	ret
                                        ## -- End function
.subsections_via_symbols
