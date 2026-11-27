## Day 1 — pwntools 시작하기

오늘의 학습 · 60분

**목표\:** pwntools로 로컬 프로그램을 실행하고 데이터를 주고받을 수 있다.

### 1. 이론 (15분)

pwntools의 기본 입출력 함수 세 가지를 기억해.

- `process()` — 로컬 프로그램 실행
- `sendline()` — 데이터와 개행 문자 전송
- `recvline()` — 개행 문자까지 한 줄 수신

### 2. 코드 실습 (35분)

먼저 `pip install pwntools`로 설치하고, 아래 C 프로그램을 만들어 봐.

```c
// chall.c
#include <stdio.h>

int main(void) {
    char name[64];

    printf("Name: ");
    fflush(stdout);

    fgets(name, sizeof(name), stdin);
    printf("Hello, %s", name);
    return 0;
}
```

컴파일\:

```bash
gcc -o chall chall.c
```

pwntools 코드\:

```python
from pwn import *

p = process('./chall')

p.sendlineafter(b'Name: ', b'pwntools')

result = p.recvline()
print(result)

p.close()
```

예상 출력\:

```text
b'Hello, pwntools\n'
```

여기서 `sendlineafter()`는 `Name: `이라는 문자열이 출력될 때까지 기다렸다가 데이터를 전송하는 함수야.

### 3. 오늘의 실습 과제 (10분)

위 코드를 다음과 같이 수정해 봐.

1. `sendlineafter()`를 `recvuntil()`과 `sendline()`으로 나누어 작성하기.
2. `b'pwntools'` 대신 `b'/bin/sh\x00'` 전송하기.
3. `context.log_level = 'debug'`를 추가해 실제 송수신 바이트 확인하기.

**완료 기준\:** 프로그램이 정상 종료되고 `\x00`이 포함된 데이터가 전송되는 것을 디버그 로그에서 확인하면 성공이야.

내일 Day 2에서는 `send()`와 `sendline()`의 차이, `recvuntil()`을 더 자세히 다룰 거야.

---

# you asked

message time: 2026-11-19 20:28:09

from pwn import *

context.log_level = 'debug'
p = process("./chall")

#p.sendlineafter(b'Name: ', b'pwntools')
p.recvuntil(b'Name: ')
p.sendline(b'/bin/sh\x00')

result = p.recvline()
print(result)

p.close()

코드를 작성했으니 검토해줘.

---

# chatgpt response

잘 작성했어\! **Day 1 실습 과제의 핵심 요구사항 3가지를 모두 충족했어.** 특히 `sendlineafter()`를 `recvuntil()`과 `sendline()`으로 분리한 부분이 정확해.

## 코드 리뷰

**Day 1 실습 평가** (통과)

### 1. 작성한 코드 분석

```python
from pwn import *

context.log_level = 'debug'
p = process("./chall")

p.recvuntil(b'Name: ')
p.sendline(b'/bin/sh\x00')

result = p.recvline()
print(result)

p.close()
```

| 코드 | 동작 |
|--------|--------|
| `context.log_level = 'debug'` | 송수신 데이터의 HEX 덤프 출력 |
| `process("./chall")` | 로컬 바이너리 실행 |
| `recvuntil(b'Name: ')` | 입력 프롬프트까지 수신 |
| `sendline(b'/bin/sh\x00')` | 9바이트 전송 |
| `recvline()` | 개행 문자까지 출력 수신 |
| `close()` | 프로세스 연결 종료 |

### 2. 주의할 점: Null Byte와 Newline

네 코드에서 가장 중요한 부분이야.

```python
p.sendline(b'/bin/sh\x00')
```

실제로 전송되는 데이터는 다음과 같아.

전송 바이트 구조

총 9바이트: `/bin/sh` 7바이트 + `\x00` 1바이트 + `\x0a` 1바이트

`sendline()`이 마지막에 `\x0a`를 추가하기 때문이야.

현재 C 프로그램은 `fgets()`를 사용하므로 개행 문자가 들어오는 것이 자연스러워.

### 3. 예상 실행 결과

이전에 작성한 `chall.c`를 그대로 사용했다면 대략 다음과 같은 로그가 나올 거야.

```text
[DEBUG] Received 0x6 bytes:
    b'Name: '
[DEBUG] Sent 0x9 bytes:
    00000000  2f 62 69 6e 2f 73 68 00  0a
    00000009
[DEBUG] Received 0x13 bytes:
    00000000  48 65 6c 6c 6f 2c 20 2f  62 69 6e 2f 73 68 00 0a
    00000010
```

여기서 중요한 점은 C의 `printf("Hello, %s", name)`이 `\x00`에서 문자열 출력을 멈춘다는 거야.

따라서 `recvline()`이 돌려주는 데이터는 다음과 같을 가능성이 높아.

```python
b'Hello, /bin/sh'
```

이후 프로그램이 종료되기 때문에, 개행 문자가 없더라도 EOF까지 받은 데이터를 반환할 수 있어. pwntools 버전에 따라 EOF 경고가 출력될 수도 있어.

## 4. 추가로 개선하면 좋은 부분

현재 코드는 잘 동작하지만, `recvline()` 결과를 더 명확하게 확인하려면 `repr()`을 사용해 보는 걸 추천해.

```python
from pwn import *

context.log_level = 'debug'

p = process('./chall')

p.recvuntil(b'Name: ')
p.sendline(b'/bin/sh\x00')

result = p.recvall()
print(repr(result))

p.close()
```

이 예시에서는 `recvall()`을 사용했어. 프로그램이 종료될 때까지 남은 출력을 모두 수신하기 때문에, 개행이 없는 출력도 확인하기 편해.

---

## Day 1 추가 도전 과제

여기서 한 단계 더 나아가 보자.

**질문\:** 다음 코드로 변경하면 어떤 문제가 발생할까?

```python
p.recvuntil(b'Name: ')
p.send(b'/bin/sh\x00')
result = p.recvline()
```

힌트: C 프로그램은 `fgets()`를 사용하고 있어.

`send()`와 `sendline()`의 차이를 정확히 이해했는지 확인하기 좋은 문제야.

참고로 지금까지 작성한 코드만으로는 Day 1의 학습 목표를 충분히 달성했어. 다음에는 `recv()` 계열 함수들의 차이를 이해하면 좋아.

---

# you asked

message time: 2026-11-19 20:35:39

send()는 개행을 보내지 않고, sendline은 개행을 끝에 보내. send의 경우 \x00에서 입력이 끝나기 때문에 마지막 바이트가 제대로 전달되지 않을 거같아.

---

# chatgpt response

거의 정확하게 이해했어\! 👍 다만 **한 가지 중요한 오해**가 있어.

`send()`가 `\x00`을 만나면 입력이 끝난다는 부분은 잘못된 생각이야.

## 1. 핵심 개념

**`\x00`은 문자열의 끝을 나타내지만, 데이터 전송의 끝을 의미하지는 않아.**

| 구분 | `\x00` $NULL) | `\x0a` \(Newline) |
|--------|--------|--------|
| HEX 값 | `0x00` | `0x0a` |
| C 문자열 | 문자열 종료 표시 | 일반 문자 |
| `send()` | 그대로 전송 | 그대로 전송 |
| `fgets()` | 입력에 포함 가능 | 입력 종료 조건 |
| `read()` | 일반 바이트 | 일반 바이트 |

예를 들어\:

```python
p.send(b'AAA\x00BBB')
```

실제로 전송되는 데이터는 다음과 같아.

```text
41 41 41 00 42 42 42
```

**7바이트 모두 전송돼.** `\x00` 이후의 `BBB`도 정상적으로 전달되는 거야.

## 2. 그렇다면 왜 send()에서 문제가 발생할까?

우리가 작성한 C 코드를 다시 보자.

```c
char name[64];
fgets(name, sizeof(name), stdin);
```

`fgets()`는 일반적으로 다음 조건 중 하나를 만족할 때 반환해.

1. 개행 문자(`\n`$를 읽었을 때
2. 최대 `sizeof(name) - 1`바이트를 읽었을 때
3. EOF를 만났을 때

따라서 Python에서 다음과 같이 전송하면\:

```python
p.send(b'/bin/sh\x00')
```

8바이트는 정상적으로 전달되지만, `fgets()`는 아직 개행 문자를 받지 않았으므로 추가 입력을 기다릴 수 있어.

이 상태에서\:

```python
result = p.recvline()
```

을 호출하면 Python도 C 프로그램의 출력을 기다리게 돼.

**입출력 대기 상태**

**Python (pwntools)** (recvline() 대기)

8바이트 전송 완료

---

**C 프로그램** (fgets() 대기)

양쪽이 서로 다음 동작을 기다리기 때문에 진행되지 않는 상황이 발생할 수 있어.

## 3. 직접 확인하는 실습

아래 코드를 실행해 봐.

```python
from pwn import *

context.log_level = 'debug'

p = process('./chall')

p.recvuntil(b'Name: ')

p.send(b'/bin/sh\x00')

# 1초 동안 출력을 기다림
result = p.recv(timeout=1)

print(f'Received: {result!r}')

# 개행 문자를 추가로 전송
p.send(b'\n')

result = p.recvall()
print(f'Received after newline: {result!r}')

p.close()
```

첫 번째 `recv()`에서는 일반적으로 `b''`가 반환되고, 개행 문자를 보낸 후에는 다음과 같은 출력이 나올 거야.

```text
Received: b''
Received after newline: b'Hello, /bin/sh'
```

이 실습에서 기억해야 할 내용은 세 가지야.

- `send()`는 `\x00`을 포함한 모든 바이트를 그대로 전송한다.
- `fgets()`는 `\x00`이 아니라 개행 문자 등을 기준으로 입력을 끝낸다.
- `printf("%s", ...)`는 `\x00`을 만나면 문자열 출력을 멈춘다.

---

### 이해도 확인 문제

이번에는 다음 C 코드라고 가정해 보자.

```c
char buf[16];
read(0, buf, 8);
```

Python에서 아래와 같이 전송하면\:

```python
p.send(b'AAA\x00BBB\x00')
```

**질문\:** `read()`는 몇 바이트를 읽을까? 그리고 `buf`에는 어떤 데이터가 저장될까?

이 문제까지 이해하면 `send()`와 C의 입력 함수 사이의 관계를 확실히 잡을 수 있어.

---

# you asked

message time: 2026-11-19 20:38:27

read의 3번째 파라미터는 읽을 바이트 갯수를 의미하므로 8byte, buf에는 'AAA\x00BBB\x00'가 저장될거야.

---

# chatgpt response

정답이야\! 🎯 **핵심 개념을 정확히 이해했어.**

다만 `read()`에 대해 한 가지 더 알아두면 좋은 부분이 있어.

## 1. 코드 분석

```c
char buf[16];
read(0, buf, 8);
```

```python
p.send(b'AAA\x00BBB\x00')
```

전송 데이터는 다음과 같아.

**buf에 저장되는 8바이트** (8 bytes)

`read()`는 `\x00`을 특별하게 취급하지 않으므로 모든 바이트를 읽을 수 있어.

## 2. 중요한 차이점

`read(0, buf, 8)`의 세 번째 인자인 `8`은 **정확히 8바이트를 읽는다는 의미가 아니라, 최대 8바이트를 읽겠다는 의미**야.

따라서 실제 반환값은 상황에 따라 달라질 수 있어.

```c
ssize_t n = read(0, buf, 8);
printf("Read: %zd bytes\n", n);
```

일반적인 로컬 실습에서는 8바이트를 모두 읽을 가능성이 높지만, `read()`는 8바이트보다 적게 읽고 반환할 수도 있어.

## 3. Day 1 최종 평가

**Day 1 — pwntools 기초** (학습 완료)

`process()`로 프로그램 실행

`send()`와 `sendline()` 차이 이해

`recvuntil()` 사용

NULL 바이트와 개행 문자 구분

`read()`와 `fgets()`의 차이 이해

**오늘의 핵심\:** pwntools는 바이트를 전송하고, C의 입력 함수는 각자의 규칙에 따라 그 바이트를 읽어.

다음 Day 2에서는 `recv()`, `recvn()`, `recvuntil()`, `recvline()`의 차이를 실습하면서 배워보자.

특히 `recv(n)`이 항상 n바이트를 반환하는 것은 아니라는 점이 중요한 학습 포인트가 될 거야.

---