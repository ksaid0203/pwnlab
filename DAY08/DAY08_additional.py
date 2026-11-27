from pwn import *

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int (p.recvline().strip(), 16)

elf = ELF('./chall08', checksec=False)
context.binary = elf

for i in range(3):
    # 프로세스 실행
    p = process('./chall08')

    # RBP 주소 수신
    rbp = recv_addr(p, b'RBP')

    # BUF 주소 수신
    buf = recv_addr(p, b'BUF')
    # RET 주소 수신
    ret = recv_addr(p, b'RET')

    # 주소 및 상대 거리 출력
    print(f'RBP: {rbp:016x}')
    print(f'BUF: {buf:016x}')
    print(f'RET: {ret:016x}')

    print(f"BUF - RBP: {buf - rbp}")

    print(f"inspect_stack: {elf.symbols['inspect_stack']:#x}")
    
    runtime_base = p.libs()[elf.path]

    inspect_addr = (
        runtime_base
        + elf.symbols['inspect_stack']
        - elf.address
    )
    print(f"inspect_stack: {inspect_addr:#x}")

    # 프로세스 종료
    p.close()