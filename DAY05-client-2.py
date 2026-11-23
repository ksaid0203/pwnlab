#client-2.py
from pwn import *

context.log_level = 'info'

def start():
    if args.REMOTE:
        return remote('127.0.0.1', 9001)
    return process(['python3', '-u', 'local.py'])

def solve(p):
    p.sendlineafter(b'Number: ', b'21')
    p.recvuntil(b'Result: ')

    result = int(p.recvline().strip())
    assert result == 42

    log.success(f"Result: {result}")

p = start()

try:
    solve(p)
finally:
    p.close()
