from pwn import *

elf = ELF('./chall08',checksec=False)
context.binary = elf

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int (p.recvline().strip(), 16)

p = process(elf.path)

try:
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker = recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    p.recvuntil(b'Input: ')

    marker_raw = p.readmem(marker, 8)
    marker_value = u64(marker_raw)

    print(f"Marker raw: {marker_raw.hex(' ')}")
    print(f"Marker value: {marker_value:#x}")

    # 버퍼 읽기
    buf_raw = p.readmem(buf, 32)
    print(f"Buffer: {buf_raw}")

    # 이전 RBP 읽기
    saved_rbp = u64(p.readmem(rbp, 8))
    print(f"Saved RBP: {saved_rbp:#x}")

    # 반환 주소 읽기
    saved_ret = u64(p.readmem(rbp + 8, 8))
    print(f"Saved RET: {saved_ret:#x}")

    assert marker_value == 0x1122334455667788
    assert saved_ret == ret

    print("All tests passed!")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally :
    p.close()