
from pwn import *

context.log_level = 'debug'

p = process('./chall02')

p.sendlineafter(b'MENU> ', b'hello')

data1 = p.recvn(4)
data2 = p.recvn(4)
data3 = p.recvline()
data4 = p.recvline()


print(f"data1:{repr(data1)}")
print(f"data2:{repr(data2)}")
print(f"data3:{repr(data3)}")
print(f"data4:{repr(data4)}")

p.close()

