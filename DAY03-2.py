from pwn import *

def choose(p, number) :
    p.sendlineafter(b'Choice: ', str(number).encode())

def set_name(p, name) :
    choose(p, 1)
    p.sendlineafter(b'Name: ', name)

def show_name(p) :
    choose(p, 2)
    p.recvuntil(b'Your name: ')
    return p.recvline(keepends=False)

context.log_level = 'debug'

p = process('./menu')

set_name(p, b'AAAA')
print(show_name(p))

set_name(p, b'BBBB')
print(show_name(p))

choose(p, 3)
p.close()
