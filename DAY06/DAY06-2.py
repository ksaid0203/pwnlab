
from pwn import *

elf = ELF('./chall06', checksec=False)

print("Architecture:", elf.arch)
print("Bits:", elf.bits)
print("Endian:", elf.endian)
print("Entry:", hex(elf.entry))

print(elf.checksec())
