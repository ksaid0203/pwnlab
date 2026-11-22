from pwn import *

context.endian = 'little'

value32 = 0xdeadbeef
value64 = 0x401234

raw32 = b'\xef\xbe\xad\xde'
leak6 = b'\x80\x45\x23\x01\x00\x00'

#TODO 1 : value32 to 4bytes
TODO1 = p32(value32)

#TODO 2 : value64 to 8bytes
TODO2 = p64(value64)

#TODO 3 : raw32 to int
TODO3 = u32(raw32)

#TODO 4 : leak6 to 8bytes with padding
TODO4 = u64(leak6.ljust(8, b'\x00'))

#TODO 5 : assert
assert TODO1 == b'\xef\xbe\xad\xde'
assert TODO2 == b'\x34\x12\x40' + b'\x00' * 5
assert TODO3 == 0xdeadbeef, f"TODO3: {TODO3:#x}"
assert TODO4 == 0x1234580, f"TODO4: {TODO4:#x}"