
from pwn import *

context.endian = 'little'

addr = 0x401234

packed32 = p32(addr)
packed64 = p64(addr)

print("p32:", packed32.hex(' '))
print("p64:", packed64.hex(' '))

print("p32 length:", len(packed32))
print("p64 length:", len(packed64))
