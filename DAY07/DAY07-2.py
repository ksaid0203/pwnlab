
from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf

puts_plt = elf.plt['puts']
puts_got = elf.got['puts']

print(f"puts PLT: {puts_plt:#x}")
print(f"puts GOT: {puts_got:#x}")

print("\n[PLT disassembly]")
print(elf.disasm(puts_plt, 16))

print("\n[GOT raw data]")
raw = elf.read(puts_got, 8)

print(raw)
print(raw.hex(' '))
print(f"Stored address: {u64(raw):#x}")
