from pwn import *

elf = ELF('./chall06', checksec=False)

# 문자열 검색
string_addr = next(
    elf.search(b'Hello, pwntools!\x00')
)

print(f"String address: {string_addr:#x}")

# 문자열 데이터 읽기
data = elf.read(string_addr, 17)

print("String:", data)

# 전역 변수 읽기
global_addr = elf.symbols['global_value']
raw = elf.read(global_addr, 4)

print("Raw bytes:", raw.hex(' '))
print("Integer:", u32(raw))

assert u32(raw) == 1234
