
from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf

functions = ['puts', 'printf', 'read', 'write']

for name in functions:
    print(f"\nFunction: {name}")
    print(f"PLT: {elf.plt[name]:#x}")
    print(f"GOT: {elf.got[name]:#x}")

print(f"\n\nsymbols: {elf.symbols['puts']:#x}")
print(f"plt:     {elf.plt['puts']:#x}")
print(f"got:     {elf.got['puts']:#x}")

print(f"elf.symbols['puts'] == elf.plt['puts']: {elf.symbols['puts'] == elf.plt['puts']}")
print(f"elf.plt['puts'] == elf.got['puts']: {elf.plt['puts'] == elf.got['puts']}")