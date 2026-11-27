
from pwn import *

# TODO 1: Load ELF

elf = ELF('./chall07', checksec=False)
context.binary = elf

functions = ['puts', 'printf', 'read', 'write']

# TODO 2: Print GOT and PLT addresses

for name in functions:
    print(f"elf.plt[{name}]: {elf.plt[name]:#x}")
    print(f"elf.got[{name}]: {elf.got[name]:#x}")

# TODO 3: Assert GOT != PLT

assert elf.plt['puts'] != elf.got['puts']

# TODO 4: Disassemble puts@plt

puts_plt = elf.plt['puts']
print(f"{elf.disasm(puts_plt, 16)}")

# TODO 5: Read GOT data from ELF file
puts_got = elf.got['puts']
print(f"GOT Data from ELF: {u64(elf.read(puts_got, 8)):#x}")

# TODO 6: Read GOT data from running process
p = process("./chall07")

p.recvuntil(b'Input: ')

runtime_raw = p.readmem(puts_got, 8)
runtime_value = u64(runtime_raw)

print(f"GOT Data from RUNTIME: {u64(p.readmem(puts_got, 8)):#x}")



# TODO 7: Compare file and runtime values

print(f"{elf.read(puts_got, 8) == p.readmem(puts_got, 8)}")

print("Analysis complete!")

# Additional Challenge

for name in functions :
    got_addr = elf.got[name]
    got_raw = p.readmem(got_addr, 8)
    got_value = u64(got_raw)

    print(f"{name}'s got_addr:{got_addr:#x}")
    print(f"{name}'s got_raw:{got_raw}")
    print(f"{name}'s got_value:{got_value:#x}")


p.close()