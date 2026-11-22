from pwn import *

context.endian = 'little'

print(p32(0x12345678))
# b'\x78\x56\x34\x12'

print(hex(u32(b'\x78\x56\x34\x12')))
# 0x12345678