# 배선 데이터 → 꽂는 순서표(Markdown). 사람이 옮겨 적지 않도록 자동 생성
import json, pathlib, re
HERE=pathlib.Path(__file__).parent
d=json.loads((HERE/'wiring-EXP.json').read_text(encoding='utf8')); H=d['holes']
NEW={'RPA1','RPA2','RPA3','RPB1','RPB2','RQ','SW'}
def ext(k):
    m={'UNO.':'Arduino ','LCD.':'LCD ','DS.':'온도센서 '}
    for a,b in m.items():
        if k.startswith(a): return b+{'red':'빨강','black':'검정','yellow':'노랑'}.get(k[len(a):],k[len(a):])
    return {'E1':'사인 집게 E1 (와셔 A)','E4':'사인 집게 E4 (와셔 B)','Q1':'사각 집게 Q1 (와셔 A)','Q4':'사각 집게 Q4 (와셔 B)'}.get(k,k)
L=['# 실험 보드 Rev 5 — 꽂는 순서표 (wiring-EXP.json에서 자동 생성)','',
   '구멍 표기: a~j = 세로 글자, 숫자 = 행. T+/T− = 위쪽 전원 레일, B+/B− = 아래쪽 레일 (레일 번호는 레일 구멍 순서, 25와 26 사이 끊김).','',
   '## 1단계: 칩 (LM358, 반달 홈이 1행 쪽)','','| 칩 핀 | 구멍 | 역할 |','|---|---|---|']
role={1:'A 출력 = 사인파',2:'A − 입력 (1번과 연결)',3:'A + 입력 (필터 출력)',4:'GND',5:'B + 입력 (기준 1.8 V)',6:'B − 입력 (7번과 연결)',7:'B 출력 = 가상 접지',8:'5 V'}
for k in range(1,9): L.append(f'| {k} | {H[f"U1.{k}"]} | {role[k]} |')
L+=['','## 2단계: 저항·커패시터·버튼','','| 부품 | 값 | 다리 1 | 다리 2 | 비고 |','|---|---|---|---|---|']
for p,v,kind in d['parts']:
    if kind=='button': L.append(f'| {p} | 택트 스위치 | e20·e22 | f20·f22 | 가운데 홈에 걸침 **(Rev 5 추가)** |'); continue
    note=[]
    if kind=='electrolytic': note.append('**다리 1 = + (긴 다리)**')
    if p in NEW: note.append('**Rev 5 추가**')
    L.append(f'| {p} | {v} | {H[p+".1"]} | {H[p+".2"]} | {" ".join(note)} |')
L+=['','## 3단계: 보드 위 점퍼 (그림의 원 안 번호)','','| 번호 | 넷 | 시작 | 끝 |','|---|---|---|---|']
for i,(n,a,b,c) in enumerate(d['board_jumpers'],1): L.append(f'| {i} | {n} | {a} | {b} |'+(' **Rev 5 추가**' if i==len(d['board_jumpers']) else ''))
L+=['','## 4단계: 바깥 장치로 가는 선','','| 장치 쪽 | 구멍 |','|---|---|']
for e,h in d['external_leads']: L.append(f'| {ext(e)} | {h} |')
L+=['','> 집게 2개(와셔 A·B 볼트)는 **사인 측정 = E1(j54)·E4(j56)**, **사각 측정 = Q1(j34)·Q4(i38)**. 와셔 A는 항상 1번(E1/Q1), B는 항상 4번(E4/Q4).']
(HERE/'꽂는_순서표.md').write_text('\n'.join(L)+'\n',encoding='utf8'); print('ok', len(L))
