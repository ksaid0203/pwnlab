
from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf
context.log_level = 'error'

got_addr = elf.got['puts']

# ELF 파일에 저장된 데이터
file_raw = elf.read(got_addr, 8)
file_value = u64(file_raw)

p = process(elf.path)

try:
    # puts() 호출 이후까지 대기
    p.recvuntil(b'Input: ')

    # 실행 중인 로컬 프로세스의 메모리
    runtime_raw = p.readmem(got_addr, 8)
    runtime_value = u64(runtime_raw)

    print(f"GOT address:    {got_addr:#x}")
    print(f"File value:     {file_value:#x}")
    print(f"Runtime value:  {runtime_value:#x}")

    print(f"File bytes:     {file_raw.hex(' ')}")
    print(f"Runtime bytes:  {runtime_raw.hex(' ')}")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()
