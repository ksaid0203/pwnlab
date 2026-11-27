
from pwn import *

elf = ELF('./chall06', checksec=False)

for name in ['.text', '.rodata', '.data', '.bss']:
    section = elf.get_section_by_name(name)

    if section is None:
        continue

    addr = section.header.sh_addr
    size = section.header.sh_size

    print(f"{name:10} addr={addr:#x}, size={size:#x}")