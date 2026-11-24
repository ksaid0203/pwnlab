
from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall06', checksec=False)

print(f"elf.arch: {elf.arch}")
print(f"elf.bits: {elf.bits}")
print(f"elf.endian: {elf.endian}")

# TODO 2: Find function addresses

print(f"main addr: {elf.symbols['main']:#x}")
print(f"hello addr: {elf.symbols['hello']:#x}")
print(f"secret addr: {elf.symbols['secret']:#x}")

# TODO 3: Pack and unpack secret address
sec = p64(elf.symbols['secret'])
assert u64(sec) == elf.symbols['secret']

# TODO 4: Search and read string
target = b'Secret function!'
search_addr = next(elf.search(target))
print(f"search_addr: {search_addr:#x}")
print(f"read(search_addr, len(target)): {elf.read(search_addr, len(target))}")

# TODO 5: Read global_value
global_addr = elf.symbols['global_value']
global_value = elf.read(global_addr, 4)
print(f"{global_value}")
print(f"{u32(global_value)}")

# TODO 6: Check main address range
section = elf.get_section_by_name('.text')
addr = section.header.sh_addr
size = section.header.sh_size
assert addr <= elf.symbols['main'] < addr + size

print("All tests passed!")
