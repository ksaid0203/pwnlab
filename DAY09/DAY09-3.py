
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

    before_raw = p.readmem(buf_addr, 24)

    print("[ Before Input ]")
    print(hexdump(before_raw))

    p.send(b'A' * 20)

    received = recv_value(p, b'READ', 10)
    after = recv_value(p, b'AFTER')

    p.recvuntil(b'Inspect: ')

    after_raw = p.readmem(buf_addr, 24)

    print("[ After Input ]")
    print(hexdump(after_raw))

    print("[ Changed Bytes ]")

    for i, (old, new) in enumerate(
        zip(before_raw, after_raw)
    ):
        if old != new:
            print(
                f"Offset: {i:02d} | "
                f"Address: {buf_addr + i:#x} | "
                f"{old:02x} -> {new:02x}"
            )

    assert u64(before_raw[16:24]) == before
    assert u64(after_raw[16:24]) == after
    assert received == 20

    p.sendline(b'')
    p.recvall()

finally:
    p.close()
