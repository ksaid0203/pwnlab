#client.py
from pwn import *

context.log_level = 'debug'

p = remote('127.0.0.1', 9001)

p.sendlineafter(b'Number: ', b'21')

p.recvuntil(b'Result: ')
result = int(p.recvline().strip())

print(f"Result = {result}")

assert result == 42

p.close()
