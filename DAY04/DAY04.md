# chatgpt response

# pwntools Day 4 — p32, p64, u32, u64와 리틀 엔디언

(1주 차 · 4/20회) 2026년 11월 22일 (일)

Day 3에서는 `choose()`, `set_name()`, `show_name()`으로 메뉴 자동화를 구현했고, NULL 바이트가 C 문자열 출력에 미치는 영향까지 확인했어.

오늘은 **정수와 바이트 데이터를 서로 변환하는 방법**을 배울 거야. BOF에서 반환 주소를 덮어쓰거나 메모리에서 유출된 주소를 해석할 때 반드시 필요한 기초야.

**오늘의 학습 구성** 총 60분

이론 — 엔디언과 패킹 **15분**

실습 — 주소 변환과 검증 **35분**

정리 — 복습과 직접 풀 과제 **10분**

## 1. 이론 (15분)

### 패킹과 언패킹

| 함수 | 입력 | 반환 |
|--------|--------|--------|
| `p32(n)` | 32비트 정수 | 4바이트 |
| `p64(n)` | 64비트 정수 | 8바이트 |
| `u32(data)` | 4바이트 | 정수 |
| `u64(data)` | 8바이트 | 정수 |

`p`는 *pack*, `u`는 *unpack*을 뜻해.

```python
from pwn import *

context.endian = 'little'

print(p32(0x12345678))
# b'\x78\x56\x34\x12'

print(hex(u32(b'\x78\x56\x34\x12')))
# 0x12345678
```

### 리틀 엔디언이란?

`0x12345678`이라는 정수를 메모리에 저장할 때, 가장 낮은 자리의 바이트부터 저장하는 방식이 리틀 엔디언이야.

**32비트 정수: 0x12345678** (4 bytes)

낮은 메모리 주소

높은 메모리 주소

---

따라서 `p32(0x12345678)`의 결과는 `b'\x78\x56\x34\x12'`가 돼.

반대로 빅 엔디언에서는 `12 34 56 78` 순서로 저장해.

중요한 점은 **정수의 값 자체가 바뀌는 것이 아니라 바이트를 저장하고 해석하는 순서가 달라진다**는 거야.

## 2. 실습 (35분)

### Step 1. p32와 p64 비교

`day4.py` 파일을 작성해 봐.

```python

from pwn import *

context.endian = 'little'

addr = 0x401234

packed32 = p32(addr)
packed64 = p64(addr)

print("p32:", packed32.hex(' '))
print("p64:", packed64.hex(' '))

print("p32 length:", len(packed32))
print("p64 length:", len(packed64))
```

실행\:

```bash
python3 day4.py
```

예상 출력\:

```text
p32: 34 12 40 00
p64: 34 12 40 00 00 00 00 00
p32 length: 4
p64 length: 8
```

64비트 주소라도 실제 값이 작으면 상위 바이트가 `00`일 수 있어. 하지만 `p64()`는 항상 8바이트를 반환해.

### Step 2. u64로 주소 복원

```python
from pwn import *

context.endian = 'little'

leaked = b'\x90\x12\x40\x00\x00\x00\x00\x00'

addr = u64(leaked)

print(hex(addr))
# 0x401290
```

메모리에서 읽어 온 바이트를 정수 주소로 바꿀 때 사용하는 방식이야.

### Step 3. 6바이트 주소 복원하기

실제 64비트 Linux pwnable에서는 주소의 하위 6바이트만 얻는 상황도 자주 등장해.

```python
from pwn import *

context.endian = 'little'

leaked = b'\x90\x12\x40\x00\x00\x00'

addr = u64(leaked.ljust(8, b'\x00'))

print(hex(addr))
# 0x401290
```

여기서 핵심은 다음 코드야.

```python
leaked.ljust(8, b'\x00')
```

**6바이트를 8바이트로 확장**

수신한 6바이트

추가한 2바이트

`u64()`는 정확히 8바이트를 요구하므로 부족한 길이를 채워 주는 거야.

단, 0으로 패딩하는 방법은 생략된 상위 바이트가 실제로 0이라는 가정이 맞을 때만 정확해. 모든 주소 유출에 무조건 적용할 수 있는 방법은 아니야.

### Step 4. 엔디언 비교

```python
from pwn import *

value = 0x12345678

little = p32(value, endian='little')
big = p32(value, endian='big')

print("little:", little.hex(' '))
print("big:   ", big.hex(' '))

assert u32(little, endian='little') == value
assert u32(big, endian='big') == value
```

예상 출력\:

```text
little: 78 56 34 12
big:    12 34 56 78
```

이 실습으로 같은 정수라도 엔디언 설정에 따라 바이트 배열이 달라진다는 것을 확인할 수 있어.

## 3. 직접 풀 실습 과제

**Day 4 과제 — 주소 변환기 만들기**

다음 조건을 만족하는 `day4_task.py`를 작성해 봐.

1. `0xdeadbeef`를 `p32()`로 변환하고 출력하기
2. `0x401234`를 `p64()`로 변환하고 출력하기
3. `b'\xef\xbe\xad\xde'`를 `u32()`로 복원하기
4. 아래 6바이트 데이터를 8바이트로 패딩한 뒤 `u64()`로 복원하기
5. 각 변환 결과가 올바른지 `assert`로 확인하기

```python

from pwn import *

context.endian = 'little'

value32 = 0xdeadbeef
value64 = 0x401234

raw32 = b'\xef\xbe\xad\xde'
leak6 = b'\x80\x45\x23\x01\x00\x00'

# TODO 1: value32를 4바이트로 변환
# TODO 2: value64를 8바이트로 변환
# TODO 3: raw32를 정수로 복원
# TODO 4: leak6를 8바이트로 패딩한 뒤 복원
# TODO 5: assert로 결과 검증
```

## 4. 정리 (10분)

**Day 4 이해도 퀴즈** /3 응답

오늘은 \*\*정수를 바이트로 만드는 `p32/p64`와 바이트를 정수로 복원하는 `u32/u64`\*\*를 구분하는 것이 가장 중요해.

전체 학습 진도 4 / 20회 · 20%

다음 Day 5에서는 지금까지 배운 입출력과 바이트 변환을 종합해서 **로컬 프로그램과 TCP 서버에 동일한 pwntools 스크립트를 적용하는 실습**을 진행할 거야.

---

# you asked

message time: 2026-11-22 22:51:21

from pwn import *

context.endian = 'little'

value32 = 0xdeafbeef
value64 = 0x401234

raw32 = b'\xef\xbe\xad\xde'
leak6 = b'\x80\x45\x23\x01\x00\x00'

#TODO 1 : value32 to 4bytes
TODO1 = p32(value32)

#TODO 2 : value64 to 8bytes
TODO2 = p64(value64)

#TODO 3 : raw32 to int
TODO3 = u32(raw32)

#TODO 4 : leak6 to 8bytes with padding
TODO4 = u64(leak6.ljust(8, b'\x00'))

#TODO 5 : assert
assert TODO1 == b'\xef\xbe\xaf\xde'
assert TODO2 == b'\x34\x12\x40' + b'\x00' * 5
assert TODO3 == 0xdeadbeef, print(TODO3)
assert TODO4 == 0x1234580, print(TODO4)

실습과제 정답은 위와 같아.
근데 여기서 질문이 있는데, TODO3와 TODO4는 int data니까 hex로 바꿨는데 왜 틀렸다고 출력될까?

---

# chatgpt response

좋아\! 코드를 보면 `p32()`, `p64()`, `u32()`, `u64()`의 사용법은 정확히 이해했어. 👍

질문한 부분에서 핵심은 **정수를 16진수로 표현하는 것과 정수를 실제로 변환하는 것은 다르다**는 거야.

그리고 네 코드에는 `assert`와 관련해서 알아두면 좋은 부분도 있어.

## 1. TODO3는 사실 정답이야

```python
raw32 = b'\xef\xbe\xad\xde'
TODO3 = u32(raw32)

assert TODO3 == 0xdeadbeef
```

리틀 엔디언으로 해석하면 다음과 같아.

```text
메모리 바이트: EF BE AD DE
정수 표현:    0xDEADBEEF
```

따라서 `TODO3 == 0xdeadbeef`는 `True`야.

Python에서는 다음 두 표현이 완전히 동일한 정수야.

```python
print(3735928559 == 0xdeadbeef)
# True
```

즉, `hex()`로 변환할 필요가 없어.

## 2. TODO4도 정답이야

```python
leak6 = b'\x80\x45\x23\x01\x00\x00'
TODO4 = u64(leak6.ljust(8, b'\x00'))
```

8바이트로 패딩하면\:

리틀 엔디언 정수: `0x0000000001234580`

앞쪽의 0을 생략하면 `0x1234580`이므로 다음 비교도 `True`야.

```python
assert TODO4 == 0x1234580
```

## 3. 실제 오류는 TODO1에 있어

네 코드에서\:

```python
value32 = 0xdeafbeef
TODO1 = p32(value32)

assert TODO1 == b'\xef\xbe\xaf\xde'
```

이 부분은 정상적으로 통과해.

하지만 원래 과제의 값은 `0xdeadbeef`였어. 지금 작성한 값은 `0xdeafbeef`로, `AD`가 `AF`로 바뀌었어.

| 값 | 리틀 엔디언 바이트 |
|--------|--------|
| `0xdeadbeef` | `ef be ad de` |
| `0xdeafbeef` | `ef be af de` |

즉, 네가 작성한 코드 내부에서는 일관되지만 원래 과제와는 값이 달라진 거야.

## 4. assert 문법도 개선해 보자

현재 작성한 코드\:

```python
assert TODO3 == 0xdeadbeef, print(TODO3)
```

`assert` 뒤의 쉼표 다음에는 실패했을 때 표시할 메시지를 넣을 수 있어.

하지만 `print(TODO3)`은 값을 출력한 뒤 `None`을 반환하기 때문에 오류 메시지로는 적절하지 않아.

다음처럼 작성하는 것을 추천해.

```python
assert TODO3 == 0xdeadbeef, f"TODO3: {TODO3:#x}"
assert TODO4 == 0x1234580, f"TODO4: {TODO4:#x}"
```

`{TODO3:#x}`는 정수를 `0x`가 붙은 16진수 문자열로 보여줘.

### 전체 수정 코드

```python

from pwn import *

context.endian = 'little'

value32 = 0xdeadbeef
value64 = 0x401234

raw32 = b'\xef\xbe\xad\xde'
leak6 = b'\x80\x45\x23\x01\x00\x00'

TODO1 = p32(value32)
TODO2 = p64(value64)
TODO3 = u32(raw32)
TODO4 = u64(leak6.ljust(8, b'\x00'))

assert TODO1 == b'\xef\xbe\xad\xde'
assert TODO2 == b'\x34\x12\x40' + b'\x00' * 5
assert TODO3 == 0xdeadbeef, f"{TODO3:#x}"
assert TODO4 == 0x1234580, f"{TODO4:#x}"

print("All tests passed!")
```

이 코드는 정상적으로 실행되면 `All tests passed!`가 출력돼.

---

## 5. 마지막 확인 문제

다음 두 코드의 차이를 설명해 볼래?

```python
a = 0xdeadbeef
b = hex(0xdeadbeef)

print(type(a))
print(type(b))
```

**질문\:** `a`와 `b`의 자료형은 각각 무엇이고, `a == b`는 `True`일까, `False`일까?

이것까지 이해하면 정수, 바이트, 16진수 문자열의 차이를 확실하게 구분할 수 있어.

---

# you asked

message time: 2026-11-22 22:56:18

a는 int, b는 str, a == b 는 false

---

# chatgpt response

정답이야\! 🎯 **3개 모두 정확해.**

```python
a = 0xdeadbeef
b = hex(0xdeadbeef)

print(type(a))  # <class 'int'>
print(type(b))  # <class 'str'>
print(a == b)   # False
```

`hex()`는 정수를 16진수 **문자열**로 변환하는 함수야. 정수끼리 비교할 때는 `hex()`를 사용할 필요가 없어.

### 오늘 배운 자료형 정리

| 표현 | 자료형 | 의미 |
|--------|--------|--------|
| `0xdeadbeef` | `int` | 정수 |
| `hex(0xdeadbeef)` | `str` | 16진수 문자열 |
| `p32(0xdeadbeef)` | `bytes` | 리틀 엔디언 4바이트 |
| `u32(b'\xef\xbe\xad\xde')` | `int` | 바이트를 정수로 복원 |

특히 다음 차이를 기억하면 좋아.

```python
from pwn import *

value = 0xdeadbeef

print(hex(value))  # '0xdeadbeef'
print(p32(value))   # b'\xef\xbe\xad\xde'

assert int(hex(value), 16) == value
assert u32(p32(value)) == value
```

**Day 4 — 정수와 바이트 변환** (완료)

# 4 / 20회

전체 학습 진도 20%

Day 4 실습과 확인 문제까지 통과했어.

다음 **Day 5**에서는 `process()`와 `remote()`의 차이를 배우고, 로컬 프로그램과 TCP 서버에 동일한 입출력 코드를 적용하는 실습을 진행할 거야.

---