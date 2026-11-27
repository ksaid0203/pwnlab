
from pwn import *

elf = ELF('./chall08', checksec=False)

context.binary = elf


func = elf.functions['inspect_stack']

print(f"Function address: {func.address:#x}")
print(f"Function size: {func.size}")

print(elf.disasm(func.address, func.size))