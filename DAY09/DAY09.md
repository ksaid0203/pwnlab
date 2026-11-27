# chatgpt response

# Day 9 — Stack Buffer Overflow(BOF)의 원리

(2주 차 · 9/20회) 2026년 11월 27일 금요일

지난 Day 8에서는 스택 프레임을 분석하고 `push`, `pop`, `call`, `leave`, `ret`에 따른 레지스터 변화를 공부했어. 최종 확인 문제까지 모두 통과했지.

오늘은 그 지식을 바탕으로 본격적으로 바이너리 취약점 분석에 들어갈 거야.

**오늘의 핵심 목표는 버퍼의 크기를 초과하는 입력이 어떻게 인접한 메모리 데이터를 변경하는지 이해하고, pwntools로 이를 직접 검증하는 것이야.**

**오늘의 학습 구성**

이론 — BOF 발생 원리 **15분**

실습 — 입력 길이와 메모리 손상 분석 **35분**

정리 — 실습 과제 및 심화 문제 **10분**

---

**총 학습 시간**
**60분**

# 1. 이론 — Stack Buffer Overflow (15분)

## 1-1. Buffer Overflow란?

버퍼에 할당된 메모리 크기보다 많은 데이터를 기록하면서 버퍼의 경계를 넘어 인접한 메모리까지 변경하는 현상이야.

예를 들어 다음과 같은 C 코드가 있다고 가정하자.

```c
char buf[16];

read(0, buf, 16);
```

최대 16바이트를 입력받기 때문에 버퍼 크기를 초과하지 않아.

하지만 다음 코드에서는 문제가 발생할 수 있어.

```c
char buf[16];

read(0, buf, 24);
```

버퍼는 16바이트인데 최대 24바이트를 기록할 수 있기 때문이야.

| 입력 크기 | 버퍼 크기 | 경계 초과 크기 |
|--------|--------|--------|
| 8 bytes | 16 bytes | 0 bytes |
| 16 bytes | 16 bytes | 0 bytes |
| 17 bytes | 16 bytes | 1 byte |
| 24 bytes | 16 bytes | 8 bytes |

`read()`는 전달받은 포인터가 가리키는 C 배열의 실제 크기를 자동으로 검사하지 않아.

## 1-2. 스택 성장 방향과 데이터 기록 방향

여기서 반드시 구분해야 하는 개념이 있어.

- 스택의 성장 방향: 높은 주소 → 낮은 주소
- 배열의 데이터 기록 방향: 낮은 주소 → 높은 주소

설명을 위한 가상의 스택 배치이며 실제 변수 배치는 컴파일러에 따라 달라져.

스택이 낮은 주소 방향으로 성장한다고 해서 배열에 입력하는 데이터도 낮은 주소 방향으로 기록되는 것은 아니야.

## 1-3. 입력 길이에 따른 메모리 변화

16바이트 버퍼 뒤에 8바이트 정수형 변수가 존재한다고 가정해 보자.

```c
struct Frame {
    char buf[16];
    uint64_t marker;
};
```

`marker`의 초기값은 다음과 같아.

```python
marker = 0x1122334455667788
```

아래 시뮬레이터에서 입력 길이를 변경하면서 `marker`가 어떻게 변하는지 확인해 봐.

**Buffer Overflow 시뮬레이터**

입력 데이터: b'A' \* length

입력 길이

# bytes

*（可调节滑块：范围 0 – 24，步长 1）*
>
> **Scale labels:** 0 — 0 · 8 — 8 · 16 — 16 · 24 — 24

buf$$0\~15$$ — 16바이트

marker — 인접한 8바이트

---

현재 marker 값 (Little Endian)

# 0x

버퍼 경계 초과  bytes

[초기화]

특히 17바이트, 20바이트, 24바이트를 각각 입력했을 때 `marker`의 변화를 관찰해 봐.

## 1-4. Stack Canary란?

Stack Canary는 함수의 스택 프레임에 검사값을 배치하고, 함수가 반환되기 전에 그 값이 손상되었는지 검사하는 보호 기법이야.

전형적인 Canary 배치 예시

Canary가 손상되면 일반적으로 `__stack_chk_fail()`이 호출되어 프로그램이 비정상 종료돼.

단, Canary는 모든 메모리 손상을 방지하는 것이 아니야. Canary까지 도달하지 않는 인접 지역 변수의 손상은 탐지하지 못할 수도 있어.

오늘은 인접 데이터의 손상에 집중하고, 보호 기법의 상세 분석은 Day 10에서 진행할 거야.

---

# 2. 실습 — pwntools로 메모리 손상 관찰 (35분)

## Step 1. 실습용 바이너리 만들기 (5분)

이번 실습에서는 구조체를 사용해 버퍼와 인접 변수의 배치를 명확하게 구성할 거야. 직접 만든 로컬 학습용 바이너리만 대상으로 진행해.

`chall09.c` 파일을 작성해.

```c

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <unistd.h>
#include <inttypes.h>

struct Frame {
    char buf[16];
    uint64_t marker;
};

_Static_assert(
    offsetof(struct Frame, marker) == 16,
    "Unexpected structure layout"
);

int main(void) {
    struct Frame frame = {
        .buf = {0},
        .marker = 0x1122334455667788
    };

    printf("BUF: %p\n", (void *)frame.buf);
    printf("MARKER: %p\n", (void *)&frame.marker);

    printf("BEFORE: 0x%016" PRIx64 "\n", frame.marker);

    printf("Input: ");
    fflush(stdout);

    ssize_t n = read(0, frame.buf, 24);

    printf("READ: %zd\n", n);
    printf("AFTER: 0x%016" PRIx64 "\n", frame.marker);

    printf("Inspect: ");
    fflush(stdout);

    getchar();

    return 0;
}
```

컴파일\:

```bash
gcc -O0 -g -no-pie -fno-omit-frame-pointer \
    -fstack-protector-all chall09.c -o chall09
```

컴파일 과정에서 `read()`가 16바이트 버퍼에 24바이트를 기록할 수 있다는 경고가 발생할 수 있어. 이번에는 메모리 경계 초과를 관찰하기 위해 의도적으로 작성한 코드야.

Stack Canary는 활성화한 상태로 진행해.

## Step 2. 입력 전후 marker 비교하기 (5분)

`day9_basic.py`를 작성해.

```python

from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

p = process(elf.path)

try:
    buf_addr = recv_value(p, b'BUF')
    marker_addr = recv_value(p, b'MARKER')
    before = recv_value(p, b'BEFORE')

    p.recvuntil(b'Input: ')

    print(f"BUF:    {buf_addr:#x}")
    print(f"MARKER: {marker_addr:#x}")
    print(f"Offset: {marker_addr - buf_addr}")

    payload = b'A' * 16

    p.send(payload)

    received = recv_value(p, b'READ', 10)
    after = recv_value(p, b'AFTER')

    print(f"Input length: {len(payload)}")
    print(f"Read length:  {received}")
    print(f"Before: {before:#018x}")
    print(f"After:  {after:#018x}")

    assert received == len(payload)
    assert before == after

    p.sendlineafter(b'Inspect: ', b'')
    p.recvall()

finally:
    p.close()
```

예상 결과\:

```text
Offset: 16
Input length: 16
Read length:  16
Before: 0x1122334455667788
After:  0x1122334455667788
```

여기서 중요한 부분은 `p.send()`를 사용했다는 것이야.

```python
p.send(b'A' * 16)
```

`sendline()`을 사용하면 마지막에 개행 문자 `\x0a`가 추가되므로 실제 전송 길이가 17바이트가 돼.

Day 1에서 배웠던 입출력 차이가 이번 실습에서 중요하게 사용되는 거야.

## Step 3. 입력 길이별 자동 분석 (10분)

매번 새로운 프로세스를 실행하면서 입력 길이에 따른 결과를 비교해 보자.

```python

from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf
context.log_level = 'error'

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

def test_length(length):
    p = process(elf.path)

    try:
        before = recv_value(p, b'BEFORE')

        p.sendafter(b'Input: ', b'A' * length)

        received = recv_value(p, b'READ', 10)
        after = recv_value(p, b'AFTER')

        assert received == length

        p.sendlineafter(b'Inspect: ', b'')
        p.recvall()

        return before, after

    finally:
        p.close()

for length in [8, 15, 16, 17, 20, 24]:
    before, after = test_length(length)

    changed = before != after

    print(
        f"Length: {length:2d} | "
        f"Marker: {after:#018x} | "
        f"Changed: {changed}"
    )
```

예상 출력\:

```text
Length:  8 | Marker: 0x1122334455667788 | Changed: False
Length: 15 | Marker: 0x1122334455667788 | Changed: False
Length: 16 | Marker: 0x1122334455667788 | Changed: False
Length: 17 | Marker: 0x1122334455667741 | Changed: True
Length: 20 | Marker: 0x1122334441414141 | Changed: True
Length: 24 | Marker: 0x4141414141414141 | Changed: True
```

**입력 길이와 marker 손상 크기**

실습 구조에 따른 예상 결과

버퍼 내부

경계 초과

16바이트까지는 `marker`가 유지되지만, 17바이트부터 `marker`의 가장 낮은 주소에 위치한 바이트가 변경되는 것을 확인할 수 있어.

## Step 4. 실제 메모리의 입력 전후 비교 (10분)

Day 8에서 사용했던 `p.readmem()`과 `hexdump()`를 활용하자.

```python

from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

p = process(elf.path)

try:
    buf_addr = recv_value(p, b'BUF')
    marker_addr = recv_value(p, b'MARKER')
    before = recv_value(p, b'BEFORE')

    p.recvuntil(b'Input: ')

    before_raw = p.readmem(buf_addr, 24)

    print("[ Before Input ]")
    print(hexdump(before_raw))

    p.send(b'A' * 20)

    received = recv_value(p, b'READ', 10)
    after = recv_value(p, b'AFTER')

    p.recvuntil(b'Inspect: ')

    after_raw = p.readmem(buf_addr, 24)

    print("[ After Input ]")
    print(hexdump(after_raw))

    print("[ Changed Bytes ]")

    for i, (old, new) in enumerate(
        zip(before_raw, after_raw)
    ):
        if old != new:
            print(
                f"Offset: {i:02d} | "
                f"Address: {buf_addr + i:#x} | "
                f"{old:02x} -> {new:02x}"
            )

    assert u64(before_raw[16:24]) == before
    assert u64(after_raw[16:24]) == after
    assert received == 20

    p.sendline(b'')
    p.recvall()

finally:
    p.close()
```

예상 메모리 변화\:

입력 전

---

20바이트 입력 후

빨간색으로 표시된 4바이트가 버퍼 경계를 넘어 변경된 marker 데이터야.

이번 코드에서 새롭게 활용한 Python 문법은 `enumerate()`와 `zip()`의 조합이야.

```python
for i, (old, new) in enumerate(
    zip(before_raw, after_raw)
):
    if old != new:
        print(i, old, new)
```

메모리 덤프 두 개를 바이트 단위로 비교할 때 유용해.

## Step 5. 취약한 코드 수정 및 재검증 (5분)

`chall09.c`를 복사해서 `chall09_safe.c`를 만든 후 다음 부분을 수정해.

```c
// 수정 전
ssize_t n = read(0, frame.buf, 24);

// 수정 후
ssize_t n = read(0, frame.buf, sizeof(frame.buf));
```

컴파일\:

```bash
gcc -O0 -g -no-pie -fno-omit-frame-pointer \
    -fstack-protector-all chall09_safe.c -o chall09_safe
```

수정한 바이너리에 24바이트를 입력해 보자.

```python

from pwn import *

p = process('./chall09_safe')

try:
    p.recvuntil(b'BEFORE: ')
    before = int(p.recvline().strip(), 16)

    p.sendafter(b'Input: ', b'A' * 24)

    p.recvuntil(b'READ: ')
    received = int(p.recvline().strip())

    p.recvuntil(b'AFTER: ')
    after = int(p.recvline().strip(), 16)

    print(f"Read length: {received}")
    print(f"Before: {before:#018x}")
    print(f"After:  {after:#018x}")

    assert received <= 16
    assert before == after

    print("Buffer boundary verified!")

    p.recvall()

finally:
    p.close()
```

| 항목 | 수정 전 | 수정 후 |
|--------|--------|--------|
| 전송 크기 | 24 bytes | 24 bytes |
| read 최대 크기 | 24 bytes | 16 bytes |
| marker 손상 | 발생 | 발생하지 않음 |

수정 후에는 `read()`가 소비하지 않은 입력이 남아 있으므로 뒤에 있는 `getchar()`가 남은 데이터를 읽고 프로그램을 종료할 수 있어.

오늘 예제는 x86-64 Linux 및 GCC 기준으로 작성했으며, 실제 컴파일과 실행은 검증하지 않았어. `read()`는 요청한 크기보다 적은 데이터를 반환할 수도 있으므로 실습에서는 반환값도 함께 검사하도록 구성했어.

---

# 3. 직접 풀 실습 과제

## Day 9 과제 — Buffer Overflow 자동 탐지기

`day9_task.py`를 작성해서 입력 전후의 메모리를 비교하고 버퍼 경계 초과 여부를 자동으로 판단해 봐.

| 과제 | 요구사항 |
|--------|--------|
| TODO 1 | ELF 및 context 설정 |
| TODO 2 | 주소와 정수 수신 함수 구현 |
| TODO 3 | BUF, MARKER 주소 수집 |
| TODO 4 | 두 주소의 상대 거리 계산 |
| TODO 5 | 입력 전 메모리 덤프 수집 |
| TODO 6 | 지정한 길이만큼 입력 전송 |
| TODO 7 | 입력 후 메모리 덤프 수집 |
| TODO 8 | 변경된 바이트의 개수 및 위치 출력 |
| TODO 9 | marker 손상 여부 판단 |
| TODO 10 | 정상 종료 및 여러 입력 길이 반복 검사 |

### 과제용 코드

```python

from pwn import *

# TODO 1: Load ELF

def recv_value(p, label, base=16):
    # TODO 2
    pass

def analyze(length):
    p = process('./chall09')

    try:
        # TODO 3: Receive addresses

        # TODO 4: Calculate marker offset

        # TODO 5: Read memory before input

        # TODO 6: Send input and receive result

        # TODO 7: Read memory after input

        # TODO 8: Compare changed bytes

        # TODO 9: Check marker corruption

        # TODO 10: Finish process

        pass

    finally:
        p.close()

for length in [8, 16, 17, 20, 24]:
    analyze(length)
```

### 추가 도전 과제 — 손상 크기 계산

다음 함수를 직접 구현해 봐.

```python
def count_changed_bytes(before, after):
    # 변경된 바이트의 개수를 반환
    pass
```

그리고 전체 구조체에서 변경된 바이트 개수와 `marker`에서 변경된 바이트 개수를 각각 구해.

```python
total_changed = count_changed_bytes(
    before_raw,
    after_raw
)

marker_changed = count_changed_bytes(
    before_raw[16:24],
    after_raw[16:24]
)
```

다음 표를 직접 완성하는 것이 목표야.

| 입력 길이 | 전체 변경 바이트 | marker 변경 바이트 |
|--------|--------|--------|
| 8 | ? | ? |
| 16 | ? | ? |
| 17 | ? | ? |
| 20 | ? | ? |
| 24 | ? | ? |

추가로 입력 데이터가 `b'A'`가 아니라 `b'\x00'`인 경우에도 변경된 바이트 개수와 실제 기록된 바이트 개수가 항상 같은지 생각해 봐.

---

# 4. 정리 — 이해도 확인 (10분)

**Day 9 확인 퀴즈** /5 응답

## 마지막 심화 문제

다음과 같은 메모리 구조가 있다고 가정하자.

```text
buf 주소:    0x7000
marker 주소: 0x7010

buf 크기:    16 bytes
marker 크기:  8 bytes

marker 초기값:
0x1122334455667788
```

입력 전 메모리\:

다음 코드를 실행한다고 가정할게.

```python
payload = b'B' * 19
p.send(payload)
```

`read()`가 19바이트를 모두 수신했을 때 다음 여섯 가지를 구해 봐.

1. `len(payload)`의 값
2. 버퍼 경계를 초과한 바이트 개수
3. 마지막 입력 바이트가 기록되는 메모리 주소
4. 변경된 `marker`의 정수 값(16진수)
5. `p.sendline(payload)`로 변경했을 때 실제 전송 길이
6. `p.sendline(payload)`로 변경하고 모든 데이터를 수신했을 때 `marker`의 정수 값(16진수)

이번에도 정답은 미리 공개하지 않을게. 특히 4번과 6번은 Little Endian과 개행 문자까지 고려해서 계산해 봐.

---

# 5. 오늘의 핵심 암기

| 개념 | 핵심 내용 |
|--------|--------|
| Buffer Overflow | 할당된 버퍼 경계를 넘어 데이터를 기록하는 현상 |
| 스택 성장 | 높은 주소에서 낮은 주소 방향 |
| 배열 기록 | 낮은 주소에서 높은 주소 방향 |
| `send()` | 전달한 바이트 데이터 전송 |
| `sendline()` | 기본적으로 개행 문자 추가 |
| Stack Canary | 함수 반환 전 검사값의 손상 여부 확인 |
| `readmem()` | 로컬 프로세스의 메모리 읽기 |
| `hexdump()` | 메모리 데이터를 시각적으로 분석 |

Day 1부터 Day 8까지 배웠던 바이트 처리, 프로세스 동기화, Little Endian, ELF 분석, 스택 구조가 오늘 실습에서 하나로 연결되고 있어.

## 전체 학습 진도

# 9 / 20회

45% 차시 도달

**다음 Day 10 예고 — 바이너리 보호 기법과 checksec**

다음 시간에는 Canary, NX, PIE, ASLR, Partial RELRO, Full RELRO의 차이를 공부하고, 컴파일 옵션에 따른 보호 기법의 변화를 pwntools로 분석할 거야.

오늘은 단순히 메모리 손상이 발생했다는 사실을 확인하는 데 그치지 말고, **어느 주소의 어떤 바이트가 왜 변경되었는지 설명할 수 있는 수준**까지 연습하는 것이 목표야.

---

# you asked

message time: 2026-11-28 01:30:16

from pwn import *

# TODO 1: Load ELF
elf = ELF('./chall09', checksec=False)
context.binary = elf
context.log_level = 'error'

def recv_value(p, label, base=16):
    # TODO 2
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

def count_changed_bytes(before, after):
    # 변경된 바이트의 개수를 반환
    ret = []
    for i in range(8):
        if before[i] != after[i]:
            ret.append(i)
    return ret

def analyze(length):
    p = process(elf.path)

    try:
        # TODO 3: Receive addresses
        buf = recv_value(p, b'BUF')
        marker = recv_value(p, b'MARKER')

        # TODO 4: Calculate marker offset
        print(f"marker - buf: {marker - buf}")

        # TODO 5: Read memory before input
        before = recv_value(p, b'BEFORE')
        print(f"before: {before:#x}")
        print(hexdump(before, 16))

        # TODO 6: Send input and receive result
        payload = b'A' * length

        p.sendline(payload)
        after = recv_value(p, b'AFTER')

        # TODO 7: Read memory after input
        
        print(f"after: {after:#x}")
        print(hexdump(after, 16))
        # TODO 8: Compare changed bytes
        #count_changed_bytes(p64(before), p64(after))
        comp = count_changed_bytes(p64(before), p64(after))
        print(f"len(comp): {len(comp)}")
        print(comp)

        # TODO 9: Check marker corruption

        # TODO 10: Finish process
        
        p.sendlineafter(b'Inspect: ', b'')
        p.recvall()

    finally:
        p.close()

for length in [8, 16, 17, 20, 24]:
    analyze(length)

# 추가 도전 과제
def count_changed_bytes(before, after):
    # 변경된 바이트의 개수를 반환
    ret = []
    for i in range(8):
        if before[i] != after[i]:
            ret.append(i)
    return ret

c 코드에는 구조체 초기화시 0으로 초기화가 되어서 모든 byte가 b'\x00'으로 되어있을 거야.
결론적으로 이런 상황에서 입력이 b'A'에서 b'\x00'으로 바꾸면 변경된 바이트 갯수를 찾기 어려울 수 있을거 같아.

# 심화문제

1. 19
2. 3
3. 0x7012
4. 0x1122334455667BBB
5. 20
6. 0x112233445566ABBB

---

# chatgpt response

Day 9 실습에서 `p64()`를 활용해 정수 값을 바이트 단위로 비교한 접근은 좋아. 변경된 바이트의 인덱스를 리스트로 반환하도록 구현한 것도 활용도가 높아.

다만 이번 과제에서는 **`sendline()` 사용, 실제 메모리 덤프 수집, Little Endian 계산**을 보완해야 해.

# 1. 실습 과제 코드 리뷰

| 과제 | 평가 | 설명 |
|--------|--------|--------|
| TODO 1 |  | ELF 설정 완료 |
| TODO 2 |  | 정수 수신 함수 구현 |
| TODO 3 |  | 주소 수집 완료 |
| TODO 4 |  | 상대 거리 계산 완료 |
| TODO 5 |  | 실제 메모리 읽기 필요 |
| TODO 6 |  | 개행 문자 및 수신 길이 확인 필요 |
| TODO 7 |  | 실제 메모리 읽기 필요 |
| TODO 8 |  | marker 영역만 비교함 |
| TODO 9 |  | 손상 여부 판단 미구현 |
| TODO 10 |  | 반복 검사 및 종료 구현 |

실제 실행이 아닌 제출한 코드와 `chall09.c`를 기준으로 검토한 결과야.

## 1-1. count\_changed\_bytes() 개선

네가 작성한 함수\:

```python
def count_changed_bytes(before, after):
    ret = []

    for i in range(8):
        if before[i] != after[i]:
            ret.append(i)

    return ret
```

8바이트 marker를 비교하는 용도로는 정상적인 코드야. 하지만 두 가지 개선점이 있어.

- `range(8)`로 고정되어 있어 24바이트 전체 구조체를 비교할 수 없어.
- 함수 이름은 변경된 바이트의 개수를 반환하는 것처럼 보이지만, 실제로는 인덱스 리스트를 반환해.

네가 구현한 방식을 유지하면서 범용적으로 개선하면 다음과 같아.

```python
def find_changed_bytes(before, after):
    assert len(before) == len(after)

    ret = []

    for i in range(len(before)):
        if before[i] != after[i]:
            ret.append(i)

    return ret
```

또는 Python의 `enumerate()`와 `zip()`을 활용할 수 있어.

```python
def find_changed_bytes(before, after):
    assert len(before) == len(after)

    return [
        i
        for i, (old, new) in enumerate(zip(before, after))
        if old != new
    ]
```

사용 예시\:

```python
before = b'ABCDEFGH'
after  = b'ABXXEFGH'

changed = find_changed_bytes(before, after)

print(changed)       # [2, 3]
print(len(changed))  # 2
```

인덱스를 반환하는 네 방식은 변경된 메모리 주소까지 계산할 수 있다는 장점이 있어.

---

## 1-2. sendline() 사용 문제

이번 코드에서 가장 중요한 수정 사항이야.

```python
payload = b'A' * length
p.sendline(payload)
```

`sendline()`은 기본적으로 마지막에 `\x0a`를 추가해.

따라서 다음과 같은 차이가 발생해.

| length | 실제 전송 크기 | read 최대 수신 크기 | 예상 marker 기록 크기 |
|--------|--------|--------|--------|
| 8 | 9 | 9 | 0 |
| 16 | 17 | 17 | 1 |
| 17 | 18 | 18 | 2 |
| 20 | 21 | 21 | 5 |
| 24 | 25 | 24 | 8 |

위 표는 `read()`가 가능한 데이터를 한 번에 모두 읽는다고 가정한 결과야.

특히 16바이트 입력에서 문제가 발생해.

**send()와 sendline() 비교**

p.send(b'A' \* 16)

marker: 0x1122334455667788

---

p.sendline(b'A' \* 16)

marker: 0x112233445566770a

마지막 줄은 marker 영역이야. 개행 문자 하나 때문에 버퍼 경계를 초과하게 돼.

따라서 이번 실습에서는 다음과 같이 수정하는 것이 정확해.

```python
p.sendafter(b'Input: ', payload)

received = recv_value(p, b'READ', 10)

assert received == len(payload)
```

프로세스 동기화와 실제 수신 길이 검증도 함께 수행하는 거야.

---

## 1-3. hexdump() 사용 문제

네 코드\:

```python
before = recv_value(p, b'BEFORE')
print(hexdump(before, 16))
```

`before`는 정수형 데이터야. `hexdump()`에는 분석할 바이트 데이터를 명시적으로 전달하는 것이 좋아.

```python
print(hexdump(p64(before), width=16))
```

여기서 `width=16`은 읽을 메모리 크기가 아니라 한 줄에 출력할 바이트 개수야.

하지만 이 방법도 marker의 정수 값을 다시 바이트로 변환한 것일 뿐, 실제 프로세스 메모리를 읽은 것은 아니야.

이번 과제의 목적에 맞게 작성하려면 다음과 같이 해야 해.

```python
p.recvuntil(b'Input: ')

before_raw = p.readmem(buf, 24)

print(hexdump(before_raw))
```

| 코드 | 분석 대상 |
|--------|--------|
| `p64(before)` | marker 정수 값의 바이트 표현 |
| `p.readmem(marker, 8)` | 실제 marker 메모리 |
| `p.readmem(buf, 24)` | 버퍼와 marker 전체 메모리 |

Day 8에서 사용한 `p.readmem()`을 다시 활용하는 부분이야.

---

# 2. 실습 과제 개선 코드

네 코드의 구조와 변경 인덱스를 반환하는 방식을 최대한 유지하면서 수정했어.

```python

from pwn import *

elf = ELF('./chall09', checksec=False)
context.binary = elf
context.log_level = 'error'

def recv_value(p, label, base=16):
    p.recvuntil(label + b': ')
    return int(p.recvline().strip(), base)

def find_changed_bytes(before, after):
    assert len(before) == len(after)

    ret = []

    for i in range(len(before)):
        if before[i] != after[i]:
            ret.append(i)

    return ret

def analyze(length):
    p = process(elf.path)

    try:
        # Receive addresses
        buf = recv_value(p, b'BUF')
        marker = recv_value(p, b'MARKER')

        marker_offset = marker - buf

        print(f"\n[ Length: {length} ]")
        print(f"Marker offset: {marker_offset}")

        assert marker_offset == 16

        # Read memory before input
        before = recv_value(p, b'BEFORE')
        p.recvuntil(b'Input: ')

        before_raw = p.readmem(buf, 24)

        print("[ Before ]")
        print(hexdump(before_raw))

        # Send input
        payload = b'A' * length
        p.send(payload)

        received = recv_value(p, b'READ', 10)
        after = recv_value(p, b'AFTER')

        assert received == len(payload)

        # Read memory after input
        p.recvuntil(b'Inspect: ')

        after_raw = p.readmem(buf, 24)

        print("[ After ]")
        print(hexdump(after_raw))

        # Compare all bytes
        changed = find_changed_bytes(
            before_raw,
            after_raw
        )

        for i in changed:
            print(
                f"Offset: {i:02d} | "
                f"Address: {buf + i:#x} | "
                f"{before_raw[i]:02x} -> "
                f"{after_raw[i]:02x}"
            )

        # Compare marker bytes
        marker_changed = find_changed_bytes(
            before_raw[marker_offset:marker_offset + 8],
            after_raw[marker_offset:marker_offset + 8]
        )

        corrupted = before != after

        print(f"Total changed: {len(changed)}")
        print(f"Marker changed: {len(marker_changed)}")
        print(f"Marker corrupted: {corrupted}")

        assert u64(before_raw[16:24]) == before
        assert u64(after_raw[16:24]) == after

        # Finish process
        p.sendline(b'')
        p.recvall()

    finally:
        p.close()

for length in [8, 16, 17, 20, 24]:
    analyze(length)
```

기존 코드에서 추가된 핵심 기능은 실제 메모리 읽기, 전체 바이트 비교, 변경 주소 출력, marker 손상 여부 판단이야. 수정 코드 역시 실제 실행 검증은 하지 않았어.

---

# 3. 추가 도전 과제 채점

네 답변\:

> 입력이 b'A'에서 b'\\x00'으로 바뀌면 변경된 바이트 갯수를 찾기 어려울 수 있을 거 같아.

핵심 방향은 맞아. 다만 구조체의 모든 바이트가 `\x00`으로 초기화되는 것은 아니야.

```c
struct Frame frame = {
    .buf = {0},
    .marker = 0x1122334455667788
};
```

`buf`는 0으로 초기화되지만 `marker`는 별도의 초기값을 가지고 있어.

**기록된 바이트와 변경된 바이트 비교**

- b'A' $0x41$
- b'\\x00' $0x00$
현재 선택된 항목을 확인할 수 없습니다.

입력 길이 **bytes**

> **슬라이더**
>
> 현재 값을 확인할 수 없습니다.
>
> **범위:** 1~24
>
> **간격:** 1
>
> **눈금 레이블:** 1 — 1 · 16 — 16 · 24 — 24

입력 후 메모리

기록했지만 값은 동일

값이 변경됨

---

기록된 바이트

변경된 바이트

경계 초과

### 예상 결과 비교

`send()`로 전송한 데이터를 모두 수신했다고 가정할게.

| 입력 길이 | A 입력 시 전체 변경 | NULL 입력 시 전체 변경 | marker 변경 |
|--------|--------|--------|--------|
| 8 | 8 | 0 | 0 |
| 16 | 16 | 0 | 0 |
| 17 | 17 | 1 | 1 |
| 20 | 20 | 4 | 4 |
| 24 | 24 | 8 | 8 |

정확하게 표현하면 다음과 같아.

**메모리 비교를 통해 값이 변경된 바이트는 찾을 수 있지만, 기존 값과 동일한 데이터가 덮어쓰인 경우에는 메모리 비교만으로 기록 여부를 판단할 수 없어.**

이 차이는 실제 메모리 손상을 분석할 때도 중요해.

---

# 4. 심화 문제 채점

심화 문제 점수

# 4 / 6

입력 길이 및 주소 계산 정답 · 바이트 값 계산 복습 필요

| 문제 | 네 답변 | 정답 | 결과 |
|--------|--------|--------|--------|
| 1 | 19 | 19 |  |
| 2 | 3 | 3 |  |
| 3 | `0x7012` | `0x7012` |  |
| 4 | `0x1122334455667BBB` | `0x1122334455424242` |  |
| 5 | 20 | 20 |  |
| 6 | `0x112233445566ABBB` | `0x112233440a424242` |  |

4번과 6번은 ASCII 문자와 16진수 표현을 혼동한 것으로 보여.

## 4-1. ASCII 문자와 바이트 값

```python
print(b'B'.hex())     # 42
print(b'\n'.hex())    # 0a
print(b'BBB'.hex())   # 424242
```

| 문자 | ASCII 16진수 |
|--------|--------|
| A | `0x41` |
| B | `0x42` |
| C | `0x43` |
| 개행 문자 | `0x0a` |
| NULL | `0x00` |

`b'B'`는 `0x0b`나 `0xbb`가 아니라 `0x42`야.

또한 1바이트를 16진수로 표현하려면 두 자리가 필요해.

## 4-2. 4번 문제 풀이

```python
payload = b'B' * 19
p.send(payload)
```

16바이트는 버퍼에 기록되고 나머지 3바이트는 marker에 기록돼.

낮은 주소 → 높은 주소

**변경 전**

**변경 후**

---

u64()로 정수 변환

# 0x1122334455424242

## 4-3. 6번 문제 풀이

```python
p.sendline(b'B' * 19)
```

marker에는 `42 42 42 0a`가 기록돼.

**변경 후 메모리**

---

u64()로 정수 변환

# 0x112233440a424242

직접 Python으로도 검증할 수 있어.

```python
from pwn import *

original = p64(0x1122334455667788)

case1 = b'BBB' + original[3:]
case2 = b'BBB\n' + original[4:]

print(hexdump(case1))
print(hex(u64(case1)))

print(hexdump(case2))
print(hex(u64(case2)))
```

---

# 5. 마지막 재확인 문제

이번에는 marker의 초기값과 입력 데이터를 변경해 볼게.

```python
marker = 0xaabbccddeeff1234

payload = b'C' * 18
```

조건은 동일해.

```text
BUF 주소:    0x7000
BUF 크기:    16 bytes
MARKER 주소: 0x7010
MARKER 크기: 8 bytes
```

다음 여섯 가지를 구해 봐.

1. `b'C'.hex()`의 결과
2. `p.send(payload)` 사용 시 경계를 초과한 바이트 개수
3. `p.send(payload)` 사용 시 변경된 marker 정수 값
4. `p.sendline(payload)` 사용 시 실제 전송 길이
5. `p.sendline(payload)` 사용 시 변경된 marker 정수 값
6. `p.send(b'\x00' * 18)` 사용 시 전체 구조체에서 값이 변경된 바이트 개수

모든 입력은 `read()`가 전부 수신했다고 가정하고, 각 문제는 독립적으로 실행하는 조건이야.

이번에는 16진수 숫자를 바로 계산하기보다 **메모리에 저장되는 8개의 바이트를 먼저 나열한 후 역순으로 읽는 방식**을 추천해.

## Day 9 학습 현황

---

# 9 / 20회

45% 차시 도달

BOF의 발생 원리와 메모리 주소 계산은 잘 이해하고 있어. 이번에는 바이트 단위의 데이터 처리 정확도를 높이는 데 집중하자. 이후 payload를 구성할 때도 반드시 필요한 능력이야.

---

# you asked

message time: 2026-11-28 01:34:42

1. 0xC2. 2\
   \
   0xaabbccddeeff4343\
   \
   19\
   \
   0xaabbccddee0A4343\
   \
   3

---

# chatgpt response

이번에는 **6문제 중 4문제 정답**이야. 지난번에 틀렸던 Little Endian 계산은 모두 정확하게 해결했어. 1번과 6번만 복습하면 돼.

## 1. 채점 결과

| 번호 | 네 답변 | 정답 | 결과 |
|--------|--------|--------|--------|
| 1 | `0xC` | `'43'` |  |
| 2 | `2` | `2` |  |
| 3 | `0xaabbccddeeff4343` | 동일 |  |
| 4 | `19` | `19` |  |
| 5 | `0xaabbccddee0a4343` | 동일 |  |
| 6 | `3` | `2` |  |

## 2. 1번 — ASCII와 16진수 표현

3번과 5번에서 `0x43`을 정확하게 사용한 것을 보면 1번은 단순한 실수일 가능성이 있어.

```python
print(b'C'.hex())     # '43' (str)
print(ord('C'))       # 67   (int)
print(hex(ord('C')))  # '0x43' (str)
print(0xC)            # 12   (int)
```

`b'C'.hex()`의 반환값은 정수가 아니라 문자열이라는 점도 기억해 둬.

## 3. 3번과 5번 — Little Endian 계산

두 문제 모두 정확하게 계산했어.

낮은 주소 → 높은 주소

이제 입력 바이트와 개행 문자가 정수 값에 어떤 영향을 주는지 제대로 이해하고 있어.

## 4. 6번 — 기록된 바이트와 변경된 바이트

문제의 코드를 다시 확인해 보자.

```python
p.send(b'\x00' * 18)
```

`sendline()`이 아닌 `send()`이므로 개행 문자가 추가되지 않아.

**입력 전 메모리**

---

**18바이트 입력 후 메모리**

기록했지만 값은 동일

실제로 값이 변경된 영역

---

기록된 바이트

# 18

경계 초과

# 2

변경된 바이트

# 2

변경된 marker의 값은 `0xaabbccddeeff0000`이야.

## 5. 마지막 확인 문제

이번에는 기존 값과 동일한 데이터가 버퍼 경계를 넘어 기록되는 상황이야.

```python
from pwn import *

before = p64(0xaabbccddeeff1234)

payload = b'\x00' * 16 + b'\x34\x12'

p.send(payload)
```

버퍼의 초기값은 모두 `0x00`이고, 입력 데이터 18바이트를 전부 수신했다고 가정할게.

다음 다섯 가지를 구해 봐.

1. `len(payload)`의 값
2. 버퍼 경계를 초과한 바이트 개수
3. 전체 구조체에서 값이 변경된 바이트 개수
4. 입력 후 marker의 정수 값
5. `before == p64(after)`가 `True`라면 BOF가 발생하지 않았다고 판단할 수 있는가? (`after`는 입력 후 marker의 정수 값)

특히 5번이 중요해. **메모리 값의 변경 여부와 버퍼 경계 초과 여부는 서로 다른 개념**이기 때문이야.

## Day 9 학습 현황

---

# 9 / 20회

45% 차시 도달

이번 확인 문제까지 해결하면 Day 9의 이론 복습을 마무리하자.

---
Powered by [AI Exporter](https://saveai.net)