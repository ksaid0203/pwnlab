# chatgpt response

# pwntools Day 3 — 메뉴 기반 프로그램 자동화

(1주 차 · 3/20회) 2026년 11월 21일 (토)

Day 1에서는 `send()`와 `sendline()`을, Day 2에서는 `recvuntil()`, `recvn()`, `recvline()`을 학습했어.

오늘은 이 함수들을 조합해서 **여러 단계의 입력을 요구하는 프로그램을 자동으로 조작하는 방법**을 연습할 거야. 실제 pwnable 문제에서 메뉴를 선택하고, 값을 입력하고, 결과를 읽는 기본 패턴이야.

**오늘의 학습 목표**

이론 **15분**

코드 실습 **35분**

복습 및 과제 **10분**

## 1. 이론 — sendafter와 sendlineafter (15분)

두 함수는 수신과 전송을 하나로 묶어 주는 편의 함수야.

```python
p.sendafter(b'Name: ', b'AAAA')
```

위 코드는 다음과 같아.

```python
p.recvuntil(b'Name: ')
p.send(b'AAAA')
```

마찬가지로\:

```python
p.sendlineafter(b'Choice: ', b'1')
```

는 다음과 같아.

```python
p.recvuntil(b'Choice: ')
p.sendline(b'1')
```

| 함수 | 기다리는 대상 | 전송 방식 |
|--------|--------|--------|
| `sendafter(a, b)` | `a`가 출력될 때까지 | `b` 그대로 |
| `sendlineafter(a, b)` | `a`가 출력될 때까지 | `b` \+ `\n` |

여기서 중요한 것은 **프로그램이 다음 입력을 받을 준비가 되었을 때 전송한다**는 점이야.

### 데이터 송수신 흐름

```svg
<svg viewBox="0 0 340 240" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="6" width="130" height="32" rx="7" fill="#2563eb" fill-opacity=".12" stroke="#2563eb" stroke-opacity=".5" /><rect x="202" y="6" width="130" height="32" rx="7" fill="#16a34a" fill-opacity=".12" stroke="#16a34a" stroke-opacity=".5" /><g font-size="12" font-weight="600" fill="currentColor" text-anchor="middle"><text x="73" y="26">Python / pwntools</text><text x="267" y="26">C 프로그램</text></g><g stroke="currentColor" stroke-opacity=".25" stroke-dasharray="4 4"><path d="M73 38V232 M267 38V232" /></g><g stroke-width="1.6" fill="none"><path d="M267 64H73" stroke="#16a34a" /><path d="M73 64l7 -4v8z" fill="#16a34a" stroke="none" /><path d="M73 111H267" stroke="#2563eb" /><path d="M267 111l-7 -4v8z" fill="#2563eb" stroke="none" /><path d="M267 157H73" stroke="#16a34a" /><path d="M73 157l7 -4v8z" fill="#16a34a" stroke="none" /><path d="M73 205H267" stroke="#2563eb" /><path d="M267 205l-7 -4v8z" fill="#2563eb" stroke="none" /></g><g font-size="11" fill="currentColor" text-anchor="middle"><text x="170" y="56">"Choice: "</text><text x="170" y="102">b'1\n'</text><text x="170" y="149">"Name: "</text><text x="170" y="196">b'AAAA\n'</text></g></svg>
```

프로그램의 프롬프트를 확인한 다음 데이터를 보내는 순서

## 2. 코드 실습 (35분)

### Step 1. 메뉴 프로그램 만들기

`menu.c` 파일을 작성해 봐.

```c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char name[64];
    char choice[16];

    while (1) {
        printf("\n1. Set name\n");
        printf("2. Show name\n");
        printf("3. Exit\n");
        printf("Choice: ");
        fflush(stdout);

        if (!fgets(choice, sizeof(choice), stdin))
            break;

        switch (atoi(choice)) {
            case 1:
                printf("Name: ");
                fflush(stdout);

                if (!fgets(name, sizeof(name), stdin))
                    return 1;

                name[strcspn(name, "\n")] = '\0';
                break;

            case 2:
                printf("Your name: %s\n", name);
                break;

            case 3:
                puts("Bye!");
                return 0;

            default:
                puts("Invalid choice");
        }
    }

    return 0;
}
```

이 프로그램에는 학습용으로 한 가지 개선할 점이 있어. `name`을 설정하기 전에 2번을 선택하면 초기화되지 않은 배열을 문자열로 출력하게 돼. 정상적인 프로그램이라면 `char name[64] = {0};`으로 초기화해야 해.

컴파일\:

```bash
gcc -o menu menu.c
```

### Step 2. pwntools로 메뉴 자동화

```python

from pwn import *

context.log_level = 'debug'

p = process('./menu')

# 1. 이름 설정
p.sendlineafter(b'Choice: ', b'1')
p.sendlineafter(b'Name: ', b'pwntools')

# 2. 이름 출력
p.sendlineafter(b'Choice: ', b'2')
p.recvuntil(b'Your name: ')
name = p.recvline(keepends=False)

print(f"Saved name: {name!r}")

# 3. 종료
p.sendlineafter(b'Choice: ', b'3')
print(p.recvline().decode().strip())

p.close()
```

예상 결과\:

```text
Saved name: b'pwntools'
Bye!
```

`context.log_level = 'debug'`가 설정되어 있기 때문에 실제 실행에서는 추가 송수신 로그도 출력돼.

### Step 3. 함수로 자동화하기

메뉴를 반복적으로 선택해야 한다면 함수를 만드는 것이 좋아.

```python
def choose(p, number):
    p.sendlineafter(b'Choice: ', str(number).encode())

def set_name(p, name):
    choose(p, 1)
    p.sendlineafter(b'Name: ', name)

def show_name(p):
    choose(p, 2)
    p.recvuntil(b'Your name: ')
    return p.recvline(keepends=False)
```

이제 복잡한 입력 과정을 다음처럼 단순화할 수 있어.

```python
set_name(p, b'AAAA')
print(show_name(p))

set_name(p, b'BBBB')
print(show_name(p))

choose(p, 3)
p.close()
```

이런 함수들을 **익스플로잇 헬퍼 함수**라고 부르기도 해. 메뉴 기반 pwnable 문제에서는 `add()`, `edit()`, `delete()`, `show()` 같은 함수로 정리하는 경우가 많아.

## 3. 직접 풀어볼 실습 과제

오늘은 정답 코드를 제공하지 않을게. 직접 구현해 보는 것이 목표야.

**Day 3 과제 — 자동화 스크립트 작성**

아래 동작을 순서대로 수행하는 Python 스크립트를 작성해 봐.

1. 프로그램을 `process('./menu')`로 실행한다.
2. 메뉴 1번을 선택하고 이름을 `AAAA`로 설정한다.
3. 메뉴 2번으로 이름을 출력하고 `b'AAAA'`인지 확인한다.
4. 이름을 `BBBB`로 변경하고 다시 확인한다.
5. 메뉴 3번을 선택해 정상 종료한다.

---

**추가 조건**

`choose()`, `set_name()`, `show_name()` 함수를 반드시 만들어 사용하고, 결과 확인에는 `assert`를 사용해 봐.

`assert`는 조건이 거짓이면 `AssertionError`를 발생시키는 Python 문법이야.

```python
assert show_name(p) == b'AAAA'
```

## 4. 복습 (10분)

**Day 3 이해도 퀴즈** /3 응답

오늘의 핵심은 **메뉴를 선택하는 코드와 실제 익스플로잇 로직을 분리하는 습관**이야. 이렇게 작성하면 프로그램의 입출력 구조가 복잡해져도 코드를 쉽게 수정하고 디버깅할 수 있어.

다음 Day 4에서는 `p32()`, `p64()`, `u32()`, `u64()`를 사용해 정수와 바이트 데이터를 변환하고, 리틀 엔디언을 직접 확인하는 실습으로 넘어갈 거야.

---

# you asked

message time: 2026-11-21 20:49:01

문제가 생겼어 이름 출력 후 Saved name: 줄로 이동을 하지 못해.

---

# chatgpt response

이 상황은 pwntools에서 자주 발생하는 **입출력 동기화 문제**일 가능성이 있어.

우선 이전에 작성한 코드를 보면\:

```python
p.sendlineafter(b'Choice: ', b'2')
p.recvuntil(b'Your name: ')
name = p.recvline(keepends=False)

print(f"Saved name: {name!r}")
```

정상적으로 실행된다면 `Saved name: b'pwntools'`가 출력되어야 해.

## 1. 먼저 디버그 로그를 확인해 보자

다음 코드를 실행해 봐.

```python
from pwn import *

context.log_level = 'debug'

p = process('./menu')

p.sendlineafter(b'Choice: ', b'1')
p.sendlineafter(b'Name: ', b'pwntools')

p.sendlineafter(b'Choice: ', b'2')

print("[*] recvuntil 시작")
p.recvuntil(b'Your name: ', timeout=2)

print("[*] recvline 시작")
name = p.recvline(timeout=2)

print(f"Saved name: {name!r}")

p.close()
```

`timeout=2`를 설정하면 데이터를 무한정 기다리는 상황을 피할 수 있어.

## 2. 어디서 멈추는지 확인하기

| 마지막으로 출력된 내용 | 의심할 부분 |
|--------|--------|
| `recvuntil 시작` | `Your name: ` 문자열을 찾지 못함 |
| `recvline 시작` | 개행 문자가 오지 않음 |
| `Saved name: b''` | 타임아웃 또는 수신 데이터 부족 |
| `Saved name: b'pwntools\n'` | 정상 수신, 개행 포함 |

특히 다음 부분을 확인해 봐.

```c
printf("Your name: %s\n", name);
```

C 코드가 정확히 이 형태인지 확인해야 해.

예를 들어 C 프로그램이 `Your Name:`을 출력하는데 Python에서 `Your name:`을 기다리면 `recvuntil()`이 계속 대기할 수 있어.

## 3. 또 다른 가능성: stdout 버퍼링

C 코드에서 다음 부분이 빠지면 입력을 기다리는 프롬프트가 즉시 전달되지 않을 수 있어.

```c
printf("Choice: ");
fflush(stdout);
```

우리가 작성한 예제에는 이미 `fflush(stdout)`이 들어 있으므로, 동일한 코드를 사용했다면 이 문제일 가능성은 낮아.

---

### 확인하고 싶은 것

**실행했을 때 마지막으로 출력되는 `[DEBUG]` 로그를 보여줄 수 있을까?**

특히 `Your name:`이 출력되는지, `recvuntil()`에서 멈추는지 확인하면 원인을 정확히 찾을 수 있어.

가능하다면 현재 작성한 Python 코드도 함께 보내줘. 어느 줄에서 대기하는지 분석해 줄게.

---

# you asked

message time: 2026-11-21 20:52:13

아 다시보니 이름 출력 후 메뉴 출력을 하고 있네. 느낌상 12번째 줄의 name = p.recvline()이 문제일듯 해.

---

# chatgpt response

좋아, 관찰한 내용이 중요한 단서야. 다만 **이름 출력 후 메뉴가 다시 출력되는 건 정상 동작**이야.

C 코드가 `while (1)` 반복문으로 되어 있기 때문에 이름을 출력한 뒤 다시 메뉴를 보여주는 거야.

문제는 `recvline()` 자체보다는 **어느 지점에서 Python 코드가 대기하고 있는지** 확인하는 거야.

### 데이터 흐름 확인

메뉴 2번을 선택하면 C 프로그램은 다음 내용을 출력해.

```text
Your name: pwntools

1. Set name
2. Show name
3. Exit
Choice:
```

Python에서는\:

```python
p.recvuntil(b'Your name: ')
name = p.recvline(keepends=False)
print(f"Saved name: {name!r}")
```

이 순서로 처리해.

1. `recvuntil()`이 `Your name: `까지 소비
2. `recvline()`이 `pwntools\n`을 소비
3. `print()`가 `Saved name: b'pwntools'` 출력

이후 메뉴 출력은 pwntools 내부 버퍼에 남아 있다가 다음 `sendlineafter(b'Choice: ', ...)`에서 소비될 수 있어.

### 원인을 찾는 간단한 방법

```python
print("A: 메뉴 2번 선택 시작", flush=True)
p.sendlineafter(b'Choice: ', b'2')

print("B: 이름 프롬프트 수신 시작", flush=True)
p.recvuntil(b'Your name: ')

print("C: 이름 수신 시작", flush=True)
name = p.recvline(timeout=2)

print(f"D: Saved name: {name!r}", flush=True)
```

여기서 `D`가 출력된다면 `recvline()`은 정상적으로 끝난 거야.

그리고 한 가지 확인할 점이 있어. `context.log_level = 'debug'`를 설정했다면 화면에 보이는 메뉴 출력은 Python의 `print()`가 아니라 **pwntools의 DEBUG 수신 로그**일 수도 있어.

**질문 하나\:** 이름 출력 후 메뉴가 다시 나타났을 때, 프로그램이 계속 멈춰 있는 상태야? 아니면 `Saved name:`이 출력되지 않은 채 종료돼? 이 차이를 알면 원인을 더 정확히 좁힐 수 있어.

---

# you asked

message time: 2026-11-21 21:01:01

미안해 보고 받아적다가 Your Name으로 python에 작성했네.

3번은 아래와 같이 작성하면되나?

from pwn import *

def choose(p, number) :
    p.sendlineafter(b'Choice: ', str(number).encode())

def set_name(p, name) :
    choose(p, 1)
    p.sendlineafter(b'Name: ', name)

def show_name(p) :
    choose(p, 2)
    p.recvuntil(b'Your name: ')
    return p.recvline(keepends=False)

context.log_level = 'debug'

p = process('./menu')

set_name(p, b'AAAA')
print(show_name(p))

set_name(p, b'BBBB')
print(show_name(p))

choose(p, 3)
p.close()

---

# chatgpt response

응\! **작성한 코드는 정상적으로 동작하고, Day 3의 핵심 목표도 달성했어.** 👍

특히 `choose()`, `set_name()`, `show_name()`으로 기능을 분리한 점이 좋아. 실제 pwnable 익스플로잇을 작성할 때도 이런 구조를 많이 사용해.

## 1. 코드 리뷰

| 항목 | 평가 |
|--------|--------|
| `choose()` 메뉴 선택 | 정확함 |
| `set_name()` 이름 설정 | 정확함 |
| `show_name()` 이름 반환 | 정확함 |
| `sendlineafter()` 사용 | 정확함 |
| 메뉴 3번으로 종료 | 정확함 |
| `assert`로 결과 검증 | 추가 필요 |

현재 코드의 예상 출력은 다음과 같아.

```text
b'AAAA'
b'BBBB'
```

`context.log_level = 'debug'` 때문에 송수신 로그도 함께 출력될 거야.

## 2. 한 가지만 개선해 보자

과제에서 요구한 `assert`를 추가하면 완벽해.

```python
set_name(p, b'AAAA')
assert show_name(p) == b'AAAA'

set_name(p, b'BBBB')
assert show_name(p) == b'BBBB'

choose(p, 3)
p.close()
```

`print()`는 결과를 보여주지만, `assert`는 결과가 예상과 다를 때 오류를 발생시켜.

실제 익스플로잇에서도 특정 메뉴 동작이나 수신 데이터가 예상대로인지 검증할 때 유용해.

## 3. 추가로 알아둘 점

네가 작성한 함수\:

```python
def choose(p, number):
    p.sendlineafter(b'Choice: ', str(number).encode())
```

여기서 `str(number).encode()`의 역할을 정확히 이해하면 좋아.

```python
number = 3

print(str(number))           # '3'
print(str(number).encode())  # b'3'
```

즉, 정수 `3`을 프로그램에 전송할 수 있는 바이트 문자열 `b'3'`으로 변환하는 거야.

## Day 3 학습 결과

**메뉴 자동화** (실습 통과)

# 3 / 20회

Day 1\~3 학습 완료 · Day 4는 정수와 바이트 변환

### 마지막 확인 문제

다음 코드에서\:

```python
set_name(p, b'AAAA\x00BBBB')
```

C 프로그램이 다음과 같이 출력한다면\:

```c
printf("Your name: %s\n", name);
```

**`show_name(p)`의 반환값은 무엇일까?**

이 문제는 Day 1에서 배운 NULL 바이트와 오늘 학습한 메뉴 자동화를 연결하는 복습 문제야.

---

# you asked

message time: 2026-11-21 21:01:36

AAAA

---

# chatgpt response

정답이야\! 🎯

정확한 반환값은 \*\*`b'AAAA'`\*\*야.

```python
set_name(p, b'AAAA\x00BBBB')
print(show_name(p))

# b'AAAA'
```

이유는 다음과 같아.

1. `sendlineafter()`는 `b'AAAA\x00BBBB\n'`을 전송해.
2. C의 `fgets()`는 NULL 바이트(`\x00`\)를 포함한 데이터도 읽어서 배열에 저장해.
3. `printf("%s", name)`은 첫 번째 NULL 바이트를 문자열의 끝으로 인식해.
4. 따라서 `AAAA`까지만 출력되고, `show_name()`은 `b'AAAA'`를 반환해.

**중요한 차이\:** `BBBB`가 전송되지 않은 게 아니라, 메모리에는 저장되었지만 `%s` 출력에서 보이지 않는 거야.

**Day 3 최종 결과**

**실습 및 복습 완료**

진도: 3/20회 (15%)

다음 **Day 4**에서는 `p32()`, `p64()`, `u32()`, `u64()`와 리틀 엔디언을 배울 거야.

특히 메모리 주소를 바이트로 변환하는 방법은 앞으로 BOF와 ROP 익스플로잇을 작성할 때 계속 사용하게 돼.

---