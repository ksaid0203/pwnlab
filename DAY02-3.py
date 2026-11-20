from pwn import *

p = process('./chall02')
p.sendlineafter(b'MENU> ', b'test')

print(f'first: {p.recvn(3)}')
print(f'second: {p.recvuntil(b'\n').strip()}')
print(f'third: {p.recvline().strip()}')

p.close()