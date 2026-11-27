from pwn import *

# 로컬 실행
p = process('./chall')

# TCP 서버 연결
p = remote('127.0.0.1', 9001)