# 검증기 자체 시험: 일부러 배선을 틀리게 바꿨을 때 validate_exp.py가 잡아내는지
import json, subprocess, pathlib, copy, shutil
src=pathlib.Path('wiring-EXP.json'); orig=src.read_text(encoding='utf8')
def mut(desc, fn):
    d=json.loads(orig); fn(d); src.write_text(json.dumps(d,ensure_ascii=False),encoding='utf8')
    r=subprocess.run(['python3','validate_exp.py'],capture_output=True,text=True)
    caught=r.returncode!=0; print(('잡음  ' if caught else '놓침! ')+desc); return caught
ok=True
try:
    ok&=mut('RPB1을 CD가 쓰는 B-8에 꽂음(구멍 중복)', lambda d: d['holes'].__setitem__('RPB1.2','B-8'))
    ok&=mut('RQ 두 다리를 같은 줄(g30, h30)에 꽂음', lambda d: d['holes'].__setitem__('RQ.2','h30'))
    ok&=mut('GND 레일 25/26 연결 점퍼 빠짐', lambda d: d['board_jumpers'].remove(['GND','T-25','T-26','G']))
    ok&=mut('VG 점퍼 h11→i56 빠짐(E4 끊김)', lambda d: d['board_jumpers'].remove(['VG','h11','i56','V']))
    ok&=mut('A3 선을 i34 대신 i35에 꽂음', lambda d: (d['holes'].__setitem__('UNO.A3','i35'), d['external_leads'].__setitem__([e for e,_ in d['external_leads']].index('UNO.A3'),['UNO.A3','i35'])))
    ok&=mut('버튼 GND 점퍼를 5V 레일(T+17)에 꽂음', lambda d: d['board_jumpers'].__setitem__(d['board_jumpers'].index(['GND','a22','T-17','G']),['GND','a22','T+17','G']))
finally:
    src.write_text(orig,encoding='utf8')
print('전부 잡아냄' if ok else '놓친 것 있음'); raise SystemExit(0 if ok else 1)
