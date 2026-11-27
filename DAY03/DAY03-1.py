from pwn import *

context.log_level = 'debug'

p = process('./menu')

p.sendlineafter(b'Choice: ', b'1')
p.sendlineafter(b'Name: ', b'pwntools')

p.sendlineafter(b'Choice: ', b'2')
p.recvuntil(b'Your name: ')
name = p.recvline(keepends=False)

print(f"Saved name: {name!r}")

p.sendlineafter(b'Choice: ', b'3')
print(p.recvline().decode().strip())

p.close()

'''
def choose(p, number) :
    p.sendlineafter(b'Choice: ', str(number).encode())

def set_name(p, name) :
    choose(p, 1)
    p.snedlineafter(b'Name: ', name)

def show_name(p) :
    choose(p, 2)
    p.recvuntil(b'Your name: ')
    return p.recvuntil(keepends=False)

'''