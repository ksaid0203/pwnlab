from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf
context.log_level = 'error'

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

def test_length(length):
    p = process(elf.path)

    try:
        before = recv_value(p, b'BEFORE')

        p.sendafter(b'Input: ', b'A' * length)

        received = recv_value(p, b'READ', 10)
        after = recv_value(p, b'AFTER')

        assert received == length

        p.sendlineafter(b'Inspect: ', b'')
        p.recvall()

        return before, after
    finally:
        p.close()

for length in [8, 15, 16, 17, 20, 24]:
    before, after = test_length(length)
    
    changed = before != after

    print(
        f"Length: {length:2d}   |   "
        f"Marker: {after:#018x} |   "
        f"Changed: {changed}"
    )