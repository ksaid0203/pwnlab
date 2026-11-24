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


3. Day 6 핵심 암기
| 코드 | 결과 | 크기 |
| --- | --- | --- |
| b'\x00' | NULL 바이트 | 1바이트 |
| p32(0) | NULL 바이트 4개 | 4바이트 |
| p64(0) | NULL 바이트 8개  |8바이트 |
| u32(p32(0)) | 정수 0 | 정수형 |