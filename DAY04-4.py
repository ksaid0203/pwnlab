from pwn import *

context.endian = 'little'

leaked = b'\x90\x12\x40\x00\x00\x00'

# parameter of u64 should be 8 bytes
#addr = u64(leaked)
addr = u64(leaked.ljust(8, b'\x00'))

print(hex(addr))
# 0x401290