all: fib pointers pointers_magic types

run: all
	./fib
	@echo
	@echo
	./pointers
	@echo
	@echo
	./pointers_magic

fib: fib.opale
	../src/compiler.py fib.opale -o fib.asm
	nasm -f elf64 fib.asm
	gcc -no-pie -fno-pie fib.o -o fib

pointers: pointers.opale
	../src/compiler.py pointers.opale -o  pointers.asm
	nasm -f elf64 pointers.asm
	gcc -no-pie -fno-pie pointers.o -o pointers

pointers_magic: pointers_magic.opale
	../src/compiler.py pointers_magic.opale -o pointers_magic.asm
	nasm -f elf64 pointers_magic.asm
	gcc -no-pie -fno-pie pointers_magic.o -o pointers_magic

types: types.opale
	../src/compiler.py types.opale -o types.asm
	nasm -f elf64 types.asm
	gcc -no-pie -fno-pie types.o -o types
