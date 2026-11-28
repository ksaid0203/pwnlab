# chatgpt response

# Day 8 — 스택(Stack)과 함수 호출 구조

(2주 차 · 8/20회) 2026년 11월 26일 목요일

지난 Day 7에서는 GOT, PLT, Lazy Binding과 직접·간접 주소 참조를 공부했어.

오늘은 함수가 호출될 때 CPU의 레지스터와 스택이 어떻게 변화하는지 알아볼 거야. 특히 **함수의 반환 주소(Return Address)가 어디에 저장되고 어떻게 사용되는지** 이해하는 것이 핵심 목표야.

이 개념을 이해해야 이후 Stack Buffer Overflow와 ret2win을 제대로 이해할 수 있어.

**오늘의 학습 구성**

이론 — 스택과 레지스터 **15분**

실습 — 함수 호출 및 스택 분석 **35분**

정리 — 실습 과제 및 이해도 확인 **10분**

---

**총 학습 시간**
**60분**

# 1. 이론 — 스택과 함수 호출 (15분)

## 1-1. 스택(Stack)이란?

스택은 프로그램이 실행되는 동안 함수의 지역 변수, 반환 주소, 저장된 레지스터 등을 관리하는 메모리 영역이야.

기본적으로 LIFO(Last In, First Out), 즉 마지막에 저장한 데이터를 먼저 꺼내는 구조야.

x86-64 환경에서 스택은 일반적으로 **높은 주소에서 낮은 주소 방향으로 성장해.**

64비트 데이터를 push하면 RSP가 8만큼 감소해.

## 1-2. 반드시 알아야 하는 레지스터

| 레지스터 | 전체 이름 | 역할 |
|--------|--------|--------|
| RSP | Stack Pointer | 현재 스택의 최상단 주소 |
| RBP | Base Pointer | 스택 프레임의 기준 주소로 사용 가능 |
| RIP | Instruction Pointer | 실행할 명령어의 주소 |
| RAX | Accumulator | 연산 결과 및 일반적인 함수 반환값 |
| RDI | Destination Index | Linux x86-64 함수의 첫 번째 정수·포인터 인자 |
| RSI | Source Index | 두 번째 정수·포인터 인자 |
| RDX | Data Register | 세 번째 정수·포인터 인자 |

오늘은 RSP, RBP, RIP에 집중하면 돼.

참고로 RBP는 컴파일러 최적화 설정에 따라 스택 프레임의 기준 주소로 사용되지 않을 수도 있어.

## 1-3. push와 pop

### push 명령어

```asm
push rax
```

64비트 레지스터를 대상으로 하는 위 명령어는 다음과 같은 동작을 수행해.

```python
# Python 의사 코드
RSP = RSP - 8
memory[RSP] = RAX
```

### pop 명령어

```asm
pop rbx
```

```python
# Python 의사 코드
RBX = memory[RSP]
RSP = RSP + 8
```

직접 아래 시뮬레이터로 스택의 변화를 확인해 봐.

**스택 동작 시뮬레이터**

RSP

저장된 데이터

## bytes

push할 값


[push] [pop]

높은 주소

낮은 주소

[초기화]

push할 때 RSP가 감소하고, pop할 때 RSP가 증가하는 것을 확인해 봐.

## 1-4. call과 ret

오늘 가장 중요한 부분이야.

다음과 같은 어셈블리 코드가 있다고 가정하자.

```asm
0x401150: call 0x401200
0x401155: mov eax, 0
```

`call`은 단순히 함수 주소로 이동하는 명령어가 아니야. 다음 명령어의 주소를 스택에 저장한 뒤 함수로 이동해.

```python
# call의 동작을 표현한 의사 코드

RSP -= 8
memory[RSP] = 0x401155
RIP = 0x401200
```

반대로 `ret`은 스택 최상단에 저장된 주소를 읽어서 RIP에 넣어.

```python
# ret의 동작을 표현한 의사 코드

RIP = memory[RSP]
RSP += 8
```

Day 7에서 공부한 메모리 간접 참조와 연결되는 부분이야.

**call과 ret 실행 시뮬레이터**

- 호출 전
- call 실행
- ret 실행

RIP

RSP

반환 주소가 저장되는 스택 위치

**0x7fffffffdff8**

## 1-5. Stack Frame 구조

일반적인 함수의 시작 부분(Function Prologue)은 다음과 같아.

```asm
push rbp
mov rbp, rsp
sub rsp, 0x20
```

함수 종료 부분(Function Epilogue)은 다음과 같을 수 있어.

```asm
leave
ret
```

여기서 `leave`는 일반적인 64비트 환경에서 다음 동작과 같아.

```asm
mov rsp, rbp
pop rbp
```

**일반적인 Stack Frame 구조**

프레임 포인터를 사용하는 전형적인 함수의 예시야. 실제 지역 변수의 배치는 컴파일러에 따라 달라져.

이러한 스택 프레임에서는 다음 관계가 성립해.

| 위치 | 저장된 데이터 |
|--------|--------|
| `[rbp + 8]` | 반환 주소 |
| `[rbp]` | 이전 함수의 RBP |
| `[rbp - 8]` 등 | 지역 변수 또는 기타 프레임 데이터 |

여기서 `[rbp + 8]`은 주소 자체가 아니라 해당 주소에 저장된 데이터를 의미해.

---

# 2. 실습 — pwntools를 이용한 스택 분석 (35분)

## Step 1. 실습용 바이너리 만들기 (5분)

`chall08.c` 파일을 작성해.

```c

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

__attribute__((noinline))
void inspect_stack(void) {
    volatile uint64_t marker = 0x1122334455667788;
    char buf[32] = "STACK_TEST";

    void *rbp = __builtin_frame_address(0);
    void *ret = __builtin_return_address(0);

    printf("RBP: %p\n", rbp);
    printf("BUF: %p\n", (void *)buf);
    printf("MARKER: %p\n", (void *)&marker);
    printf("RET: %p\n", ret);

    printf("Input: ");
    fflush(stdout);

    read(0, buf, sizeof(buf));
}

int main(void) {
    inspect_stack();
    puts("Returned to main!");
    return 0;
}
```

컴파일\:

```bash
gcc -O0 -g -no-pie -fno-omit-frame-pointer chall08.c -o chall08
```

실행\:

```bash
./chall08
```

예상 출력 예시\:

```text
RBP: 0x7fffffffdfe0
BUF: 0x7fffffffdfa0
MARKER: 0x7fffffffdfc8
RET: 0x401234
Input:
```

실제 주소는 실행 환경과 컴파일러에 따라 달라질 수 있어.

이번 실습에서는 버퍼 크기 이내로만 입력을 받고, 스택 보호 기법도 별도로 비활성화하지 않았어. 오늘의 목적은 메모리 구조를 관찰하는 것이야.

## Step 2. 함수의 어셈블리 분석 (5분)

Day 7에서 배운 `elf.disasm()`을 활용해 보자.

```python

from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

func = elf.functions['inspect_stack']

print(f"Function address: {func.address:#x}")
print(f"Function size: {func.size}")

print(elf.disasm(func.address, func.size))
```

디스어셈블 결과에서 다음 명령어들을 찾아봐.

```asm
push rbp
mov rbp, rsp
sub rsp, ...
```

그리고 함수 마지막 부분에서 다음 명령어도 찾아봐.

```asm
leave
ret
```

이번에는 `elf.functions`를 사용해서 함수의 주소뿐만 아니라 함수 크기까지 가져왔어.

## Step 3. 스택 주소 자동 수집 (5분)

C 프로그램이 출력하는 주소들을 pwntools로 수집해 보자.

```python

from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), 16)

p = process(elf.path)

try:
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker = recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    p.recvuntil(b'Input: ')

    print(f"RBP:    {rbp:#x}")
    print(f"BUF:    {buf:#x}")
    print(f"MARKER: {marker:#x}")
    print(f"RET:    {ret:#x}")

    print(f"RBP - BUF: {rbp - buf:#x}")
    print(f"RBP - MARKER: {rbp - marker:#x}")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()
```

새롭게 사용한 부분은 다음 코드야.

```python
int(p.recvline().strip(), 16)
```

`b'0x7fffffffdfe0'`처럼 16진수 문자열로 전달된 데이터를 정수 주소로 변환해.

Day 5에서 숫자 문자열을 `int()`로 변환했던 것과 같은 원리야.

## Step 4. 실제 스택 메모리 읽기 (10분)

Day 7에서 배운 `p.readmem()`을 활용해서 이번에는 GOT가 아닌 스택을 읽어보자.

```python

from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), 16)

p = process(elf.path)

try:
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker = recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    p.recvuntil(b'Input: ')

    # 지역 변수 읽기
    marker_raw = p.readmem(marker, 8)
    marker_value = u64(marker_raw)

    print(f"Marker raw: {marker_raw.hex(' ')}")
    print(f"Marker value: {marker_value:#x}")

    # 버퍼 읽기
    buf_raw = p.readmem(buf, 32)
    print(f"Buffer: {buf_raw}")

    # 이전 RBP 읽기
    saved_rbp = u64(p.readmem(rbp, 8))
    print(f"Saved RBP: {saved_rbp:#x}")

    # 반환 주소 읽기
    saved_ret = u64(p.readmem(rbp + 8, 8))
    print(f"Saved RET: {saved_ret:#x}")

    assert marker_value == 0x1122334455667788
    assert saved_ret == ret

    print("All tests passed!")

    p.sendline(b'hello')
    print(p.recvall().decode())

finally:
    p.close()
```

### marker의 메모리 구조

64비트 지역 변수 marker

# 0x1122334455667788

리틀 엔디언 방식으로 낮은 주소부터 저장된 바이트

---

`u64(p.readmem(marker, 8))`

**0x1122334455667788**

여기서 특히 중요한 코드는 다음 두 줄이야.

```python
saved_ret = u64(p.readmem(rbp + 8, 8))
assert saved_ret == ret
```

C 프로그램이 출력한 반환 주소와 실제 스택에 저장된 반환 주소가 일치하는지 검증하는 거야.

## Step 5. 스택 메모리 덤프 만들기 (10분)

이번에는 RBP 주변 메모리를 8바이트씩 읽어서 출력해 보자.

```python

from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

p = process(elf.path)

try:
    p.recvuntil(b'RBP: ')
    rbp = int(p.recvline().strip(), 16)

    p.recvuntil(b'Input: ')

    print("[ Stack Dump ]")

    for offset in range(-0x40, 0x18, 8):
        addr = rbp + offset

        raw = p.readmem(addr, 8)
        value = u64(raw)

        label = ""

        if offset == 0:
            label = "<-- Saved RBP"
        elif offset == 8:
            label = "<-- Return Address"

        print(
            f"{addr:#018x} "
            f"RBP{offset:+#06x} "
            f"{value:#018x} "
            f"{label}"
        )

    p.sendline(b'hello')
    p.recvall()

finally:
    p.close()
```

예상 출력 형식\:

```text
[ Stack Dump ]

0x00007fffffffdfa0 RBP-0x040 0x45545f4b43415453
0x00007fffffffdfa8 RBP-0x038 0x0000000000005453
...
0x00007fffffffdfc8 RBP-0x018 0x1122334455667788
...
0x00007fffffffdfe0 RBP+0x000 0x00007fffffffdff0 <-- Saved RBP
0x00007fffffffdfe8 RBP+0x008 0x0000000000401234 <-- Return Address
```

위 출력은 설명을 위한 예시이며 실제 변수의 위치는 달라질 수 있어.

추가로 다음 함수도 사용해 봐.

```python
raw = p.readmem(rbp - 0x40, 0x50)
print(hexdump(raw))
```

pwntools의 `hexdump()`는 바이트 데이터를 16진수와 ASCII 형태로 함께 보여줘서 메모리를 분석할 때 유용해. 프로세스를 종료하기 전에 실행해야 해.

---

# 3. 직접 풀 실습 과제

**Day 8 과제 — Stack Frame 자동 분석기 만들기**

앞에서 컴파일한 `chall08`을 대상으로 `day8_task.py`를 작성해 봐.

| 과제 | 요구사항 |
|--------|--------|
| TODO 1 | ELF를 불러오고 `context.binary` 설정 |
| TODO 2 | `inspect_stack` 함수의 디스어셈블 결과 출력 |
| TODO 3 | 프로세스에서 RBP, BUF, MARKER, RET 주소 수집 |
| TODO 4 | `Input: `까지 수신하여 실행 시점 동기화 |
| TODO 5 | marker의 실제 데이터를 읽고 정수 변환 및 검증 |
| TODO 6 | Saved RBP와 Return Address 읽기 |
| TODO 7 | 실제 반환 주소와 출력된 RET 주소가 같은지 검증 |
| TODO 8 | RBP 기준 스택 메모리를 8바이트씩 출력 |
| TODO 9 | 정상 입력 전송 및 프로세스 종료 |

## 과제용 코드

```python

from pwn import *

# TODO 1: Load ELF

# TODO 2: Disassemble inspect_stack

def recv_addr(p, label):
    # TODO: Receive hexadecimal address
    pass

p = process('./chall08')

try:
    # TODO 3: Receive stack addresses

    # TODO 4: Synchronize process

    # TODO 5: Read and verify marker

    # TODO 6: Read saved RBP and RET

    # TODO 7: Verify return address

    # TODO 8: Dump stack memory

    # TODO 9: Send input and receive result

    print("Analysis complete!")

finally:
    p.close()
```

## 추가 도전 과제 — ASLR 관찰

동일한 바이너리를 세 번 실행해서 다음 주소들을 비교해 봐.

```python
for i in range(3):
    # 프로세스 실행
    # RBP 주소 수신
    # BUF 주소 수신
    # RET 주소 수신
    # 주소 및 상대 거리 출력
    # 프로세스 종료
    pass
```

비교할 항목은 다음과 같아.

| 항목 | 실행할 때마다 변경될까? |
|--------|--------|
| RBP 주소 | 직접 확인 |
| BUF 주소 | 직접 확인 |
| RET 주소 | 직접 확인 |
| RBP - BUF | 직접 확인 |
| inspect\_stack 함수 주소 | 직접 확인 |

ASLR이 활성화된 일반적인 Linux 환경과 오늘의 No PIE 바이너리를 기준으로 결과를 예상해 봐.

이 과제는 나중에 libc 베이스 주소를 계산할 때 도움이 될 거야.

---

# 4. 정리 — 이해도 확인 (10분)

**Day 8 확인 퀴즈** /5 응답

## 마지막 심화 문제

CPU의 현재 상태가 다음과 같다고 가정하자.

```text
RSP = 0x7fffffffe000
RBP = 0x7fffffffe100
RAX = 0x12345678
```

다음 명령어를 순서대로 실행할 거야.

```asm
push rax
push rbp
pop rbx
pop rcx
```

**초기 스택 상태**

다음 여섯 가지를 답해 봐.

1. `push rax` 실행 직후 RSP 값
2. `push rbp` 실행 직후 RSP 값
3. `pop rbx` 실행 직후 RBX 값
4. `pop rcx` 실행 직후 RCX 값
5. 모든 명령어 실행 후 RSP 값
6. 모든 명령어 실행 후 RBP 값

이번에도 정답은 미리 제공하지 않을게. 실습 과제 코드와 함께 제출하면 검토해 줄게.

# 5. 오늘의 핵심 암기

| 명령어 | 핵심 동작 |
|--------|--------|
| `push rax` | RSP 감소 후 RAX 저장 |
| `pop rax` | 스택 데이터 읽은 후 RSP 증가 |
| `call addr` | 반환 주소 저장 후 함수로 이동 |
| `ret` | 스택에 저장된 반환 주소로 이동 |
| `push rbp` | 이전 RBP 저장 |
| `mov rbp, rsp` | 현재 프레임 기준 설정 |
| `sub rsp, size` | 스택 공간 확보 |
| `leave` | 스택 프레임 정리 |

**RSP는 주소이고, `[RSP]`는 해당 주소에 저장된 데이터라는 점을 반드시 구분해야 해.** 지난 시간에 공부한 GOT 주소와 GOT에 저장된 값의 관계와 동일한 원리야.

오늘 예제는 x86-64 Linux와 GCC 환경을 기준으로 작성했어. 실제 컴파일 및 실행 검증은 하지 않았으며, 스택 배치나 주소는 환경에 따라 달라질 수 있어.

---

## 전체 학습 진도

# 8 / 20회

40% 차시 도달

**다음 Day 9 예고 — Stack Buffer Overflow의 원리**

다음 시간에는 배열의 크기를 초과하는 입력이 왜 문제가 되는지, 버퍼의 경계와 인접한 스택 데이터의 관계, 메모리 손상과 Stack Canary의 역할을 직접 만든 실습용 바이너리를 통해 공부할 거야.

오늘은 특히 `call`, `ret`, `RBP`, `RSP`의 관계를 충분히 이해하고 넘어가도록 하자.

---

# you asked

message time: 2026-11-27 14:28:45

# 실습 과제

```python
from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall08', checksec=False)
context.binary = elf

# TODO 2: Disassemble inspect_stack
disasm = elf.disasm(elf.symbols['inspect_stack'], 0x100)
print("[ Disassembly of inspect_stack ]")
print(disasm)

def recv_addr(p, label):
    # TODO: Receive hexadecimal address
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), 16)

p = process('./chall08')

try:
    # TODO 3: Receive stack addresses
    rbp = recv_addr(p, b'RBP')
    buf = recv_addr(p, b'BUF')
    marker = recv_addr(p, b'MARKER')
    ret = recv_addr(p, b'RET')

    print(f"RBP: {rbp:#x}")
    print(f"BUF: {buf:#x}")
    print(f"MARKER: {marker:#x}")
    print(f"RET: {ret:#x}")

    # TODO 4: Synchronize process
    p.recvuntil(b'Input: ')

    # TODO 5: Read and verify marker
    marker_addr = p.readmem(marker, 8)
    marker_value = u64(marker_addr)
    print(f"marker_value: {marker_value:#x}")

    assert marker_value == 0x1122334455667788

    # TODO 6: Read saved RBP and RET
    saved_rbp = u64(p.readmem(rbp, 8))
    return_addr = u64(p.readmem(rbp + 8, 8))

    print(f"Saved RBP: {saved_rbp:#x}")
    print(f"Return Address: {return_addr:#x}")

    # TODO 7: Verify return address
    assert return_addr == ret
    
    # TODO 8: Dump stack memory
    print("[ Stack Dump ]")

    for offset in range(-0x40, 0x18, 8):
        addr = rbp + offset

        raw = p.readmem(addr, 8)
        value = u64(raw)

        label = ""

        if offset == 0:
            label = "<-- Saved RBP"
        elif offset == 8:
            label = "<-- Return Address"

        print(
            f"{addr:#018x} "
            f"RBP{offset:+#06x} "
            f"{value:#018x} "
            f"{label}"
        )



    # TODO 9: Send input and receive result
    p.sendline(b'hello')
    print(p.recvall().decode())

    print("Analysis complete!")
    

finally:
    p.close()

```
# 추가 도전 과제

```python
from pwn import *

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int (p.recvline().strip(), 16)

elf = ELF('./chall08', checksec=False)
context.binary = elf

for i in range(3):
    # 프로세스 실행
    p = process('./chall08')

    # RBP 주소 수신
    rbp = recv_addr(p, b'RBP')

    # BUF 주소 수신
    buf = recv_addr(p, b'BUF')
    # RET 주소 수신
    ret = recv_addr(p, b'RET')

    # 주소 및 상대 거리 출력
    print(f'RBP: {rbp:016x}')
    print(f'BUF: {buf:016x}')
    print(f'RET: {ret:016x}')

    print(f"BUF - RBP: {buf - rbp}")

    print(elf.functions['inspect_stack'])
    # 프로세스 종료
    p.close()
```

확인 결과 RBP, BUF, RET 주소값은 실행 할 때 마다 달랐지만, 상대 거리 값은 항상 동일 했어.
inspect 함수 주소도 동일했는데 이 부분은 확신이 없어.

# 마지막 심화 문제

0x7fffffffdff8
0x7fffffffdff0
0x7fffffffe100
0x12345678
0x7fffffffe000
0x7fffffffe100

[push rax]
RSP -= 8
[e000] = 0x12345678

[push rbp]
RSP -= 8
[dff8] = 0x7fffffffe100

[pop rbx]
RSP += 8
rbx = 0x7fffffffe100

[pop rcx]
RSP += 8
rcx = 0x12345678

---

# chatgpt response

Day 8 실습 과제의 핵심 기능을 모두 구현했고, **심화 문제도 6문제 모두 정답이야.**

다만 추가 도전 과제에서 관찰한 RET 주소의 변화는 확인이 필요해. 그리고 심화 문제의 최종 답은 맞지만, 명령어별 메모리 저장 위치와 실행 순서에서 잘못된 부분이 있어.

## 1. 실습 과제 코드 리뷰

| 과제 | 평가 | 설명 |
|--------|--------|--------|
| TODO 1 | 정답 | ELF 및 context 설정 |
| TODO 2 | 개선 권장 | 디스어셈블 범위 지정 |
| TODO 3 | 정답 | 주소 수집 및 정수 변환 |
| TODO 4 | 정답 | 프로세스 동기화 |
| TODO 5 | 정답 | marker 데이터 검증 |
| TODO 6 | 정답 | Saved RBP, RET 추출 |
| TODO 7 | 정답 | 반환 주소 검증 |
| TODO 8 | 정답 | 스택 덤프 |
| TODO 9 | 정답 | 정상 입력 및 종료 |

실제 바이너리를 실행하지 않고 제출한 코드와 기존 C 소스코드를 기준으로 검토했어.

### TODO 2 — 디스어셈블 범위

네가 작성한 코드\:

```python
disasm = elf.disasm(elf.symbols['inspect_stack'], 0x100)
```

이 코드는 `inspect_stack` 함수의 시작 주소부터 256바이트를 디스어셈블해.

하지만 실제 함수의 크기가 256바이트보다 작으면 다른 함수까지 출력되고, 크다면 일부 명령어가 누락돼.

다음처럼 함수 크기를 자동으로 가져오는 것이 좋아.

```python
func = elf.functions['inspect_stack']

print(f"Function address: {func.address:#x}")
print(f"Function size: {func.size:#x}")

disasm = elf.disasm(func.address, func.size)
print(disasm)
```

| 코드 | 반환 정보 |
|--------|--------|
| `elf.symbols['inspect_stack']` | 정수형 심볼 주소 |
| `elf.functions['inspect_stack']` | 함수 정보 객체 |
| `func.address` | 함수 시작 주소 |
| `func.size` | 함수 크기 |

### TODO 5 — 변수명 개선

```python
marker_addr = p.readmem(marker, 8)
marker_value = u64(marker_addr)
```

실행 자체에는 문제가 없지만 `marker_addr`에는 주소가 아니라 바이트 데이터가 저장돼.

Day 7에서 사용했던 변수명 규칙을 적용해 보자.

```python
marker_addr = marker
marker_raw = p.readmem(marker_addr, 8)
marker_value = u64(marker_raw)

assert marker_value == 0x1122334455667788
```

marker\_addr (int)

**지역 변수의 메모리 주소**

p.readmem(marker\_addr, 8)

marker\_raw (bytes)

**88 77 66 55 44 33 22 11**

u64(marker\_raw)

marker\_value (int)

## 0x1122334455667788

주소, 바이트 데이터, 정수 값을 구분하는 습관은 계속 유지하자.

---

## 2. 추가 도전 과제 — ASLR 분석

네가 관찰한 결과와 예상 결과를 비교해 보자.

| 항목 | 네가 관찰한 결과 | No PIE + ASLR 환경의 예상 결과 |
|--------|--------|--------|
| RBP | 변경됨 | 변경됨 |
| BUF | 변경됨 | 변경됨 |
| RET | 변경됨 | **동일함** |
| BUF - RBP | 동일함 | 동일함 |
| inspect\_stack 주소 | 동일함 | 동일함 |

**RET 주소가 변경되었다는 부분을 다시 확인해야 해.**

### ASLR과 PIE의 차이

ASLR(Address Space Layout Randomization)은 프로그램 실행 시 메모리 영역의 배치를 무작위화하는 보안 기법이야.

PIE(Position Independent Executable)는 실행 파일 자체가 다양한 베이스 주소에 로딩될 수 있도록 하는 방식이야.

**ASLR 활성화 + No PIE 환경**

메모리 배치와 주소는 설명을 위한 예시야.

### 왜 RET 주소는 동일해야 할까?

우리가 작성한 C 코드에서는 `main()`이 `inspect_stack()`을 호출하고 있어.

```c
int main(void) {
    inspect_stack();
    puts("Returned to main!");
    return 0;
}
```

이를 어셈블리로 표현하면 다음과 비슷해.

```asm
0x401280: call inspect_stack
0x401285: lea rax, [...]
```

여기서 반환 주소는 `0x401285`야.

반환 주소가 **저장되는 위치는 스택이지만, 저장되는 값은 main 함수 내부의 코드 주소**라는 점이 중요해.

| 구분 | ASLR + No PIE |
|--------|--------|
| 반환 주소가 저장된 위치 (`rbp + 8`\) | 변경됨 |
| 반환 주소의 값 (`[rbp + 8]`\) | 동일함 |

지난 시간에 배운 GOT 주소와 GOT에 저장된 값의 차이와 같은 원리야.

### PIE 활성화 여부 확인하기

다음 코드를 실행해 봐.

```python
from pwn import *

elf = ELF('./chall08', checksec=False)

print(f"PIE: {elf.pie}")
print(f"ELF base: {elf.address:#x}")
print(f"inspect_stack: {elf.symbols['inspect_stack']:#x}")

print(elf.checksec())
```

만약 `elf.pie`가 `True`라면 RET 주소가 실행할 때마다 변경되는 현상을 설명할 수 있어.

### inspect\_stack 함수 주소가 동일했던 이유

네가 작성한 코드\:

```python
print(elf.functions['inspect_stack'])
```

이 코드는 실행 중인 프로세스의 함수 주소를 직접 확인하는 것이 아니라 ELF 객체의 함수 정보를 출력하는 코드야.

따라서 PIE가 활성화되어 있더라도 ELF 객체의 베이스 주소를 갱신하지 않았다면 동일한 값이 출력될 수 있어.

**ELF 객체에서 얻은 주소와 실제 프로세스에 로딩된 주소를 구분해야 해.**

### 추가 도전 과제 개선 코드

실행 중인 바이너리의 베이스 주소까지 비교하도록 작성해 봤어.

```python

from pwn import *

elf = ELF('./chall08', checksec=False)
context.binary = elf

def recv_addr(p, label):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), 16)

print(f"PIE: {elf.pie}")

for i in range(3):
    p = process(elf.path)

    try:
        rbp = recv_addr(p, b'RBP')
        buf = recv_addr(p, b'BUF')
        marker = recv_addr(p, b'MARKER')
        ret = recv_addr(p, b'RET')

        p.recvuntil(b'Input: ')

        runtime_base = p.libs()[elf.path]

        inspect_addr = (
            runtime_base
            + elf.symbols['inspect_stack']
            - elf.address
        )

        saved_ret = u64(p.readmem(rbp + 8, 8))

        print(f"\n[ Run {i + 1} ]")
        print(f"RBP:           {rbp:#x}")
        print(f"BUF:           {buf:#x}")
        print(f"RET slot:      {rbp + 8:#x}")
        print(f"RET value:     {saved_ret:#x}")
        print(f"RBP - BUF:     {rbp - buf:#x}")
        print(f"Runtime base:  {runtime_base:#x}")
        print(f"inspect_stack: {inspect_addr:#x}")

        assert saved_ret == ret

        p.sendline(b'hello')
        p.recvall()

    finally:
        p.close()
```

`p.libs()`는 실행 중인 로컬 프로세스에 매핑된 실행 파일과 라이브러리의 주소 정보를 가져오는 기능이야. 경로 표기가 환경에 따라 다르면 `p.libs()` 전체를 출력해서 키를 확인하면 돼.

---

## 3. 마지막 심화 문제 채점

심화 문제 점수

# 6 / 6

최종 레지스터 값 모두 정답

| 문제 | 네 답변 | 결과 |
|--------|--------|--------|
| push rax 이후 RSP | `0x7fffffffdff8` |  |
| push rbp 이후 RSP | `0x7fffffffdff0` |  |
| pop rbx 이후 RBX | `0x7fffffffe100` |  |
| pop rcx 이후 RCX | `0x12345678` |  |
| 최종 RSP | `0x7fffffffe000` |  |
| 최종 RBP | `0x7fffffffe100` |  |

하지만 작성한 풀이 과정에서는 메모리 저장 위치가 8바이트씩 어긋나 있어.

### push 명령어의 정확한 실행 순서

네 풀이\:

```python
# push rax
RSP -= 8
[e000] = 0x12345678
```

올바른 풀이\:

```python
# push rax
RSP -= 8
memory[RSP] = 0x12345678

# memory[0x7fffffffdff8] = 0x12345678
```

**push는 RSP를 먼저 감소시킨 후 데이터를 저장해.**

반대로 pop은 데이터를 먼저 읽고 RSP를 증가시켜.

```python
# pop rbx
RBX = memory[RSP]
RSP += 8
```

### 명령어별 스택 변화

아래에서 다음 명령어 버튼을 눌러 실행 순서를 확인해 봐.

/4 단계

RSP

높은 주소

낮은 주소

---

[이전] [다음 명령어]

[초기화]

참고로 pop을 실행해도 기존 메모리 데이터 자체가 지워지는 것은 아니야. RSP가 이동하면서 해당 영역이 현재 스택의 사용 범위에서 벗어나는 거야.

---

## 4. Day 8 마지막 확인 문제

이번에는 `leave`와 `ret`을 제대로 이해했는지 확인해 보자.

현재 레지스터 상태\:

```text
RBP = 0x7000
RSP = 0x6fe0
RIP = 0x401200
```

현재 메모리 상태\:

높은 주소

낮은 주소

다음 명령어를 순서대로 실행한다고 가정할게.

```asm
leave
ret
```

힌트\:

```asm
; leave
mov rsp, rbp
pop rbp

; ret
; [rsp]에 저장된 주소를 RIP로 가져오고
; RSP를 8 증가
```

다음 다섯 가지를 답해 봐.

1. `leave` 실행 직후 RSP 값
2. `leave` 실행 직후 RBP 값
3. `ret` 실행 직후 RIP 값
4. `ret` 실행 직후 RSP 값
5. `ret` 실행 직후 RBP 값

이 문제는 이후 함수 반환 과정과 Stack Buffer Overflow를 이해하는 데 매우 중요해.

## 전체 학습 진도

**Day 8 — 스택과 함수 호출** (실습 통과)

실습 과제 9/9 구현 완료

심화 문제 6/6 정답

ASLR 도전 과제 RET 주소 재확인 필요

---

# 8 / 20회

40%

마지막 개념 복습 진행 중

이번에는 특히 **push와 pop의 실행 순서, 반환 주소의 저장 위치와 저장된 값의 차이**를 확실히 기억하고 넘어가자.

---

# you asked

message time: 2026-11-27 14:50:12

환경은 문제 없었는데, RET 값은 동일했어 내가 잘못 본거였어.

마지막 문제 답
1. 0x7000
2. 0x7100
3. 0x401350
4. 0x7008
5. 0x7100

---

# chatgpt response

RET 값이 동일했다면 추가 도전 과제도 정상적으로 수행한 거야. No PIE 환경에서 ASLR에 의해 스택 주소는 변경되지만, `main()` 내부의 반환 주소는 고정된다는 것을 확인했네.

마지막 확인 문제는 **5문제 중 3문제 정답**이야.

## 1. 채점 결과

| 문제 | 네 답변 | 정답 | 결과 |
|--------|--------|--------|--------|
| leave 이후 RSP | `0x7000` | `0x7008` |  |
| leave 이후 RBP | `0x7100` | `0x7100` |  |
| ret 이후 RIP | `0x401350` | `0x401350` |  |
| ret 이후 RSP | `0x7008` | `0x7010` |  |
| ret 이후 RBP | `0x7100` | `0x7100` |  |

RBP와 RIP의 변화는 정확하게 이해했어. 다만 `leave` 내부의 `pop rbp`에서 RSP가 8 증가하는 것을 빠뜨렸어.

## 2. 명령어별 실행 과정

`leave`는 하나의 명령어지만 다음 두 명령어와 동일한 동작을 수행해.

```asm
mov rsp, rbp
pop rbp
```

Python 의사 코드로 표현하면 다음과 같아.

```python
# leave
RSP = RBP
RBP = memory[RSP]
RSP += 8

# ret
RIP = memory[RSP]
RSP += 8
```

아래 시뮬레이터를 통해 한 단계씩 확인해 봐.

/3 단계

---

높은 주소

낮은 주소

[이전] [다음 명령어]

[초기화]

## 3. 레지스터 변화 요약

| 명령어 | RSP | RBP | RIP |
|--------|--------|--------|--------|
| 초기 상태 | `0x6fe0` | `0x7000` | `0x401200` |
| `mov rsp, rbp` | `0x7000` | `0x7000` | — |
| `pop rbp` | `0x7008` | `0x7100` | — |
| `ret` | `0x7010` | `0x7100` | `0x401350` |

핵심은 **leave가 완료되는 순간 RSP는 반환 주소가 저장된 위치를 가리킨다**는 것이야. 이후 `ret`이 반환 주소를 읽고 RSP를 다시 8 증가시켜.

## 4. 마지막 재확인 문제

이번에는 힌트 없이 풀어보자.

```text
RBP = 0x8000
RSP = 0x7fc0

[0x8000] = 0x8100
[0x8008] = 0x401500
```

```asm
leave
ret
```

다음 값을 구해 봐.

1. `leave` 실행 직후 RSP
2. `leave` 실행 직후 RBP
3. `ret` 실행 직후 RIP
4. `ret` 실행 직후 RSP
5. `ret` 실행 직후 RBP

**Day 8 학습 현황**

---

# 8 / 20회

40%

이번 재확인 문제까지 맞히면 Day 8을 마무리하자. `leave`와 `ret`의 정확한 동작은 다음 차시인 BOF와 이후 ret2win을 이해하는 데 중요한 기반이야.

---

# you asked

message time: 2026-11-27 16:00:28

1. 0x8008
2. 0x8100
3. 0x401500
4. 0x8010
5. 0x8100

---

# chatgpt response

**5문제 모두 정답이야\!** 이제 `leave`와 `ret`에 따른 RSP, RBP, RIP의 변화를 정확하게 계산했어.

## 1. 채점 결과

| 문제 | 네 답변 | 결과 |
|--------|--------|--------|
| leave 이후 RSP | `0x8008` |  |
| leave 이후 RBP | `0x8100` |  |
| ret 이후 RIP | `0x401500` |  |
| ret 이후 RSP | `0x8010` |  |
| ret 이후 RBP | `0x8100` |  |

## 2. 최종 실행 과정 정리

앞으로 바이너리를 분석할 때 다음 의사 코드를 기억하면 돼.

```python
# push reg
RSP -= 8
memory[RSP] = reg

# pop reg
reg = memory[RSP]
RSP += 8

# leave
RSP = RBP
RBP = memory[RSP]
RSP += 8

# ret
RIP = memory[RSP]
RSP += 8
```

특히 **`leave`는 스택 프레임을 정리하고, `ret`은 스택에 저장된 반환 주소를 통해 실행 흐름을 변경한다.** 이 부분이 다음 차시의 핵심 기반이야.

## 3. Day 8 학습 완료

**Day 8 — 스택과 함수 호출** (학습 완료)

---

전체 학습 진도

# 8 / 20회

**40%**

## 4. 다음 Day 9 예고 — Stack Buffer Overflow

다음 차시에서는 다음 내용을 학습할 거야.

- 버퍼의 크기와 메모리 경계
- Stack Buffer Overflow 발생 원리
- 입력 길이에 따른 스택 데이터 변화
- 지역 변수와 인접 메모리의 손상
- Stack Canary의 역할
- pwntools를 활용한 메모리 손상 관찰

다음 학습에 앞서 한 가지 생각해 봐.

**만약 `ret`이 실행되기 전에 `[RSP]`에 저장된 반환 주소가 다른 값으로 변경되어 있다면 CPU는 어디로 이동할까?**

오늘 배운 내용과 BOF를 연결하는 핵심 질문이야.

Day 8은 여기까지 마무리하면 돼.

---