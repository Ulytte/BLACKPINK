# 실험 보드 Rev 5 배선 데이터 생성기
# = 4S(사인파, 검증된 Rev 4.0 배치 그대로) + 교차 왜곡 대책 풀다운 + 사각파 회로(구성 4 변형) + 버튼
# 출력: wiring-EXP.json  (validate_exp.py / spice_from_wiring.py / render_exp.py 가 이것만 읽음)
import json, pathlib
src=json.loads((pathlib.Path(__file__).parent/'../../최종도면/04_데이터_검증/wiring-4S.json').read_text(encoding='utf8'))
d={'configuration':'EXP-Rev5','nets':src['nets'],'parts':src['parts'],'holes':dict(src['holes']),
   'board_jumpers':[list(j) for j in src['board_jumpers']],'external_leads':[list(e) for e in src['external_leads']]}
N=d['nets']; H=d['holes']
# --- 교차 왜곡 대책: 버퍼 A 출력(SINE, 1번 핀) → GND 1 kΩ × 3, 가상 접지(VG, 7번 핀) → GND 1 kΩ × 2
for p in ('RPA1','RPA2','RPA3','RPB1','RPB2'):
    d['parts'].append([p,'1 kΩ','resistor'])
N['SINE']['ends']+=['RPA1.1','RPA2.1','RPA3.1']
N['VG']['ends']+=['RPB1.1','RPB2.1']
N['GND']['ends']+=['RPA1.2','RPA2.2','RPA3.2','RPB1.2','RPB2.2']
H.update({'RPA1.1':'b11','RPA1.2':'T-8','RPA2.1':'c11','RPA2.2':'T-7','RPA3.1':'a30','RPA3.2':'T-24',
          'RPB1.1':'g11','RPB1.2':'B-9','RPB2.1':'i11','RPB2.2':'B-7'})
# --- 사각파(구성 4 변형): D9 → RQ 330 Ω → 집게 Q1(와셔 A), 집게 Q4(와셔 B) → D8. A2 = D9 쪽, A3 = 전극 쪽
d['parts'].append(['RQ','330 Ω 1%','resistor'])
N['QDRV']={'color':'I','ends':['UNO.D9','RQ.1','UNO.A2']}
N['QNODE']={'color':'V','ends':['RQ.2','Q1','UNO.A3']}
N['QRET']={'color':'I','ends':['UNO.D8','Q4']}
H.update({'UNO.D9':'j30','UNO.A2':'i30','RQ.1':'g30','RQ.2':'g34','Q1':'j34','UNO.A3':'i34','UNO.D8':'j38','Q4':'i38'})
d['external_leads']+= [['UNO.D9','j30'],['UNO.A2','i30'],['Q1','j34'],['UNO.A3','i34'],['UNO.D8','j38'],['Q4','i38']]
# --- 버튼: 가운데 홈에 걸침 (20행·22행). D7(내부 풀업) ↔ GND
d['parts'].append(['SW','택트 스위치','button'])
N['BTN']={'color':'T','ends':['UNO.D7','SW.1']}
N['GND']['ends']+=['SW.2']
H.update({'SW.1':'e20','SW.2':'e22','SW.3':'f20','SW.4':'f22','UNO.D7':'a20'})
d['board_jumpers'].append(['GND','a22','T-17','G'])
d['external_leads'].append(['UNO.D7','a20'])
# 집게 이름 정리: E1/E4 = 사인파 단자, Q1/Q4 = 사각파 단자
d['clip_note']='와셔 볼트 2개의 집게선을 사인파 측정 땐 E1·E4(j54·j56), 사각파 측정 땐 Q1·Q4(j34·i38)에 꽂는다'
out=pathlib.Path(__file__).parent/'wiring-EXP.json'
out.write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding='utf8'); print('wrote',out.name,len(d['parts']),'parts')
