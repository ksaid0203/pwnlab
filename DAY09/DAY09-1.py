from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

p = process(elf.path)

try:
    buf_addr = recv_value(p, b'BUF')
    marker_addr = recv_value(p, b'MARKER')
    before = recv_value(p, b'BEFORE')

    p.recvuntil(b'Input: ')

    print(f"BUF:    {buf_addr:#x}")
    print(f"MARKER: {marker_addr:#x}")
    print(f"Offset: {marker_addr - buf_addr}")

    payload = b'A' * 16

    p.send(payload)

    received = recv_value(p, b'READ', 10)
    after = recv_value(p, b'AFTER')

    print(f"Input length: {len(payload)}")
    print(f"Read length: {received}")
    print(f"Before: {before:#018x}")
    print(f"After: {after:#018x}")

    assert received == len(payload)
    assert before == after

    p.sendlineafter(b'Inspect: ', b'')
    p.recvall()
    
finally:
    p.close()