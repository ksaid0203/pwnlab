
from pwn import *
'''
start() 함수를 만들고 args.REMOTE에 따라 process() 또는 remote()를 반환하기

calculate(p, number) 함수를 만들어 서버에 숫자를 전송하고 결과를 정수로 반환하기

숫자 50을 전송해서 결과 100을 수신하기

assert로 결과가 정확한지 확인하기

로컬과 TCP 모드 모두에서 정상 실행되는지 확인하기
'''


def start():
    # TODO 1: 로컬/원격 선택
    if args.REMOTE :
        return remote("127.0.0.1", 9001)
    #return process("local.py")
    return process(["python3", "-u", "local.py"])

def calculate(p, number):
    # TODO 2: 숫자 전송
    # TODO 3: 결과 수신 및 정수 변환
    p.recvline()
    p.recvuntil(b'Number: ')

    #p.sendline(str(number))
    p.sendline(str(number).encode())

    #p.sendlineafter(b'Number: ', str(number).encode())
    
    p.recvuntil(b'Result: ')
    return int(p.recvline().strip())

p = start()

try:
    result = calculate(p, 50)

    # TODO 4: assert 검증
    assert result == 100

    print(f"Result: {result}")
finally:
    p.close()
  