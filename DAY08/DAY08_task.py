
from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall08', checksec=False)
context.binary = elf

# TODO 2: Disassemble inspect_stack

#disasm = elf.disasm(elf.symbols['inspect_stack'], 0x100)
func = elf.symbols['inspect_stack']

print(f"Function address: {func.address:#x}")
print(f"Function size: {func.size:#x}")

print("[ Disassembly of inspect_stack ]")
disasm = elf.disasm(func.address, func.size)
print(disasm)

def recv_addr(p, label):
    # TODO: Receive hexadecimal address
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), 16)

p = process('./chall08')

try:
    # TODO 3: Receive stack addresses
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker = recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    print(f"RBP: {rbp:#x}")
    print(f"BUF: {buf:#x}")
    print(f"MARKER: {marker:#x}")
    print(f"RET: {ret:#x}")

    # TODO 4: Synchronize process
    p.recvuntil(b'Input: ')

    # TODO 5: Read and verify marker
    
    # marker_addr 에 byte 데이터 저장됨
    #marker_addr = p.readmem(marker, 8)
    #marker_value = u64(marker_addr)

    marker_addr = marker
    marker_raw = p.readmem(marker_addr, 8)
    marker_value = u64(marker_raw)

    print(f"marker_value: {marker_value:#x}")

    assert marker_value == 0x1122334455667788

    # TODO 6: Read saved RBP and RET
    saved_rbp = u64(p.readmem(rbp, 8))
    return_addr = u64(p.readmem(rbp + 8, 8))

    print(f"Saved RBP: {saved_rbp:#x}")
    print(f"Return Address: {return_addr:#x}")

    # TODO 7: Verify return address
    assert return_addr == ret

    # TODO 8: Dump stack memory
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



    # TODO 9: Send input and receive result
    p.sendline(b'hello')
    print(p.recvall().decode())

    print("Analysis complete!")
    

finally:
    p.close()
