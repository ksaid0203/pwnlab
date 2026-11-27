from pwn import *

elf = ELF('./chall06', checksec=False)

main_addr = elf.symbols['main']
hello_addr = elf.symbols['hello']
secret_addr = elf.symbols['secret']
global_addr = elf.symbols['global_value']

print(f"main:         {main_addr:#x}")
print(f"hello:        {hello_addr:#x}")
print(f"secret:       {secret_addr:#x}")
print(f"global_value: {global_addr:#x}")

assert main_addr != hello_addr
assert hello_addr != secret_addr


packed = p64(secret_addr)

print("Address:", hex(secret_addr))
print("Packed:", packed.hex(' '))

assert u64(packed) == secret_addr