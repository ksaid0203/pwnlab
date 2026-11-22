from pwn import *

value = 0x12345678

little = p32(value, endian='little')
big = p32(value, endian='big')

print("little:", little.hex(' '))
print("big:   ", big.hex(' '))

assert u32(little, endian='little') == value
assert u32(big, endian='big') == value