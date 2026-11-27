# chatgpt response

# Day 7 — GOT와 PLT의 구조 및 주소 분석

(2주 차 · 7/20회) 2026년 11월 25일 (수)

어제 Day 6에서는 `ELF()`를 사용해 함수 주소, 전역 변수, 섹션 정보를 분석했어. 특히 변수의 주소와 해당 주소에 저장된 데이터의 차이를 공부했지.

오늘은 외부 라이브러리 함수가 호출되는 원리를 알아볼 거야. GOT와 PLT는 이후 libc leak과 ret2libc를 이해하기 위한 핵심 개념이야.

**오늘의 학습 구성**

이론 — GOT, PLT, 동적 링킹 **15분**

실습 — GOT·PLT 주소 및 명령어 분석 **35분**

정리 — 실습 과제 및 복습 **10분**

## 1. 이론 — GOT와 PLT (15분)

### 1-1. 동적 링킹(Dynamic Linking)

다음 C 코드를 생각해 보자.

```c
#include <stdio.h>

int main(void) {
    puts("Hello!");
    return 0;
}
```

`main()`은 우리가 직접 작성한 함수지만, `puts()`는 libc에서 제공하는 함수야.

동적 링크 방식으로 컴파일하면 일반적으로 `puts()`의 실제 구현 전체가 실행 파일에 포함되지 않아. 대신 프로그램이 실행될 때 공유 라이브러리의 함수를 연결해서 사용해.

이 과정에서 GOT와 PLT가 사용돼.

### 1-2. GOT와 PLT의 차이

| 구분 | PLT | GOT |
|--------|--------|--------|
| 전체 이름 | Procedure Linkage Table | Global Offset Table |
| 역할 | 외부 함수 호출을 중계 | 주소 정보를 저장 |
| 주요 내용 | 기계어 명령어 | 주소 데이터 |
| pwntools | `elf.plt` | `elf.got` |
| 관련 섹션 | `.plt`, `.plt.sec` 등 | `.got`, `.got.plt` 등 |

쉽게 기억하면 **PLT는 실행하는 코드이고, GOT는 주소를 저장하는 공간**이야.

**puts() 함수 호출 과정**

```svg
<svg viewBox="0 0 340 342" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="65" y="8" width="210" height="53" rx="7" fill="#64748b" fill-opacity=".12" stroke="#64748b" /><text x="170" y="30" text-anchor="middle" font-size="13" font-weight="bold" fill="currentColor">main()</text><text x="170" y="47" text-anchor="middle" font-size="11" fill="currentColor">call puts@plt</text><path d="M170 61V87 M165 81L170 87L175 81" stroke="currentColor" fill="none" stroke-width="1.5" /><rect x="65" y="88" width="210" height="56" rx="7" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6" /><text x="170" y="110" text-anchor="middle" font-size="13" font-weight="bold" fill="#3b82f6">puts@plt</text><text x="170" y="129" text-anchor="middle" font-size="11" fill="currentColor">jmp [puts@got]</text><path d="M170 144V170 M165 164L170 170L175 164" stroke="currentColor" fill="none" stroke-width="1.5" /><rect x="65" y="171" width="210" height="56" rx="7" fill="#d97706" fill-opacity=".12" stroke="#d97706" /><text x="170" y="193" text-anchor="middle" font-size="13" font-weight="bold" fill="#d97706">puts@got</text><text x="170" y="212" text-anchor="middle" font-size="11" fill="currentColor">libc 함수 주소 저장</text><path d="M170 227V253 M165 247L170 253L175 247" stroke="currentColor" fill="none" stroke-width="1.5" /><rect x="65" y="254" width="210" height="56" rx="7" fill="#16a34a" fill-opacity=".12" stroke="#16a34a" /><text x="170" y="276" text-anchor="middle" font-size="13" font-weight="bold" fill="#16a34a">libc puts()</text><text x="170" y="295" text-anchor="middle" font-size="11" fill="currentColor">실제 함수 실행</text><text x="170" y="333" text-anchor="middle" font-size="10" fill="currentColor" opacity=".7">함수 주소가 연결된 이후의 호출 과정</text></svg>
```

### 1-3. GOT 주소와 GOT에 저장된 값

오늘 가장 중요한 개념이야.

예를 들어 다음과 같은 주소가 있다고 가정하자.

```svg
<svg viewBox="0 0 340 220" width="100%" xmlns="http://www.w3.org/2000/svg"><text x="10" y="17" font-size="11" fill="currentColor" opacity=".7">실행 파일 영역</text><rect x="10" y="29" width="320" height="57" rx="5" fill="#3b82f6" fill-opacity=".1" stroke="#3b82f6" /><text x="22" y="50" font-size="12" font-weight="bold" fill="currentColor">puts@plt</text><text x="318" y="50" font-size="12" text-anchor="end" fill="currentColor">0x401030</text><text x="22" y="72" font-size="11" fill="currentColor">jmp [0x404000]</text><rect x="10" y="100" width="320" height="57" rx="5" fill="#d97706" fill-opacity=".1" stroke="#d97706" /><text x="22" y="121" font-size="12" font-weight="bold" fill="currentColor">puts@got</text><text x="318" y="121" font-size="12" text-anchor="end" fill="currentColor">0x404000</text><text x="22" y="143" font-size="11" fill="currentColor">저장된 값: 0x7ffff7e12340</text><path d="M170 86V99 M170 157V176" stroke="currentColor" stroke-width="1.5" /><rect x="10" y="177" width="320" height="35" rx="5" fill="#16a34a" fill-opacity=".1" stroke="#16a34a" /><text x="22" y="199" font-size="12" font-weight="bold" fill="currentColor">libc puts()</text><text x="318" y="199" font-size="12" text-anchor="end" fill="currentColor">0x7ffff7e12340</text></svg>
```

주소는 이해를 위한 예시이며 실제 실행 환경과는 다를 수 있어.

이 예시에서 다음 세 가지는 서로 다른 값이야.

```python
elf.plt['puts']  # 0x401030
elf.got['puts']  # 0x404000

# 실행 중인 GOT에 저장된 값
# 0x7ffff7e12340
```

`elf.got['puts']`가 반환하는 것은 libc의 실제 `puts()` 주소가 아니라, 그 주소를 저장하는 GOT 엔트리의 주소야.

### 1-4. Lazy Binding

외부 함수의 실제 주소를 처음 호출할 때 연결하는 방식을 Lazy Binding이라고 해.

**Lazy Binding 동작 시뮬레이션**

- 최초 호출 전
- 최초 호출 후

전통적인 x86-64 PLT 및 Lazy Binding 구조를 단순화한 예시야. 즉시 바인딩 환경에서는 시작할 때 주소가 연결될 수 있어.

---

## 2. 실습 — pwntools로 GOT와 PLT 분석 (35분)

### Step 1. 실습용 바이너리 만들기 (5분)

`chall07.c` 파일을 작성해.

```c

#include <stdio.h>
#include <unistd.h>

int main(void) {
    char buf[32];

    puts("Welcome to Day 7!");

    printf("PID: %d\n", getpid());

    write(1, "Input: ", 7);
    read(0, buf, sizeof(buf));

    puts("Done!");

    return 0;
}
```

컴파일\:

```bash
gcc -O0 -g -no-pie -Wl,-z,lazy chall07.c -o chall07
```

실행\:

```bash
./chall07
```

예상 출력\:

```text
Welcome to Day 7!
PID: 12345
Input: hello
Done!
```

`-Wl,-z,lazy`는 링커에 Lazy Binding을 요청하는 옵션이야. 이번 실습은 직접 컴파일한 x86-64 Linux 바이너리를 기준으로 진행해.

### Step 2. GOT와 PLT 주소 추출 (5분)

`day7.py` 파일을 작성해.

```python

from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf

functions = ['puts', 'printf', 'read', 'write']

for name in functions:
    print(f"\nFunction: {name}")
    print(f"PLT: {elf.plt[name]:#x}")
    print(f"GOT: {elf.got[name]:#x}")
```

실행\:

```bash
python3 day7.py
```

예상 출력 예시\:

```text
Function: puts
PLT: 0x401030
GOT: 0x404000

Function: printf
PLT: 0x401050
GOT: 0x404010
```

실제 주소는 컴파일러와 링커 환경에 따라 달라져.

### Step 3. symbols, PLT, GOT 비교 (5분)

```python
from pwn import *

elf = ELF('./chall07', checksec=False)

print(f"symbols: {elf.symbols['puts']:#x}")
print(f"plt:     {elf.plt['puts']:#x}")
print(f"got:     {elf.got['puts']:#x}")

print(elf.symbols['puts'] == elf.plt['puts'])
print(elf.plt['puts'] == elf.got['puts'])
```

일반적인 이번 실습 바이너리에서는 다음 결과를 예상할 수 있어.

```text
symbols: 0x401030
plt:     0x401030
got:     0x404000
True
False
```

pwntools는 PLT와 GOT 정보를 이용해 합성 심볼(synthetic symbol)을 추가해. 따라서 이번처럼 외부 함수의 `elf.symbols['puts']`가 PLT 주소를 가리킬 수 있어.

다만 모든 바이너리에서 반드시 동일하다고 가정하면 안 돼. 원하는 주소를 명확하게 지정하는 습관을 들이는 게 좋아.

### Step 4. PLT 내부 기계어 분석 (10분)

이번에는 새로운 함수인 `elf.disasm()`을 사용해 보자.

```python

from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf

puts_plt = elf.plt['puts']
puts_got = elf.got['puts']

print(f"puts PLT: {puts_plt:#x}")
print(f"puts GOT: {puts_got:#x}")

print("\n[PLT disassembly]")
print(elf.disasm(puts_plt, 16))

print("\n[GOT raw data]")
raw = elf.read(puts_got, 8)

print(raw)
print(raw.hex(' '))
print(f"Stored address: {u64(raw):#x}")
```

전통적인 PLT 구조에서는 다음과 비슷한 명령어를 확인할 수 있어.

```asm
401030: jmp QWORD PTR [rip+0x2fca]
401036: push 0x0
40103b: jmp 0x401020
```

첫 번째 명령어가 중요해.

```asm
jmp QWORD PTR [rip+0x2fca]
```

x86-64의 RIP 상대 주소 지정 방식을 사용해 GOT에 저장된 8바이트 주소를 참조하고, 그 주소로 이동하는 명령어야.

**RIP 상대 주소 계산**

현재 명령어 주소 `0x401030`

명령어 길이 `6 bytes`

다음 명령어 주소 (RIP) `0x401036`

Displacement `0x2fca`

---

$$
\text{GOT} = \text{RIP} + \text{displacement}
$$

`0x401036 + 0x2fca`

# 0x404000

puts\@got 주소

직접 값을 변경하면서 계산해 봐.

**RIP 상대 주소 계산기**

다음 명령어 주소 (RIP)


Displacement (16진수)


---

계산된 참조 주소

[초기화]

실제 디스어셈블 결과는 CET, 링커 설정 등에 따라 예시와 다를 수 있어.

### Step 5. 실행 전후 GOT 데이터 비교 (10분)

Day 6에서 `elf.read()`는 실행 중인 프로세스의 메모리를 읽는 함수가 아니라고 배웠지.

이번에는 직접 만든 로컬 프로세스의 메모리를 읽는 `p.readmem()`과 비교해 보자.

```python

from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf
context.log_level = 'error'

got_addr = elf.got['puts']

# ELF 파일에 저장된 데이터
file_raw = elf.read(got_addr, 8)
file_value = u64(file_raw)

p = process(elf.path)

try:
    # puts() 호출 이후까지 대기
    p.recvuntil(b'Input: ')

    # 실행 중인 로컬 프로세스의 메모리
    runtime_raw = p.readmem(got_addr, 8)
    runtime_value = u64(runtime_raw)

    print(f"GOT address:    {got_addr:#x}")
    print(f"File value:     {file_value:#x}")
    print(f"Runtime value:  {runtime_value:#x}")

    print(f"File bytes:     {file_raw.hex(' ')}")
    print(f"Runtime bytes:  {runtime_raw.hex(' ')}")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()
```

예상 출력 예시\:

```text
GOT address:    0x404000
File value:     0x401036
Runtime value:  0x7ffff7e12340
File bytes:     36 10 40 00 00 00 00 00
Runtime bytes:  40 23 e1 f7 ff 7f 00 00
Done!
```

**같은 GOT 주소, 서로 다른 데이터**

GOT 엔트리 주소: 0x404000

ELF 파일 내부 데이터

`u64(file_raw)` → `0x401036`

---

실행 중인 프로세스의 데이터

`u64(runtime_raw)` → `0x7ffff7e12340`

동적 링킹으로 인해 실행 중인 GOT에 저장된 값이 달라질 수 있어.

참고로 `p.readmem()`은 로컬 프로세스의 메모리를 읽는 기능이야. Linux의 프로세스 메모리 접근 권한과 pwntools 버전에 따라 제한될 수 있으며, `remote()` 연결에 그대로 사용할 수 있는 기능은 아니야.

---

## 3. 직접 풀 실습 과제

**Day 7 과제 — GOT·PLT 자동 분석기 만들기**

앞에서 컴파일한 `chall07`을 대상으로 `day7_task.py`를 작성해 봐.

| 과제 | 요구사항 |
|--------|--------|
| TODO 1 | ELF 파일 불러오기 |
| TODO 2 | `puts`, `printf`, `read`, `write`의 GOT와 PLT 주소를 반복문으로 출력 |
| TODO 3 | `puts`의 GOT와 PLT 주소가 서로 다른지 assert 검증 |
| TODO 4 | `puts@plt`에서 16바이트를 디스어셈블 |
| TODO 5 | `puts@got`에 저장된 파일 데이터를 8바이트 읽고 정수로 변환 |
| TODO 6 | 프로세스 실행 후 `puts@got`의 실제 메모리 데이터 읽기 |
| TODO 7 | 파일 데이터와 실행 중 데이터를 비교하고 차이 설명 |

### 과제용 코드

```python

from pwn import *

# TODO 1: Load ELF

functions = ['puts', 'printf', 'read', 'write']

# TODO 2: Print GOT and PLT addresses

# TODO 3: Assert GOT != PLT

# TODO 4: Disassemble puts@plt

# TODO 5: Read GOT data from ELF file

# TODO 6: Read GOT data from running process

# TODO 7: Compare file and runtime values

print("Analysis complete!")
```

**추가 도전 과제**

`puts@got`뿐만 아니라 `printf@got`, `read@got`, `write@got`의 실행 중 메모리 데이터도 반복문을 사용해 출력해 봐.

이번에는 주소와 저장된 값을 구분해서 변수명을 작성하는 것을 추천해.

```python
got_addr = ...
got_raw = ...
got_value = ...
```

이렇게 작성하면 나중에 익스플로잇 코드에서 주소와 실제 데이터를 혼동하는 실수를 줄일 수 있어.

---

## 4. 정리 — 이해도 확인 (10분)

**Day 7 확인 퀴즈** /5 응답

### 마지막 심화 문제

다음과 같은 상황을 가정해 보자.

```python
puts_plt = 0x401030
puts_got = 0x404000

raw = b'\x40\x23\xe1\xf7\xff\x7f\x00\x00'
value = u64(raw)
```

`raw`는 실행 중인 프로세스의 `puts@got`에서 읽은 8바이트 데이터야.

아래 코드의 결과를 각각 예상해 봐.

```python
print(hex(value))             # 문제 1
print(len(p64(puts_got)))     # 문제 2

assert value == puts_got      # 문제 3
assert u64(p64(value)) == value  # 문제 4
```

문제 3과 문제 4의 `assert`는 각각 독립적으로 실행한다고 가정해. 결과뿐만 아니라 왜 그런 결과가 나오는지도 설명해 봐.

## 5. 오늘의 핵심 암기

| 코드 | 의미 |
|--------|--------|
| `elf.plt['puts']` | 함수 호출 중계 코드 주소 |
| `elf.got['puts']` | 함수 주소를 저장하는 공간의 주소 |
| `elf.read(got_addr, 8)` | ELF 파일 기준 GOT 데이터 |
| `p.readmem(got_addr, 8)` | 실행 중인 로컬 프로세스의 GOT 데이터 |
| `u64(raw)` | 8바이트 데이터를 정수로 변환 |
| `elf.disasm(addr, 16)` | 해당 주소부터 16바이트 디스어셈블 |

오늘 예제는 직접 컴파일하는 실습용 바이너리를 기준으로 작성했으며, 실제 실행 검증은 하지 않았어. 주소나 디스어셈블 결과가 예시와 다르더라도 개념을 중심으로 비교하면 돼.

## 전체 학습 진도

# 7 / 20회

35% 차시 도달

**다음 Day 8 예고 — 스택(Stack)과 함수 호출 구조**

다음 시간에는 RSP, RBP, RIP 레지스터와 `push`, `pop`, `call`, `ret` 명령어를 공부할 거야. 함수가 호출될 때 반환 주소가 어디에 저장되는지 이해하고, 이후 Stack Buffer Overflow 실습을 준비할 예정이야.

---

# you asked

message time: 2026-11-26 01:03:38

from pwn import *

# TODO 1: Load ELF

elf = ELF('./chall07', checksec=False)
context.binary = elf

functions = ['puts', 'printf', 'read', 'write']

# TODO 2: Print GOT and PLT addresses

for name in functions:
    print(f"elf.plt[{name}]: {elf.plt[name]:#x}")
    print(f"elf.got[{name}]: {elf.got[name]:#x}")

# TODO 3: Assert GOT != PLT

assert elf.plt['puts'] != elf.got['puts']

# TODO 4: Disassemble puts@plt

puts_plt = elf.plt['puts']
print(f"{elf.disasm(puts_plt, 16)}")

# TODO 5: Read GOT data from ELF file
puts_got = elf.got['puts']
print(f"GOT Data from ELF: {u64(elf.read(puts_got, 8)):#x}")

# TODO 6: Read GOT data from running process
p = process("./chall07")
print(f"GOT Data from RUNTIME: {u64(p.readmem(puts_got, 8)):#x}")

# TODO 7: Compare file and runtime values

print(f"{elf.read(puts_got, 8) == p.readmem(puts_got, 8)}")

print("Analysis complete!")

# Additional Challenge

for name in functions :
    got_addr = elf.got[name]
    got_raw = p.readmem(got_addr, 8)
    got_value = u64(got_raw)

    print(f"{name}'s got_addr:{got_addr:#x}")
    print(f"{name}'s got_raw:{got_raw}")
    print(f"{name}'s got_value:{got_value:#x}")
 
#심화 문제
0x7ffff7e12340
8 // p64는 8byte의 결과값이 반환되므로
False // 0x404000 != 0x7ffff7e12340
True // int인 value 를 byte로 바꾼뒤 int로 바꿨으니 동일할 것

---

# chatgpt response

Day 7 과제 잘 풀었어\! 특히 추가 도전 과제까지 구현했고, **심화 문제도 4문제 모두 정답**이야.

다만 실습 코드에서 프로세스 실행 시점과 관련된 중요한 문제가 하나 있어. 앞으로 익스플로잇 코드를 작성할 때도 주의해야 하는 부분이야.

## 1. 실습 과제 코드 리뷰

| 과제 | 평가 | 설명 |
|--------|--------|--------|
| TODO 1 | 정답 | ELF 및 context 설정 |
| TODO 2 | 정답 | 반복문으로 GOT·PLT 추출 |
| TODO 3 | 정답 | 주소 비교 |
| TODO 4 | 정답 | PLT 디스어셈블 |
| TODO 5 | 정답 | ELF 데이터 읽기 및 변환 |
| TODO 6 | 개선 필요 | 프로세스 실행 시점 동기화 |
| TODO 7 | 정답 | 바이트 데이터 비교 |
| 추가 과제 | 정답 | 반복문으로 GOT 데이터 분석 |

실제 바이너리를 실행하지 않고 제출한 코드와 실습용 C 소스코드를 기준으로 검토했어.

## 2. 중요한 수정 사항 — 프로세스 동기화

작성한 코드에서 다음 부분을 보자.

```python
p = process("./chall07")
print(f"GOT Data from RUNTIME: {u64(p.readmem(puts_got, 8)):#x}")
```

`process()`로 프로그램을 실행했다고 해서 반드시 `puts()`까지 실행된 상태라는 보장은 없어.

Python 코드와 C 프로그램이 별개의 프로세스로 실행되기 때문이야.

**현재 코드의 실행 흐름**

발생 가능한 실행 순서의 예시야. 실제 순서는 프로세스 스케줄링에 따라 달라져.

이 상태에서는 `puts()`가 호출되기 전에 GOT 데이터를 읽을 가능성이 있어.

이러한 실행 타이밍 의존성을 없애기 위해 다음 코드를 추가하면 돼.

```python
p = process("./chall07")
p.recvuntil(b'Input: ')

runtime_raw = p.readmem(puts_got, 8)
runtime_value = u64(runtime_raw)

print(f"GOT Data from RUNTIME: {runtime_value:#x}")
```

**수정된 코드의 실행 흐름**

Input: 메시지를 수신한 이후에는 앞선 puts() 호출이 완료된 상태임을 알 수 있어.

Day 2에서 배운 `recvuntil()`이 단순히 데이터를 수신하는 것뿐만 아니라 **프로그램의 실행 시점을 동기화하는 역할**도 하는 거야.

## 3. 추가 도전 과제에서 주의할 점

네가 작성한 다음 코드는 정확해.

```python
for name in functions:
    got_addr = elf.got[name]
    got_raw = p.readmem(got_addr, 8)
    got_value = u64(got_raw)

    print(f"{name}'s got_addr:{got_addr:#x}")
    print(f"{name}'s got_raw:{got_raw}")
    print(f"{name}'s got_value:{got_value:#x}")
```

특히 변수명을 구분한 점이 좋아.

| 변수 | 자료형 | 의미 |
|--------|--------|--------|
| `got_addr` | `int` | GOT 엔트리의 주소 |
| `got_raw` | `bytes` | GOT에 저장된 8바이트 |
| `got_value` | `int` | GOT에 저장된 주소 값 |

다만 분석이 끝난 후에는 Day 5에서 배운 `p.close()`를 호출하는 습관을 들이자.

## 4. 개선된 전체 코드

네 코드의 구조를 유지하면서 실행 동기화, 중복 메모리 읽기 제거, 프로세스 종료 처리를 추가했어.

```python

from pwn import *

elf = ELF('./chall07', checksec=False)
context.binary = elf

functions = ['puts', 'printf', 'read', 'write']

# TODO 2
for name in functions:
    print(f"elf.plt[{name}]: {elf.plt[name]:#x}")
    print(f"elf.got[{name}]: {elf.got[name]:#x}")

# TODO 3
puts_plt = elf.plt['puts']
puts_got = elf.got['puts']

assert puts_plt != puts_got

# TODO 4
print(elf.disasm(puts_plt, 16))

# TODO 5
file_raw = elf.read(puts_got, 8)
file_value = u64(file_raw)

print(f"GOT Data from ELF: {file_value:#x}")

p = process(elf.path)

try:
    # Synchronization
    p.recvuntil(b'Input: ')

    # TODO 6
    runtime_raw = p.readmem(puts_got, 8)
    runtime_value = u64(runtime_raw)

    print(f"GOT Data from RUNTIME: {runtime_value:#x}")

    # TODO 7
    print(f"Same data: {file_raw == runtime_raw}")

    # Additional Challenge
    for name in functions:
        got_addr = elf.got[name]
        got_raw = p.readmem(got_addr, 8)
        got_value = u64(got_raw)

        print(f"\nFunction: {name}")
        print(f"GOT address: {got_addr:#x}")
        print(f"GOT raw:     {got_raw.hex(' ')}")
        print(f"GOT value:   {got_value:#x}")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()

print("Analysis complete!")
```

## 5. 심화 문제 채점

심화 문제 점수

# 4 / 4

모든 문제 정답

---

문제 3에서 설명한 다음 내용이 특히 중요해.

```python
0x404000 != 0x7ffff7e12340
```

GOT 엔트리 자체의 주소와 GOT에 저장된 실제 함수 주소를 정확하게 구분했어.

문제 4 역시 정확해.

```python
u64(p64(value)) == value
```

64비트 범위 내의 정수를 동일한 엔디언 설정으로 패킹하고 언패킹했기 때문에 원래 값으로 복원돼.

## 6. Day 7 마지막 확인 문제

이번에는 GOT와 PLT의 차이를 완전히 이해했는지 확인해 보자.

다음과 같은 상황을 가정할게.

```python
puts_plt = 0x401030
puts_got = 0x404000

# 실행 중인 GOT에 저장된 값
puts_value = 0x7ffff7e12340
```

CPU가 다음 명령어를 실행한다고 가정하자.

```asm
call 0x401030
```

그리고 `0x401030`에는 다음 명령어가 있어.

```asm
jmp QWORD PTR [0x404000]
```

**문제 1.** CPU가 최종적으로 이동하는 주소는 무엇일까?

**문제 2.** `jmp 0x404000`과 `jmp QWORD PTR [0x404000]`의 차이는 무엇일까?

**문제 3.** 위 상황에서 Lazy Binding이 완료된 이후 변경된 것은 PLT 주소, GOT 주소, GOT에 저장된 값 중 무엇일까?

**Day 7 — GOT와 PLT** (과제 통과)

# 7 / 20회

35%

실습 과제 통과 · 심화 문제 4/4 · 마지막 개념 복습 남음

이번 마지막 확인 문제는 어셈블리에서 **직접 주소 참조와 간접 주소 참조의 차이**를 이해하기 위한 문제야. 다음 Day 8의 스택과 레지스터 분석에서도 계속 활용할 개념이야.

---

# you asked

message time: 2026-11-26 01:09:28

1. 0X404000
2. 잘 모르겠음
3. GOT 에 저장된 값이 libc의 puts 주소 값으로 변경됨

---

# chatgpt response

3번은 정확해\! 1번과 2번은 같은 개념에서 헷갈린 것 같아. 이번에 **직접 참조와 간접 참조의 차이**를 확실하게 이해하고 넘어가자.

## 1. 정답 확인

| 문제 | 정답 | 평가 |
|--------|--------|--------|
| 1번 | `0x7ffff7e12340` | 오답 |
| 2번 | 직접 이동과 메모리 간접 참조의 차이 | 복습 필요 |
| 3번 | GOT에 저장된 값이 변경됨 | 정답 |

## 2. 직접 참조와 간접 참조

어셈블리에서 대괄호 `[]`의 의미가 중요해.

### 직접 이동

```asm
jmp 0x404000
```

CPU는 `0x404000` 주소로 직접 이동해.

### 간접 이동

```asm
jmp QWORD PTR [0x404000]
```

CPU는 `0x404000` 주소에 저장된 8바이트 값을 읽고, 그 값을 목적지 주소로 사용해 이동해.

직접 이동 — jmp 0x404000

```svg
<svg viewBox="0 0 340 135" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="40" width="105" height="48" rx="6" fill="#64748b" fill-opacity=".1" stroke="#64748b" /><text x="57" y="68" font-size="13" text-anchor="middle" fill="currentColor">CPU</text><path d="M110 64H180 M173 59L180 64L173 69" fill="none" stroke="#3b82f6" stroke-width="2" /><rect x="181" y="28" width="154" height="72" rx="6" fill="#3b82f6" fill-opacity=".1" stroke="#3b82f6" /><text x="258" y="48" font-size="12" font-weight="bold" text-anchor="middle" fill="currentColor">0x404000</text><path d="M181 58H335" stroke="#3b82f6" stroke-opacity=".5" /><text x="258" y="77" font-size="11" text-anchor="middle" fill="currentColor">0x7ffff7e12340</text><text x="258" y="91" font-size="9" text-anchor="middle" fill="currentColor">저장된 데이터</text><text x="170" y="123" font-size="11" text-anchor="middle" fill="#3b82f6">RIP = 0x404000</text></svg>
```

---

간접 이동 — jmp QWORD PTR $$0x404000$$

```svg
<svg viewBox="0 0 340 225" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="38" width="105" height="48" rx="6" fill="#64748b" fill-opacity=".1" stroke="#64748b" /><text x="57" y="66" font-size="13" text-anchor="middle" fill="currentColor">CPU</text><path d="M110 62H180 M173 57L180 62L173 67" stroke="#d97706" stroke-width="2" fill="none" /><text x="145" y="51" font-size="10" text-anchor="middle" fill="#d97706">읽기</text><rect x="181" y="25" width="154" height="75" rx="6" fill="#d97706" fill-opacity=".1" stroke="#d97706" /><text x="258" y="45" font-size="12" text-anchor="middle" font-weight="bold" fill="currentColor">0x404000</text><path d="M181 55H335" stroke="#d97706" stroke-opacity=".5" /><text x="258" y="77" font-size="11" text-anchor="middle" fill="currentColor">0x7ffff7e12340</text><path d="M258 100V143 M253 136L258 143L263 136" fill="none" stroke="#16a34a" stroke-width="2" /><text x="245" y="124" font-size="10" text-anchor="end" fill="#16a34a">저장된 주소로 이동</text><rect x="75" y="144" width="260" height="48" rx="6" fill="#16a34a" fill-opacity=".1" stroke="#16a34a" /><text x="205" y="163" font-size="12" font-weight="bold" text-anchor="middle" fill="currentColor">0x7ffff7e12340</text><text x="205" y="180" font-size="11" text-anchor="middle" fill="currentColor">libc puts()</text><text x="170" y="215" font-size="11" text-anchor="middle" fill="#16a34a">RIP = 0x7ffff7e12340</text></svg>
```

참고로 `QWORD`는 8바이트를 의미하고, `PTR`은 메모리 피연산자의 크기를 지정하는 표현이야.

## 3. C 언어의 포인터로 이해하기

C 언어의 포인터 역참조와 비슷한 개념이야.

```c
long value = 1234;
long *ptr = &value;

printf("%p\n", (void *)ptr);  // 변수의 주소
printf("%ld\n", *ptr);        // 주소에 저장된 값: 1234
```

| 구분 | C 언어 | 어셈블리 개념 |
|--------|--------|--------|
| 주소 자체 | `ptr` | `0x404000` |
| 주소에 저장된 값 | `*ptr` | `[0x404000]` |

## 4. 네가 작성한 pwntools 코드와 연결하기

오늘 제출한 추가 과제 코드를 다시 보자.

```python
got_addr = elf.got['puts']
got_raw = p.readmem(got_addr, 8)
got_value = u64(got_raw)
```

각각 다음과 같은 의미였어.

```python
got_addr  = 0x404000
got_value = 0x7ffff7e12340
```

어셈블리의 동작을 Python 의사 코드로 표현하면 다음과 같아.

```python
# jmp 0x404000
RIP = got_addr

# jmp QWORD PTR [0x404000]
RIP = u64(p.readmem(got_addr, 8))
```

이미 네가 실습에서 구현했던 메모리 읽기와 동일한 개념이야.

## 5. 직접 확인해 보는 시뮬레이션

**CPU 주소 이동 시뮬레이터**

GOT 주소: 0x404000

GOT에 저장된 주소 값

- 0x401036 $연결 전 예시$
- 0x7ffff7e12340 $연결 후 예시$
현재 선택된 항목을 확인할 수 없습니다.

jmp 0x404000

jmp QWORD PTR $$0x404000$$

---

명령어 실행 후 RIP

## 6. 마지막 재확인 문제

이번에는 조금 다른 주소를 사용해 볼게.

```text
메모리 주소       저장된 값
0x601000         0x401234
0x601008         0x401567
```

다음 명령어를 각각 독립적으로 실행했을 때 RIP에 저장되는 값은 무엇일까?

```asm
; 문제 1
jmp 0x601000

; 문제 2
jmp QWORD PTR [0x601000]

; 문제 3
jmp QWORD PTR [0x601008]
```

세 문제 모두 주소만 답해도 돼.

**대괄호가 없으면 주소 자체, 대괄호가 있으면 해당 메모리에 저장된 값.** 이번 문제에서는 이 원칙만 기억하면 돼.

**Day 7 — GOT와 PLT**

# 7 / 20회

35%

실습 통과 · 직접 참조와 간접 참조 복습 중

---

# you asked

message time: 2026-11-26 01:10:55

1. 0x601000
2. 0x401234
3. 0x401567

---

# chatgpt response

세 문제 모두 정답이야\! 이제 직접 이동과 간접 이동의 차이를 정확하게 이해했어.

## 채점 결과

| 명령어 | 실행 후 RIP | 결과 |
|--------|--------|--------|
| `jmp 0x601000` | `0x601000` |  |
| `jmp QWORD PTR [0x601000]` | `0x401234` |  |
| `jmp QWORD PTR [0x601008]` | `0x401567` |  |

## Day 7 핵심 개념 정리

오늘 배운 내용을 하나의 그림으로 정리하면 다음과 같아.

반드시 기억할 내용은 다음과 같아.

- **PLT\:** 외부 함수 호출을 중계하는 코드.
- **GOT\:** 외부 함수 주소를 저장하는 공간.
- **Lazy Binding\:** 최초 함수 호출 시 실제 함수 주소를 연결하는 방식.
- **직접 이동\:** 지정된 주소로 이동.
- **메모리 간접 이동\:** 지정된 주소에 저장된 값을 읽고 그 주소로 이동.
- **프로세스 동기화\:** `recvuntil()`을 활용해 원하는 실행 시점까지 대기.

**Day 7 — GOT와 PLT** (학습 완료)

---

# 7 / 20회

35%

## 다음 Day 8 예고 — 스택과 함수 호출 구조

다음 시간에는 아래 내용을 학습할 거야.

- RSP, RBP, RIP 레지스터
- 스택의 성장 방향
- `push`, `pop` 명령어
- `call`, `ret` 명령어
- Stack Frame과 Return Address
- pwntools를 활용한 스택 데이터 분석

오늘 배운 간접 참조 개념은 다음에 배울 `ret` 명령어를 이해하는 데도 도움이 돼.

이제 Day 7은 마무리하고 다음 차시로 넘어가면 돼.

---

# you asked

message time: 2026-11-26 01:30:20

질문, 함수 호출 전의 puts@got 에는 어떤 값이 들어가있다고 표현할 수 있어.

---

# chatgpt response

Lazy Binding이 적용된 일반적인 x86-64 ELF 바이너리에서는 `puts()` 최초 호출 전의 `puts@got`에 **동적 링커를 호출하기 위한 PLT 내부 명령어의 주소가 저장되어 있다**고 표현하면 돼.

## 1. 최초 호출 전

예를 들어 `puts@plt`의 디스어셈블 결과가 다음과 같다고 가정하자.

```asm
0x401030: jmp QWORD PTR [0x404000]
0x401036: push 0x0
0x40103b: jmp 0x401020
```

이때 `puts@got(0x404000)`에는 `0x401036`이 저장되어 있어.

```svg
<svg viewBox="0 0 340 280" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="15" y="5" width="310" height="52" rx="6" fill="#3b82f6" fill-opacity=".1" stroke="#3b82f6" /><text x="170" y="25" text-anchor="middle" font-size="12" font-weight="bold" fill="currentColor">puts@plt (0x401030)</text><text x="170" y="43" text-anchor="middle" font-size="11" fill="currentColor">jmp QWORD PTR [0x404000]</text><path d="M170 57V79 M165 73L170 79L175 73" stroke="currentColor" fill="none" /><rect x="15" y="80" width="310" height="52" rx="6" fill="#d97706" fill-opacity=".1" stroke="#d97706" /><text x="170" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="currentColor">puts@got (0x404000)</text><text x="170" y="119" text-anchor="middle" font-size="12" fill="#d97706">저장된 값: 0x401036</text><path d="M170 132V154 M165 148L170 154L175 148" stroke="currentColor" fill="none" /><rect x="15" y="155" width="310" height="52" rx="6" fill="#3b82f6" fill-opacity=".1" stroke="#3b82f6" /><text x="170" y="175" text-anchor="middle" font-size="12" font-weight="bold" fill="currentColor">PLT 내부 (0x401036)</text><text x="170" y="193" text-anchor="middle" font-size="11" fill="currentColor">push 0x0 → jmp 0x401020</text><path d="M170 207V229 M165 223L170 229L175 223" stroke="currentColor" fill="none" /><rect x="15" y="230" width="310" height="43" rx="6" fill="#16a34a" fill-opacity=".1" stroke="#16a34a" /><text x="170" y="248" text-anchor="middle" font-size="12" font-weight="bold" fill="currentColor">동적 링커 (Dynamic Linker)</text><text x="170" y="264" text-anchor="middle" font-size="10" fill="currentColor">libc puts의 실제 주소 탐색 및 연결</text></svg>
```

즉, 아직 libc의 실제 함수 주소를 모르기 때문에 PLT 내부의 주소를 저장해 두고, 최초 호출 시 동적 링커를 거쳐 실제 함수 주소를 알아내는 구조야.

## 2. 최초 호출 전후 비교

- 최초 호출 전
- 최초 호출 후
현재 선택된 항목을 확인할 수 없습니다.

**puts\@got**

엔트리 주소: 0x404000

---

저장된 값

## 3. 정확한 표현 정리

| 상태 | GOT에 저장된 값 |
|--------|--------|
| 최초 호출 전 | PLT 내부의 심볼 연결 처리 코드 주소 |
| 최초 호출 중 | 동적 링커가 실제 함수 주소를 탐색 |
| 최초 호출 후 | libc의 실제 함수 주소 |

주의할 점은 최초 호출 전 GOT에 **동적 링커의 주소가 직접 저장되어 있는 것은 아니라는 점**이야. 전통적인 PLT 구조에서는 동적 링커로 연결하기 위한 PLT 내부 코드의 주소가 저장돼.

또한 일반적인 PLT 구조에서는 다음 관계가 성립해.

```python
# 최초 호출 전 GOT에 저장된 값
puts_got_value = puts_plt + 6
```

다만 CET나 링커 설정에 따라 구조가 달라질 수 있으므로 항상 `+6`이라고 단정하면 안 돼. 즉시 바인딩(Binding Now)이 적용된 경우에는 최초 호출 전부터 실제 libc 함수 주소가 저장될 수도 있어.

**암기하기 좋은 표현\:**

> Lazy Binding에서 최초 호출 전의 GOT에는 심볼 주소를 해결하기 위한 PLT 내부 코드의 주소가 저장되고, 최초 호출 이후에는 실제 라이브러리 함수의 주소가 저장된다.

---