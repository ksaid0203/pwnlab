from pwn import *

elf = ELF('./chall')

print(hex(elf.symbols['main']))
print(hex(elf.symbols['hello']))

