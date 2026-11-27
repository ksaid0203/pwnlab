| No | 내용 | 링크 |
| --- | --- | --- |
| 01 | pwntools 설치 및 process() 실습 | [DAY01](./DAY01/DAY01.md) |
| 02 | send / sendline / recvuntil | [DAY02](./DAY02/DAY02.md) |
| 03 | sendafter / sendlineafter | [DAY03](./DAY03/DAY03.md) |
| 04 | p32 / p64 / u32 / u64 | [DAY04](./DAY04/DAY04.md) |
| 05 | 메뉴 기반 프로그램 자동화 | [DAY05](./DAY05/DAY05.md) |
| 06 | ELF 심볼 및 함수 주소 확인 | [DAY06](./DAY06/DAY06.md) |
| 07 | GOT와 PLT 이해 | [DAY07](./DAY07/DAY07.md) |
| 08 | 스택 프레임과 리턴 주소 | [DAY08](./DAY08/DAY08.md) |
| 09 | 버퍼 오버플로우 원리 | [DAY09](./DAY09/DAY09.md) |
| 10 | 간단한 취약 프로그램 분석 | [DAY10](./DAY10/DAY10.md) |
| 11 | GDB 기본 명령어 | [DAY11](./DAY11/DAY11.md) |
| 12 | cyclic과 오프셋 찾기 | [DAY12](./DAY12/DAY12.md) |
| 13 | gdb.attach 디버깅 | [DAY13](./DAY13/DAY13.md) |
| 14 | ret2win 페이로드 제작 | [DAY14](./DAY14/DAY14.md) |
| 15 | 로컬 익스플로잇 완성 | [DAY15](./DAY15/DAY15.md) |
| 16 | 메모리 leak과 u64 | [DAY16](./DAY16/DAY16.md) |
| 17 | libc 베이스 주소 계산 | [DAY17](./DAY17/DAY17.md) |
| 18 | ROP와 ret2libc 개념 | [DAY18](./DAY18/DAY18.md) |
| 19 | 로컬 CTF 문제 풀이 | [DAY19](./DAY19/DAY19.md) |
| 20 | 최종 익스플로잇 정리 | [DAY20](./DAY20/DAY20.md) |

1. \x00은 문자열의 끝을 나타내지만, 데이터 전송의 끝을 의미하지는 않아.

| 구분 | \x00 (NULL) | \x0a (Newline) |
| --- | --- | --- |
| HEX 값 | 0x00 | 0x0a |
| C 문자열 | 문자열 종료 표시 | 일반 문자
|send() | 그대로 전송 | 그대로 전송 |
| fgets() | 입력에 포함 가능 | 입력 종료 조건 |
| read() | 일반 바이트 | 일반 바이트 |

2. ELF 기능

| 기능 | 설명 |
| --- | --- |
| ELF('./chall') | ELF 파일 분석 |
| elf.arch | CPU 아키텍처 |
| elf.bits | 32비트 또는 64비트 |
| elf.endian | 엔디언 정보 |
| elf.entry | 프로그램 진입점 |
| elf.symbols | 심볼 정보 |
| elf.search() | 바이너리 내부 데이터 검색 |
| elf.read() | 가상 주소 기준 데이터 읽기 |
| elf.checksec() | 바이너리 보호 기법 확인 |

3. 자료형

| 코드 | 자료형 | 반환값 |
| --- | --- | --- |
| elf.symbols['global_value'] | int | 변수의 주소 |
| elf.read(addr, 4) | bytes | b'\xd2\x04\x00\x00' |
| u32(elf.read(addr, 4)) | int | 1234 |
| p32(1234) | bytes | b'\xd2\x04\x00\x00' |
| hex(1234) | str | '0x4d2' |

4. Day 6 핵심 암기

| 코드 | 결과 | 크기 |
| --- | --- | --- |
| b'\x00' | NULL 바이트 | 1바이트 |
| p32(0) | NULL 바이트 4개 | 4바이트 |
| p64(0) | NULL 바이트 8개  |8바이트 |
| u32(p32(0)) | 정수 0 | 정수형 |

5. GOT와 PLT의 차이

동적 링크 방식으로 컴파일하면 일반적으로 puts()의 실제 구현 전체가 실행 파일에 포함되지 않아. 대신 프로그램이 실행될 때 공유 라이브러리의 함수를 연결해서 사용해.

| 구분	|   PLT	|   GOT |
| --- | --- | --- |
| 전체 이름 |   Procedure Linkage Table |	Global Offset Table |
|   역할	|   외부 함수 호출을 중계   |   주소 정보를 저장    |
|   주요 내용	|   기계어 명령어	|   주소 데이터 |
|   pwntools    |	elf.plt	|   elf.got |
|   관련 섹션   |	.plt, .plt.sec 등	|   .got, .got.plt 등   |

6. Lazy Binding

외부 함수의 실제 주소를 처음 호출할 때 연결하는 방식을 Lazy Binding이라고 해.

