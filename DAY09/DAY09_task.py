
from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall09', checksec=False)
context.binary = elf
context.log_level = 'error'

def recv_value(p, label, base=16):
    # TODO 2
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

'''
def count_changed_bytes(before, after):
    # 변경된 바이트의 개수를 반환
    ret = []
    for i in range(8):
        if before[i] != after[i]:
            ret.append(i)
    return ret
'''
def find_changed_bytes(before, after):
    assert len(before) == len(after)

    ret = []

    for i in range(len(before)):
        if before[i] != after[i]:
            ret.append(i)

    return ret

def analyze(length):
    p = process(elf.path)

    try:
        # TODO 3: Receive addresses
        buf = recv_value(p, b'BUF')
        marker = recv_value(p, b'MARKER')

        # TODO 4: Calculate marker offset
        #print(f"marker - buf: {marker - buf}")
        marker_offset = marker - buf

        print(f"\n[ Length: {length} ]")
        print(f"Marker offset: {marker_offset}")
        
        assert marker_offset == 16
        
        # TODO 5: Read memory before input
        before = recv_value(p, b'BEFORE')
        print(f"before: {before:#x}")
        #print(hexdump(before, 16))
        before_raw = p.readmem(buf, 24)

        print("[ Before ]")
        print(hexdump(before_raw))

        # TODO 6: Send input and receive result
        payload = b'A' * length

        #p.sendline(payload)
        p.send(payload)
        
        received = recv_value(p, b'READ', 10)
        after = recv_value(p, b'AFTER')

        assert received == len(payload)
        
        # TODO 7: Read memory after input
        

        #print(f"after: {after:#x}")
        #print(hexdump(after, 16))
        p.recvuntil(b'Inspect: ')
        after_raw = p.readmem(buf, 24)

        print("[ After ]")
        print(hexdump(after_raw))

        # TODO 8: Compare changed bytes
        #count_changed_bytes(p64(before), p64(after))
        #comp = count_changed_bytes(p64(before), p64(after))
        #print(f"len(comp): {len(comp)}")
        #print(comp)
        changed = find_changed_bytes(
            before_raw,
            after_raw
        )

        for i in changed:
            print(
                f"Offset: {i:02d} | "
                f"Address: {buf + i:#x} | "
                f"{before_raw[i]:02x} -> "
                f"{after_raw[i]:02x}"
            )

        # TODO 9: Check marker corruption
        marker_changed = find_changed_bytes(
            before_raw[marker_offset:marker_offset + 8],
            after_raw[marker_offset:marker_offset + 8]
        )

        corrupted = before != after

        print(f"Total changed: {len(changed)}")
        print(f"Marker changed: {len(marker_changed)}")
        print(f"Marker corrupted: {corrupted}")

        assert u64(before_raw[16:24]) == before
        assert u64(after_raw[16:24]) == after
        # TODO 10: Finish process
        
        #p.sendlineafter(b'Inspect: ', b'')
        p.sendline(b'')
        p.recvall()

    finally:
        p.close()

for length in [8, 16, 17, 20, 24]:
    analyze(length)
