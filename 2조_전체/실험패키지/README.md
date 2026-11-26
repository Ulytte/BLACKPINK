# 2조 실험 패키지 (실험 보드 Rev 5)

**시작: [`실험_따라하기.md`](실험_따라하기.md)** — 이것만 보고 순서대로.

| 폴더 | 내용 |
|---|---|
| `01_회로/` | `breadboard-EXP.png` 배선 그림, `꽂는_순서표.md`(구멍 번호), `wiring-EXP.json`(원본 데이터) + 검증 스크립트 |
| `02_펌웨어/wc_meter/` | **Arduino에 올릴 스케치 하나** (사인·사각·온도·LCD·버튼·판정·CSV) |
| `02_펌웨어/host_test`, `avr_test` | 펌웨어 검증용 (PC 모의 실행, simavr 하네스). 실험엔 필요 없음 |
| `03_PC/` | `logger.py`(기록), `analyze.py`(분석). `test/` = 가상 실험 예시 보고서 |
| `04_기록지/` | 종이 백업 기록지 |

Rev 4 대비 바뀐 점: 사인 MID 108 / AMP 52, 풀다운 1 kΩ 5개(교차 왜곡 대책), 사각파 회로를 같은 보드에 추가(RQ, D9·D8·A2·A3), 버튼(D7), 동기검파로 측정.

검증 다시 돌리기 (Linux, ngspice·avr-gcc·simavr 필요):
```bash
cd 01_회로 && python3 wiring_exp.py && python3 validate_exp.py && python3 mutation_test.py && python3 spice_from_wiring.py
```
```bash
cd 02_펌웨어 && ./build_avr.sh
```
```bash
cd 03_PC && python3 test/virtual_experiment.py
```
