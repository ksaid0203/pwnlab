# chatgpt response

# pwntools Day 5 — process()와 remote() 실전 입출력

(1주 차 · 5/20회) 2026년 11월 23일 (월)

Day 4에서는 `p32()`, `p64()`, `u32()`, `u64()`를 이용해 정수와 바이트를 변환했고, `int`, `str`, `bytes`의 차이도 정확하게 이해했어.

오늘은 1주 차 마지막 수업이야. **로컬 프로그램을 실행하는 `process()`와 TCP 서버에 연결하는 `remote()`를 비교하고, 하나의 pwntools 스크립트로 두 환경을 모두 처리하는 방법**을 배울 거야.

**오늘의 학습 목표 — 총 60분**

이론: 로컬과 원격 연결 **15분**

실습: TCP 서버 자동화 **35분**

정리: 종합 과제 **10분**

## 1. 이론 — process() vs remote() (15분)

```python
from pwn import *

# 로컬 실행
p = process('./chall')

# TCP 서버 연결
p = remote('127.0.0.1', 9001)
```

두 객체는 연결 방식이 다르지만, 데이터를 주고받는 인터페이스는 거의 동일해.

| 항목 | `process()` | `remote()` |
|--------|--------|--------|
| 연결 대상 | 로컬 실행 파일 | TCP 서버 |
| 인자 | 실행 파일 경로 | 호스트, 포트 |
| 데이터 전송 | `send()`, `sendline()` | 동일 |
| 데이터 수신 | `recv()`, `recvuntil()` | 동일 |
| 종료 | `close()` | `close()` |

```svg
<svg viewBox="0 0 330 166" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="51" width="108" height="62" rx="9" fill="#64748b" fill-opacity=".12" stroke="#64748b" stroke-opacity=".5" /><text x="60" y="77" font-size="12" fill="currentColor" font-weight="600" text-anchor="middle">pwntools</text><text x="60" y="94" font-size="10" fill="currentColor" text-anchor="middle">Python 스크립트</text><rect x="213" y="7" width="111" height="58" rx="9" fill="#2563eb" fill-opacity=".10" stroke="#2563eb" stroke-opacity=".5" /><text x="268" y="30" font-size="12" fill="currentColor" font-weight="600" text-anchor="middle">로컬 프로그램</text><text x="268" y="47" font-size="11" fill="currentColor" text-anchor="middle">process()</text><rect x="213" y="101" width="111" height="58" rx="9" fill="#16a34a" fill-opacity=".10" stroke="#16a34a" stroke-opacity=".5" /><text x="268" y="124" font-size="12" fill="currentColor" font-weight="600" text-anchor="middle">TCP 서버</text><text x="268" y="141" font-size="11" fill="currentColor" text-anchor="middle">remote()</text><path d="M114 71L213 36 M114 94L213 130" fill="none" stroke="currentColor" stroke-opacity=".65" stroke-width="1.5" /><g fill="currentColor"><path d="M213 36l-9 -1 3 8z" /><path d="M213 130l-9 -7 -2 9z" /></g><text x="163" y="45" font-size="10" fill="currentColor" text-anchor="middle">로컬</text><text x="163" y="125" font-size="10" fill="currentColor" text-anchor="middle">TCP</text></svg>
```

연결 대상만 바꾸고 송수신 코드는 재사용할 수 있어.

실제 CTF에서는 로컬에서 익스플로잇을 검증한 다음, `process()`를 `remote()`로 변경해 문제 서버에 연결하는 경우가 많아. 다만 로컬과 원격의 라이브러리나 실행 환경이 다르면 익스플로잇 자체도 수정해야 할 수 있어.

## 2. 실습 — 로컬 TCP 서버 만들기 (35분)

오늘은 외부 서버가 아니라 **직접 만든 localhost 서버**를 대상으로 연습할 거야.

### Step 1. 서버 코드 작성

`server.py` 파일을 만들어 아래 코드를 저장해.

```python

import socketserver

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"Welcome!\n")
        self.wfile.write(b"Number: ")
        self.wfile.flush()

        data = self.rfile.readline()
        if not data:
            return

        try:
            number = int(data.strip())
        except ValueError:
            self.wfile.write(b"Invalid number\n")
            return

        self.wfile.write(
            f"Result: {number * 2}\n".encode()
        )
        self.wfile.flush()

class Server(socketserver.TCPServer):
    allow_reuse_address = True

with Server(("127.0.0.1", 9001), Handler) as server:
    print("Listening on 127.0.0.1:9001", flush=True)
    server.serve_forever()
```

첫 번째 터미널에서 실행해.

```bash
python3 server.py
```

서버는 `127.0.0.1:9001`에서 연결을 기다려. `127.0.0.1`은 자기 컴퓨터를 의미하는 루프백 주소야.

### Step 2. remote()로 서버 연결

두 번째 터미널에서 `client.py`를 작성해.

```python

from pwn import *

context.log_level = 'debug'

p = remote('127.0.0.1', 9001)

p.sendlineafter(b'Number: ', b'21')

p.recvuntil(b'Result: ')
result = int(p.recvline().strip())

print(f"Result = {result}")

assert result == 42

p.close()
```

실행\:

```bash
python3 client.py
```

예상 결과\:

```text
Result = 42
```

실제 출력에는 pwntools 디버그 로그도 함께 표시돼.

여기서 `int(p.recvline().strip())`은 수신한 ASCII 숫자 `b'42'`를 정수 `42`로 바꾸는 거야. Day 4의 `u64()`처럼 바이너리 주소를 복원하는 것과는 다르다는 점을 기억해.

### Step 3. 로컬과 원격에서 같은 코드 사용하기

이번에는 `client.py`를 수정해서 연결 대상을 실행 인자로 선택해 보자.

```python

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
```

로컬 프로그램으로 사용할 `local.py`도 작성해.

```python
print("Welcome!")
number = int(input("Number: "))
print(f"Result: {number * 2}")
```

로컬 실행\:

```bash
python3 client.py
```

원격 실행 (서버 실행 상태에서)\:

```bash
python3 client.py REMOTE
```

`args.REMOTE`는 pwntools가 명령행 인자 `REMOTE`의 존재 여부를 확인해 주는 기능이야.

`python3 -u`는 Python의 표준 출력 버퍼링을 줄여서 프롬프트를 즉시 받을 수 있도록 해.

## 3. 직접 풀 실습 과제

**Day 5 과제 — 로컬/원격 자동화 완성**

오늘은 다음 조건을 모두 만족하는 `day5_task.py`를 직접 작성해 봐.

1. `start()` 함수를 만들고 `args.REMOTE`에 따라 `process()` 또는 `remote()`를 반환하기
2. `calculate(p, number)` 함수를 만들어 서버에 숫자를 전송하고 결과를 정수로 반환하기
3. 숫자 `50`을 전송해서 결과 `100`을 수신하기
4. `assert`로 결과가 정확한지 확인하기
5. 로컬과 TCP 모드 모두에서 정상 실행되는지 확인하기

---

**시작 코드**

```python

from pwn import *

def start():
    # TODO 1: 로컬/원격 선택
    pass

def calculate(p, number):
    # TODO 2: 숫자 전송
    # TODO 3: 결과 수신 및 정수 변환
    pass

p = start()

try:
    result = calculate(p, 50)

    # TODO 4: assert 검증
    print(f"Result: {result}")
finally:
    p.close()
```

힌트: `str(number).encode()`와 `recvuntil(b'Result: ')`을 활용해 봐. 현재 서버는 연결당 숫자 하나만 처리하므로 각 테스트는 새 연결을 사용해야 해.

## 4. 정리 — 이해도 확인 (10분)

**Day 5 확인 퀴즈** /3 응답

## 1주 차 진도

**입출력과 바이트 처리** 5 / 20회

전체 계획 25% · Day 5 실습 진행 단계

오늘 과제의 핵심은 **입출력 로직은 그대로 유지하고 연결 방식만 바꿀 수 있도록 코드를 구성하는 것**이야.

다음 Day 6부터는 바이너리 분석 단계로 넘어가서 `ELF()`로 실행 파일의 심볼, 함수 주소, 섹션 정보를 확인하는 방법을 학습할 거야.

---