
from pwn import *

context.log_level = 'debug'

p = process('./chall02')

p.recvuntil(b'MENU> ')
p.sendline(b'test')

result = p.recvuntil(b'\n')
print(repr(result))

remaining = p.recvall()
print(repr(remaining))

p.close()

