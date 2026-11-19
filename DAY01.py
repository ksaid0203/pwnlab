from pwn import *

context.log_level = 'debug'
p = process("./chall")

#p.sendlineafter(b'Name: ', b'pwntools')
p.recvuntil(b'Name: ')
p.sendline(b'/bin/sh\x00')

result = p.recvline()
print(result)

p.close()