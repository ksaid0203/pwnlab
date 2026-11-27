from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

p = process(elf.path)

try:
    p.recvuntil(b'RBP: ')
    rbp = int(p.recvline().strip(), 16)

    p.recvuntil(b'Input: ')

    print("[ Stack Dump ]")

    for offset in range(-0x40, 0x18, 8):
        addr = rbp + offset

        raw = p.readmem(addr, 8)
        value = u64(raw)

        label = ""

        if offset == 0:
            label = "<-- Saved RBP"
        elif offset == 8:
            label = "<-- Return Address"

        print(
            f"{addr:#018x} "
            f"RBP{offset:+#06x} "
            f"{value:#018x} "
            f"{label}"
        )

    raw = p.readmem(rbp - 0x40, 0x50)
    print(hexdump(raw))
    
    p.sendline(b'hello')
    p.recvall()

finally:
    p.close()