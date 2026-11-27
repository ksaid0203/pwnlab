from pwn import *

context.endian = 'little'

leaked = b'\x90\x12\x40\x00\x00\x00\x00\x00'

addr = u64(leaked)

print(hex(addr))
# 0x401290