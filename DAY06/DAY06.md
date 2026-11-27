# chatgpt response

# Day 6 — ELF 구조와 함수 주소 분석

(2주 차 · 6/20회) 2026년 11월 24일 (화)

1주 차에서는 pwntools를 이용한 입출력 자동화, 바이트 처리, 정수 변환, 로컬 및 원격 연결을 학습했어.

오늘부터는 본격적으로 **바이너리 분석과 시스템 해킹의 기초**를 공부할 거야. 첫 번째 주제는 pwntools의 `ELF()`를 이용해 실행 파일 내부의 정보를 추출하는 방법이야.

**오늘의 학습 구성**

이론 — ELF 구조와 심볼 **15분**

실습 — 실행 파일 분석 **35분**

정리 — 직접 풀 과제 및 복습 **10분**

## 1. 이론 — ELF란? (15분)

ELF(Executable and Linkable Format)는 Linux에서 실행 파일, 오브젝트 파일, 공유 라이브러리 등에 사용되는 바이너리 파일 형식이야.

C 소스코드를 GCC로 컴파일하면 일반적으로 ELF 형식의 실행 파일이 만들어져.

**ELF 파일의 주요 구성 요소**

이해를 위한 개념도이며 실제 ELF 파일의 배치 순서는 달라질 수 있어. .bss는 일반적으로 파일에 실제 데이터 바이트를 저장하지 않아.

### 심볼(Symbol)이란?

심볼은 함수나 변수 등의 이름과 주소 정보를 연결해 주는 정보야.

예를 들어 다음과 같은 함수가 있다고 가정해 보자.

```c
void hello() {
    puts("Hello!");
}

int main() {
    hello();
    return 0;
}
```

컴파일된 실행 파일에 해당 심볼 정보가 남아 있다면 pwntools로 함수 주소를 찾을 수 있어.

```python
elf = ELF('./chall')

print(hex(elf.symbols['main']))
print(hex(elf.symbols['hello']))
```

이렇게 하면 함수 주소를 직접 찾아서 코드에 하드코딩하지 않아도 돼.

### 오늘 배울 ELF 기능

| 기능 | 설명 |
|--------|--------|
| `ELF('./chall')` | ELF 파일 분석 |
| `elf.arch` | CPU 아키텍처 |
| `elf.bits` | 32비트 또는 64비트 |
| `elf.endian` | 엔디언 정보 |
| `elf.entry` | 프로그램 진입점 |
| `elf.symbols` | 심볼 정보 |
| `elf.search()` | 바이너리 내부 데이터 검색 |
| `elf.read()` | 가상 주소 기준 데이터 읽기 |
| `elf.checksec()` | 바이너리 보호 기법 확인 |

## 2. 실습 — ELF 분석하기 (35분)

### Step 1. 분석 대상 만들기 (5분)

`chall.c` 파일을 작성해.

```c

#include <stdio.h>

int global_value = 1234;
int empty_value;

void hello(void) {
    puts("Hello, pwntools!");
}

void secret(void) {
    puts("Secret function!");
}

int main(void) {
    hello();
    printf("Value: %d\n", global_value);
    return 0;
}
```

컴파일\:

```bash
gcc -O0 -g -no-pie chall.c -o chall
```

실행\:

```bash
./chall
```

예상 출력\:

```text
Hello, pwntools!
Value: 1234
```

컴파일 옵션의 의미는 다음과 같아.

| 옵션 | 의미 |
|--------|--------|
| `-O0` | 컴파일러 최적화 비활성화 |
| `-g` | 디버깅 정보 포함 |
| `-no-pie` | PIE 비활성화 |
| `-o chall` | 출력 파일 이름 지정 |

오늘은 함수 주소를 쉽게 비교하기 위해 실습용 바이너리에서만 PIE를 비활성화했어.

### Step 2. ELF 기본 정보 확인 (5분)

`day6.py` 파일을 작성해.

```python

from pwn import *

elf = ELF('./chall', checksec=False)

print("Architecture:", elf.arch)
print("Bits:", elf.bits)
print("Endian:", elf.endian)
print("Entry:", hex(elf.entry))

print(elf.checksec())
```

64비트 x86 Linux 환경이라면 다음과 비슷한 결과가 나올 거야.

```text
Architecture: amd64
Bits: 64
Endian: little
Entry: 0x401050
```

보호 기법과 실제 주소는 컴파일 환경에 따라 달라질 수 있어.

**주의\:** `elf.entry`는 `main()`의 주소와 반드시 같지는 않아. 일반적인 GCC 실행 파일에서는 `_start`가 먼저 실행되고 이후 초기화 과정을 거쳐 `main()`이 호출돼.

### Step 3. 함수와 변수 주소 찾기 (10분)

```python
from pwn import *

elf = ELF('./chall', checksec=False)

main_addr = elf.symbols['main']
hello_addr = elf.symbols['hello']
secret_addr = elf.symbols['secret']
global_addr = elf.symbols['global_value']

print(f"main:         {main_addr:#x}")
print(f"hello:        {hello_addr:#x}")
print(f"secret:       {secret_addr:#x}")
print(f"global_value: {global_addr:#x}")

assert main_addr != hello_addr
assert hello_addr != secret_addr
```

여기서 `secret()`은 실제로 호출되지 않는 함수지만, 컴파일된 파일에 함수와 심볼이 남아 있으므로 주소를 찾을 수 있어.

그리고 Day 4에서 배운 내용도 적용해 보자.

```python
packed = p64(secret_addr)

print("Address:", hex(secret_addr))
print("Packed:", packed.hex(' '))

assert u64(packed) == secret_addr
```

`elf.symbols`에서 얻은 주소는 `int` 자료형이므로 바로 `p64()`에 전달할 수 있어.

### Step 4. 섹션 정보 확인하기 (5분)

```python
from pwn import *

elf = ELF('./chall', checksec=False)

for name in ['.text', '.rodata', '.data', '.bss']:
    section = elf.get_section_by_name(name)

    if section is None:
        continue

    addr = section.header.sh_addr
    size = section.header.sh_size

    print(f"{name:10} addr={addr:#x}, size={size:#x}")
```

이 코드는 각 섹션의 시작 주소와 크기를 출력해.

`main()`, `hello()`, `secret()` 같은 함수는 일반적으로 `.text` 섹션에 위치하고, 초기화된 전역 변수 `global_value`는 `.data` 섹션에 위치해.

### Step 5. 문자열과 전역 변수 읽기 (10분)

이번에는 ELF 파일 내부에서 데이터를 직접 찾아보자.

```python

from pwn import *

elf = ELF('./chall', checksec=False)

# 문자열 검색
string_addr = next(
    elf.search(b'Hello, pwntools!\x00')
)

print(f"String address: {string_addr:#x}")

# 문자열 데이터 읽기
data = elf.read(string_addr, 17)

print("String:", data)

# 전역 변수 읽기
global_addr = elf.symbols['global_value']
raw = elf.read(global_addr, 4)

print("Raw bytes:", raw.hex(' '))
print("Integer:", u32(raw))

assert u32(raw) == 1234
```

예상 결과\:

```text
String address: 0x...
String: b'Hello, pwntools!\x00'
Raw bytes: d2 04 00 00
Integer: 1234
```

Day 4에서 학습한 `u32()`가 실제 바이너리 분석에 활용되는 예제야.

**전역 변수 global\_value 분석**

C 코드: int global\_value = 1234;

u32(raw)

# 1234

0x4d2

참고로 `elf.read()`는 실행 중인 프로세스의 현재 메모리를 읽는 함수가 아니라 ELF 객체의 바이너리 데이터를 가상 주소 기준으로 읽는 함수야.

## 3. 직접 풀 실습 과제

**Day 6 과제 — ELF 자동 분석기 만들기**

앞에서 컴파일한 `chall` 파일을 대상으로 다음 조건을 만족하는 `day6_task.py`를 작성해 봐.

- TODO 1: ELF 파일을 불러오고 아키텍처, 비트 수, 엔디언 출력하기.
- TODO 2: `main`, `hello`, `secret`의 함수 주소를 각각 출력하기.
- TODO 3: `secret` 함수 주소를 `p64()`로 변환하고 `u64()`로 복원하여 검증하기.
- TODO 4: `Secret function!` 문자열의 주소를 검색하고 데이터를 읽기.
- TODO 5: `global_value`의 데이터를 읽고 정수 `1234`로 복원하기.
- TODO 6: `main` 함수의 주소가 `.text` 섹션 범위에 포함되는지 `assert`로 검증하기.

```python

from pwn import *

# TODO 1: Load ELF

# TODO 2: Find function addresses

# TODO 3: Pack and unpack secret address

# TODO 4: Search and read string

# TODO 5: Read global_value

# TODO 6: Check main address range

print("All tests passed!")
```

**TODO 6 힌트**

섹션의 시작 주소와 크기를 얻으면 끝 주소를 계산할 수 있어.

```python
section = elf.get_section_by_name('.text')

start = section.header.sh_addr
size = section.header.sh_size
end = start + size
```

```svg
<svg viewBox="0 0 330 108" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="35" y="32" width="260" height="36" rx="4" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6" /><text x="165" y="54" text-anchor="middle" font-size="12" fill="currentColor">.text section</text><path d="M35 24V77 M295 24V77" stroke="currentColor" stroke-dasharray="3 3" /><text x="35" y="94" font-size="11" text-anchor="middle" fill="currentColor">start</text><text x="295" y="94" font-size="11" text-anchor="middle" fill="currentColor">end</text><path d="M116 19V31 M111 26L116 32L121 26" fill="none" stroke="#16a34a" stroke-width="2" /><text x="116" y="12" text-anchor="middle" font-size="11" fill="#16a34a">main_addr</text></svg>
```

main\_addr가 start 이상, end 미만인지 확인하면 돼.

이번에는 정답 코드를 제공하지 않을게. 지금까지 배운 `assert`, `p64()`, `u64()`와 오늘 배운 `ELF()`를 조합해서 직접 작성해 봐.

## 4. 정리 — 이해도 확인 (10분)

**Day 6 확인 퀴즈** /4 응답

### 마지막 심화 문제

다음 코드를 실행하면 어떤 결과가 나올지 생각해 봐.

```python
from pwn import *

elf = ELF('./chall', checksec=False)

addr = elf.symbols['global_value']

print(elf.read(addr, 4))
print(u32(elf.read(addr, 4)))

assert elf.read(addr, 4) == p32(1234)
```

`assert`가 통과하는지, 그리고 그 이유까지 설명할 수 있으면 오늘의 핵심 개념을 이해한 거야.

## 전체 학습 진도

# 6 / 20회

30% 차시 도달

**다음 Day 7 예고 — GOT와 PLT**

오늘은 ELF 파일에서 함수와 변수의 주소를 찾았어. 다음 시간에는 외부 라이브러리 함수가 어떻게 호출되는지, `elf.got['puts']`와 `elf.plt['puts']`는 어떤 차이가 있는지 학습할 거야. 이는 이후 libc 주소 분석과 ret2libc를 이해하는 데 중요한 기초가 돼.

---

# you asked

message time: 2026-11-24 21:25:39

실습 과제 제출
from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall06', checksec=False)

print(f"elf.arch: {elf.arch}")
print(f"elf.bits: {elf.bits}")
print(f"elf.endian: {elf.endian}")

# TODO 2: Find function addresses

print(f"main addr: {elf.symbols['main']}")
print(f"hello addr: {elf.symbols['hello']}")
print(f"secret addr: {elf.symbols['secret']}")

# TODO 3: Pack and unpack secret address
sec = p64(elf.symbols['secret'])
assert u64(sec) == elf.symbols['secret']

# TODO 4: Search and read string
search_addr = next(elf.search(b'Secret function!'))
print(f"search_addr: {search_addr}")
print(f"read(search_addr, 16): {elf.read(search_addr, 17)}")

# TODO 5: Read global_value
global_addr = elf.symbols['global_value']
global_value = elf.read(global_addr, 4)
print(f"{global_value}")

# TODO 6: Check main address range
section = elf.get_section_by_name('.text')
addr = section.header.sh_addr
size = section.header.sh_size
assert addr <= elf.symbols['main'] < addr + size

print("All tests passed!")

심화문제
1234
b'\xD2\x04'
assert 문은 잘 모르겠어

---

# chatgpt response

전체적으로 잘 작성했어\! 특히 TODO 3의 주소 패킹·언패킹 검증과 TODO 6의 `.text` 섹션 범위 검증은 정확해.

다만 TODO 4와 TODO 5에서 조금 수정할 부분이 있고, 심화 문제에서는 바이트 데이터와 정수의 차이를 다시 확인하면 좋겠어.

## 1. 실습 과제 코드 리뷰

| 과제 | 평가 | 설명 |
|--------|--------|--------|
| TODO 1 | 정답 | ELF 기본 정보 추출 |
| TODO 2 | 정답 | 함수 심볼 주소 추출 |
| TODO 3 | 정답 | 패킹 및 언패킹 검증 |
| TODO 4 | 부분 정답 | 문자열 읽기 길이 수정 |
| TODO 5 | 부분 정답 | 정수 변환 누락 |
| TODO 6 | 정답 | 섹션 주소 범위 검증 |

실제 바이너리를 실행하지 않고 제출한 코드와 앞서 제공한 C 소스코드를 기준으로 검토했어.

### TODO 2 — 주소 출력 방식

현재 코드도 틀리지 않았지만, 바이너리 분석에서는 주소를 16진수로 출력하는 것이 일반적이야.

```python
print(f"main addr: {elf.symbols['main']:#x}")
print(f"hello addr: {elf.symbols['hello']:#x}")
print(f"secret addr: {elf.symbols['secret']:#x}")
```

Day 4에서 배웠듯이 `#x`는 출력 형식만 바꾸므로 원래 주소의 자료형은 여전히 `int`야.

### TODO 4 — 문자열 읽기 길이

작성한 코드를 보면\:

```python
search_addr = next(elf.search(b'Secret function!'))
print(f"read(search_addr, 16): {elf.read(search_addr, 17)}")
```

`Secret function!`은 16바이트이고, 문자열 끝의 NULL 바이트까지 포함하면 17바이트야.

따라서 실제로 17바이트를 읽는 것은 맞아. 다만 출력 메시지에는 16이라고 적혀 있어.

이 부분은 내가 앞선 평가에서 수정 대상으로 분류했지만, **실제 읽기 길이는 정확해.** 더 좋은 방법은 `len()`을 사용하는 거야.

```python
target = b'Secret function!\x00'

search_addr = next(elf.search(target))
data = elf.read(search_addr, len(target))

print(f"Address: {search_addr:#x}")
print(f"Data: {data}")

assert data == target
```

이렇게 하면 문자열이 변경되어도 읽을 길이를 직접 계산할 필요가 없어.

### TODO 5 — 바이트를 정수로 변환

작성한 코드\:

```python
global_addr = elf.symbols['global_value']
global_value = elf.read(global_addr, 4)
print(f"{global_value}")
```

여기까지는 메모리 주소에 해당하는 ELF 데이터를 정확하게 읽었어.

하지만 과제의 조건은 정수 `1234`로 복원하는 것이었으므로 `u32()`를 추가해야 해.

```python
global_addr = elf.symbols['global_value']
raw = elf.read(global_addr, 4)
global_value = u32(raw)

print(f"Raw: {raw}")
print(f"Value: {global_value}")

assert global_value == 1234
```

예상 출력\:

```text
Raw: b'\xd2\x04\x00\x00'
Value: 1234
```

### TODO 6 — 아주 정확하게 작성했어

```python
assert addr <= elf.symbols['main'] < addr + size
```

Python의 연쇄 비교 연산자를 잘 활용했어.

시작 주소는 포함하고 끝 주소는 포함하지 않는다는 점까지 정확하게 구현했기 때문에 수정할 필요가 없어.

---

## 2. 심화 문제 해설

문제의 코드는 다음과 같았어.

```python
addr = elf.symbols['global_value']

print(elf.read(addr, 4))
print(u32(elf.read(addr, 4)))

assert elf.read(addr, 4) == p32(1234)
```

네 답변은 출력 순서가 반대이고, NULL 바이트 2개가 빠져 있어.

정확한 출력은 다음과 같아.

```text
b'\xd2\x04\x00\x00'
1234
```

그리고 **assert 문은 정상적으로 통과해.**

### 왜 assert가 통과할까?

C 코드에서는 다음과 같이 선언했지.

```c
int global_value = 1234;
```

일반적인 x86-64 Linux 환경에서 `int`는 4바이트이고 리틀 엔디언으로 저장돼.

정수 (int)

# 1234

0x000004d2

p32()   u32()

주소 +0

# D2

주소 +1

# 04

주소 +2

# 00

주소 +3

# 00

바이트 데이터 (bytes)

**`b'\xd2\x04\x00\x00'`**

---

elf.read(addr, 4)

D2 04 00 00

p32(1234)

D2 04 00 00

**두 바이트 데이터가 동일하므로 True**

결국 assert 문은 아래와 같은 비교를 하는 거야.

```python
assert b'\xd2\x04\x00\x00' == b'\xd2\x04\x00\x00'
```

Day 4에서 배웠던 패킹과 언패킹이 실제 ELF 분석에 적용된 사례야.

## 3. 자료형 정리

| 코드 | 자료형 | 반환값 |
|--------|--------|--------|
| `elf.symbols['global_value']` | `int` | 변수의 주소 |
| `elf.read(addr, 4)` | `bytes` | `b'\xd2\x04\x00\x00'` |
| `u32(elf.read(addr, 4))` | `int` | `1234` |
| `p32(1234)` | `bytes` | `b'\xd2\x04\x00\x00'` |
| `hex(1234)` | `str` | `'0x4d2'` |

**변수의 주소와 그 주소에 저장된 값은 서로 다르다**는 것도 반드시 기억해 둬.

## 4. Day 6 마지막 확인 문제

이번에는 C 코드에 다음과 같은 전역 변수가 있다고 가정해 보자.

```c
int global_value = 1234;
int empty_value;
```

Python에서 다음 코드를 실행했을 때\:

```python
addr = elf.symbols['empty_value']

raw = elf.read(addr, 4)

print(raw)             # 문제 1
print(u32(raw))        # 문제 2

assert raw == p32(0)   # 문제 3
```

세 가지 질문에 답해 봐.

- 문제 1: `raw`의 출력값은?
- 문제 2: `u32(raw)`의 출력값은?
- 문제 3: `assert`는 통과할까? 그 이유는?

힌트: 초기화하지 않은 전역 변수는 일반적으로 `.bss` 섹션에 위치해.

**Day 6 — ELF 분석** 마지막 복습 진행 중

# 6 / 20회

전체 학습 진도 30%

이 문제까지 해결하면 Day 6을 마무리하자.

---

# you asked

message time: 2026-11-24 21:32:21

b'\x00'
0
assert 조건문은 true 반환

---

# chatgpt response

거의 정답이야\! 두 번째와 세 번째 답은 정확하고, 첫 번째 답에서 바이트 길이만 수정하면 돼.

## 1. 정답 확인

| 문제 | 네 답변 | 정답 | 평가 |
|--------|--------|--------|--------|
| `print(raw)` | `b'\x00'` | `b'\x00\x00\x00\x00'` |  |
| `print(u32(raw))` | `0` | `0` |  |
| `assert raw == p32(0)` | True | 조건이 True이므로 통과 |  |

## 2. 왜 NULL 바이트가 4개일까?

C 코드에서 `empty_value`는 전역 변수이므로 명시적으로 초기화하지 않아도 0으로 초기화돼.

```c
int empty_value;
```

일반적인 x86-64 Linux 환경에서 `int`는 4바이트야.

**empty\_value의 메모리 구조**

`elf.read(addr, 4)`

**`b'\x00\x00\x00\x00'`**

`u32(raw)`

# 0

`.bss`는 ELF 파일에 변수의 실제 초기 데이터 바이트를 저장하지 않지만, pwntools의 `elf.read()`는 해당 영역의 데이터를 0으로 채워 반환할 수 있어.

## 3. assert는 True를 반환할까?

정확히 말하면 `assert` 자체가 `True`를 반환하는 것은 아니야.

```python
raw = b'\x00' * 4

print(raw == p32(0))  # True
assert raw == p32(0)  # 아무런 오류 없이 통과
```

비교 연산의 결과가 `True`이고, `assert`는 그 조건을 검사하는 문장이야.

## 4. Day 6 핵심 암기

| 코드 | 결과 | 크기 |
|--------|--------|--------|
| `b'\x00'` | NULL 바이트 | 1바이트 |
| `p32(0)` | NULL 바이트 4개 | 4바이트 |
| `p64(0)` | NULL 바이트 8개 | 8바이트 |
| `u32(p32(0))` | 정수 0 | 정수형 |

**정수의 값이 0이라고 해서 저장된 바이트의 길이가 1바이트인 것은 아니야.** 앞으로 메모리를 분석할 때 값과 데이터 크기를 항상 구분하는 습관을 들이자.

**Day 6 — ELF 분석** (학습 완료)

# 6 / 20회

30%

ELF 심볼, 섹션, 주소 검색, 데이터 읽기 학습 완료

다음 **Day 7 — GOT와 PLT**에서는 다음 세 가지 주소의 차이를 집중적으로 공부할 거야.

```python
elf.symbols['puts']
elf.got['puts']
elf.plt['puts']
```

앞으로 libc 주소를 분석하고 ret2libc를 이해하는 데 매우 중요한 개념이야.

---