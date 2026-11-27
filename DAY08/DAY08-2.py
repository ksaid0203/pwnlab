
from pwn import *

elf = ELF('./chall08', checksec=False)

context.binary = elf

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int (p.recvline().strip(), 16) # b'0x~~~' -> hexa int

p = process(elf.path)

try:
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker =  recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    p.recvuntil(b'Input: ')

    print(f"RBP: {rbp:#x}")
    print(f"BUF: {buf:#x}")
    print(f"MARKER: {marker:#x}")
    print(f"RET: {ret:#x}")

    print(f"RBP - BUF: {rbp - buf:#x}")
    print(f"RBP - MARKER: {rbp - marker:#x}")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()