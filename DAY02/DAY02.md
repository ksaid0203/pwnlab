# chatgpt response

# pwntools Day 2 — 데이터 수신 함수 완전 정복

(1주 차 · 2/20회) 2026년 11월 20일

어제는 `send()`와 `sendline()`의 차이, NULL 바이트, C의 `read()`와 `fgets()`를 학습했어.

오늘은 **프로그램이 출력하는 데이터를 정확하게 읽는 방법**을 배울 거야. 앞으로 메모리 주소 leak이나 메뉴 기반 pwnable 문제를 풀 때 필수적인 내용이야.

**오늘의 학습 계획** 총 60분

1. 이론 15분 — `recv`, `recvn`, `recvuntil`, `recvline`
2. 실습 35분 — 직접 만든 C 프로그램과 데이터 송수신
3. 정리 10분 — 수신 함수 선택과 디버깅

## 1. 이론 (15분)

| 함수 | 동작 |
|--------|--------|
| `recv(8)` | 최대 8바이트 수신 |
| `recvn(8)` | 정확히 8바이트가 모일 때까지 대기 |
| `recvuntil(b'> ')` | 특정 구분자가 나올 때까지 수신 |
| `recvline()` | 개행 문자까지 수신 |

여기서 가장 중요한 차이는 `recv(8)`과 `recvn(8)`이야.

`recv(8)`은 최대 8바이트만 요청하기 때문에 3바이트만 반환할 수도 있어. 반면 `recvn(8)`은 8바이트가 모일 때까지 기다려. 단, EOF나 타임아웃이 발생하면 정상적으로 8바이트를 얻지 못할 수 있어.

**수신 버퍼 예시**

8바이트 중 처음 3바이트만 도착했다고 가정

`recv(8)` → `b'ABC'`를 반환할 수 있음

`recvn(8)` → 나머지 5바이트를 기다림

## 2. 실습 (35분)

### Step 1. C 프로그램 작성

`chall.c` 파일을 만들어 봐.

```c

#include <stdio.h>
#include <unistd.h>

int main(void) {
    char buf[32];

    printf("MENU> ");
    fflush(stdout);

    if (fgets(buf, sizeof(buf), stdin) == NULL)
        return 1;

    write(1, "ABCDEFGH", 8);
    write(1, "\nDONE\n", 6);

    return 0;
}
```

컴파일\:

```bash
gcc -o chall chall.c
```

이 프로그램은 입력을 한 줄 받은 뒤 `ABCDEFGH\nDONE\n`을 출력해.

### Step 2. pwntools로 수신하기

```python

from pwn import *

context.log_level = 'debug'

p = process('./chall')

p.sendlineafter(b'MENU> ', b'hello')

data1 = p.recvn(4)
data2 = p.recvn(4)
data3 = p.recvline()
data4 = p.recvline()

print("data1:", repr(data1))
print("data2:", repr(data2))
print("data3:", repr(data3))
print("data4:", repr(data4))

p.close()
```

예상 출력\:

```text
data1: b'ABCD'
data2: b'EFGH'
data3: b'\n'
data4: b'DONE\n'
```

`recvn(4)`를 두 번 호출했기 때문에 처음 8바이트를 나누어 읽는 거야.

중요한 점은 `recv` 계열 함수가 이미 받은 데이터를 내부 버퍼에 보관할 수 있다는 거야. 디버그 로그에 14바이트가 한꺼번에 수신된 것으로 보여도, 각 함수는 요청한 만큼 데이터를 꺼내 반환할 수 있어.

### Step 3. recvuntil() 실습

다음 코드도 실행해 봐.

```python

from pwn import *

p = process('./chall')

p.recvuntil(b'MENU> ')
p.sendline(b'test')

result = p.recvuntil(b'\n')
print(repr(result))

remaining = p.recvall()
print(repr(remaining))

p.close()
```

예상 결과\:

```text
b'ABCDEFGH\n'
b'DONE\n'
```

`recvuntil(b'\n')`은 기본적으로 구분자 `\n`까지 반환한다는 점을 기억해.

## 3. 오늘의 실습 과제

아래 코드는 앞서 만든 `chall` 프로그램을 실행해.

```python
from pwn import *

p = process('./chall')
p.sendlineafter(b'MENU> ', b'test')

# TODO: 여기에 수신 코드를 작성

p.close()
```

`TODO` 부분을 수정해서 다음 결과가 나오도록 만들어 봐.

**목표 출력**

```text
first: b'ABC'
second: b'DEFGH'
third: b'DONE'
```

---

**조건**

- `first`는 `recvn()`으로 수신
- `second`는 `recvuntil()`을 활용
- `third`는 `recvline()`을 활용
- 출력에서 불필요한 `\n`은 제거

힌트: `recvuntil()`에는 `drop=True` 옵션이 있고, `recvline()` 결과에는 `.strip()`을 사용할 수 있어.

## 4. 학습 정리 (10분)

**Day 2 이해도 퀴즈** /3 응답

오늘의 핵심은 **원하는 바이트 수를 읽는 것과 특정 구분자까지 읽는 것은 다르다**는 거야.

실습 과제 코드를 완성한 뒤 이 대화에 붙여 넣으면, 실제 pwnable 코드 리뷰처럼 각 수신 함수의 동작과 잠재적인 문제까지 검토할 수 있어.

---

# you asked

message time: 2026-11-20 22:47:16

from pwn import *

p = process('./chall')
p.sendlineafter(b'MENU> ', b'test')

print(f'first: {p.recvn(3)}')
print(f'second: {p.recvuntil(b'\n').strip()}')
print(f'third: {p.recvline().strip()}')

p.close()

---

# chatgpt response

좋아\! 전체적인 접근은 정확해. 특히 `recvn(3)`으로 처음 3바이트를 읽고, `recvuntil()`과 `recvline()`으로 나머지를 처리하려는 의도가 잘 보여.

다만 **Python 문법 오류가 한 군데 있어.**

## 1. 코드 리뷰

문제가 되는 부분은 다음 코드야.

```python
print(f'second: {p.recvuntil(b'\n').strip()}')
```

바깥쪽 f-string과 내부 바이트 문자열에 모두 작은따옴표(`'`\)를 사용했어.

Python 3.11 이하에서는 이 코드가 `SyntaxError`를 발생시켜. Python 3.12 이상에서는 f-string 문법이 개선되어 허용될 수 있지만, 버전 호환성을 위해 바깥쪽에 큰따옴표를 사용하는 게 좋아.

## 2. 수정한 코드

```python
from pwn import *

p = process('./chall')
p.sendlineafter(b'MENU> ', b'test')

print(f"first: {p.recvn(3)}")
print(f"second: {p.recvuntil(b'\n').strip()}")
print(f"third: {p.recvline().strip()}")

p.close()
```

예상 출력은 다음과 같아.

```text
first: b'ABC'
second: b'DEFGH'
third: b'DONE'
```

## 3. 한 가지 더 알아두면 좋은 점

네가 사용한 `.strip()`은 문자열 양쪽의 공백 문자도 제거해.

```python
data = b'  ABC  \n'
print(data.strip())

# b'ABC'
```

만약 개행 문자만 제거하고 싶다면 다음과 같이 작성할 수 있어.

```python
data = p.recvuntil(b'\n', drop=True)
```

또는\:

```python
data = p.recvline(keepends=False)
```

이렇게 하면 다른 공백 문자를 보존할 수 있어.

## 4. Day 2 평가

**Day 2 — 수신 함수** (개념 통과)

## 5. 추가 도전 문제

마지막으로 하나만 더 생각해 보자.

```python
p.recvn(3)
p.recvuntil(b'G')
p.recvline()
```

C 프로그램이 `ABCDEFGH\nDONE\n`을 출력했다면, **각 함수는 어떤 데이터를 반환할까?**

특히 세 번째 `recvline()`이 무엇을 반환하는지 생각해 봐.

이 문제까지 해결하면 Day 2를 마무리하고, Day 3에서는 `sendafter()`와 `sendlineafter()`를 활용한 메뉴 자동화로 넘어가자.

---

# you asked

message time: 2026-11-20 22:48:36

ABC
DEFG
H

---

# chatgpt response

정답이야\! 🎯 **3개 모두 정확하게 이해했어.**

다만 실제 반환값에는 바이트 타입과 개행 문자가 포함된다는 점을 기억하자.

```python
p.recvn(3)           # b'ABC'
p.recvuntil(b'G')    # b'DEFG'
p.recvline()         # b'H\n'
```

### 왜 세 번째 결과가 `b'H\n'`일까?

프로그램이 출력하는 전체 데이터는 다음과 같아.

```text
ABCDEFGH\nDONE\n
```

recvn(3)

recvuntil(b'G')

recvline()

`recvline()`은 `H`만 읽는 게 아니라 그 뒤에 있는 `\n`까지 읽기 때문이야.

이후 `p.recvline()`을 한 번 더 호출하면 `b'DONE\n'`이 반환돼.

**Day 2 학습 결과** (완료)

# 2 / 20회

입출력 함수의 기본 동작을 이해했어.

다음 **Day 3**에서는 `sendafter()`와 `sendlineafter()`를 이용해 여러 단계의 입력을 요구하는 C 프로그램을 자동화하는 실습을 진행할 거야.

이때부터 실제 pwnable 문제에서 자주 등장하는 메뉴 기반 입력 처리 패턴을 연습하게 돼.

---