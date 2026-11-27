
from pwn import *

p = process('./chall09_safe')

try:
    p.recvuntil(b'BEFORE: ')
    before = int(p.recvline().strip(), 16)

    p.sendafter(b'Input: ', b'A' * 24)

    p.recvuntil(b'READ: ')
    received = int(p.recvline().strip())

    p.recvuntil(b'AFTER: ')
    after = int(p.recvline().strip(), 16)

    print(f"Read length: {received}")
    print(f"Before: {before:#018x}")
    print(f"After:  {after:#018x}")

    assert received <= 16
    assert before == after

    print("Buffer boundary verified!")

    p.recvall()

finally:
    p.close()
