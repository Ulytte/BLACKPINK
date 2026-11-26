import json, html
from gen import *   # FONT, CSS, dip_svg, table, box, ln, dot, txt, inv, sch6, sch7, colors
SRC='/home/claude/rev/src/build-drawings-rev3.1/'
OUT='/home/claude/rev/out/'

def svg_open(h=430): return f'<svg viewBox="0 0 900 {h}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">'
def gbar(x,y,w,h,t,c='#9aa3ab'): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="#555"/>'+txt(x+w/2,y-6,t,13,'#333','middle',True)

def vessel(x,y,w,h,label):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#8aa" stroke-width="2"/>'
            f'<rect x="{x+4}" y="{y+40}" width="{w-8}" height="{h-44}" fill="#d2d2cc"/>'+txt(x+w/2,y-8,label,13,'#555','middle'))

# ---------- schematics ----------
def sch_ac(cfg):
    s=[svg_open(460)]
    s.append(box(10,60,90,40,'UNO D9',bold=True)); s.append(ln([(100,80),(160,80)],O)); s.append(dot(130,80,O))
    s.append(box(160,68,90,24,'R1 330 Ω',fs=14)); s.append(dot(275,80,O))
    s.append(f'<rect x="250" y="200" width="400" height="170" fill="none" stroke="#8aa" stroke-width="2"/><rect x="254" y="235" width="392" height="131" fill="#d2d2cc"/>')
    s.append(txt(450,390,'용기 · 페이스트에 전극이 직접 닿음',13,'#555','middle'))
    a_e1='A2' if cfg==1 else 'A0'; a_d9='A3' if cfg==1 else 'A2'
    s.append(txt(130,55,a_d9,14,B,'middle',True)); s.append(ln([(130,80),(130,62)],B))
    s.append(txt(275,55,a_e1,14,B,'middle',True)); s.append(ln([(275,80),(275,62)],B))
    if cfg in (1,2):
        for xx,nm,on in ((300,'E1',1),(400,'E2',cfg==1),(500,'E3',cfg==1),(600,'E4',1)):
            s.append(f'<rect x="{xx-6}" y="215" width="12" height="130" fill="{"#9aa3ab" if on else "#e2e2e2"}" stroke="#555"/>')
            s.append(txt(xx,365 if False else 232,'',1))
            s.append(txt(xx+12,228,nm,13,'#333' if on else '#aaa','start',True))
        x1,y1,x4,y4=300,215,600,215
        if cfg==2: s.append(txt(450,300,'E2·E3: 연결 안 함',13,'#777','middle'))
    else:
        s.append('<rect x="254" y="250" width="10" height="80" fill="#9aa3ab" stroke="#555"/><rect x="636" y="250" width="10" height="80" fill="#9aa3ab" stroke="#555"/>')
        s.append(txt(270,245,'E1 와셔',13,'#333','start',True)); s.append(txt(630,245,'E4 와셔',13,'#333','end',True))
        x1,y1,x4,y4=259,250,641,250
    s.append(ln([(250,80),(x1 if x1>260 else 290,80),(x1 if x1>260 else 290,180),(x1,180),(x1,y1)],O) if x1<260 else ln([(250,80),(x1,80),(x1,y1)],O))
    if cfg==1:
        s.append(ln([(400,215),(400,144)],B)); s.append(box(360,120,80,24,'UNO A0',fs=14))
        s.append(ln([(500,215),(500,144)],B)); s.append(box(460,120,80,24,'UNO A1',fs=14))
    s.append(ln([(x4,y4),(x4,110),(700,110)],O)); s.append(dot(670,110,O))
    if cfg!=1: s.append(txt(670,96,'A1',14,B,'middle',True))
    s.append(box(700,90,90,40,'UNO D8',bold=True))
    if cfg==1: s.append(txt(60,420,'E1·E4 = 전류 전극 (D9 → R1 → E1 … E4 → D8), E2·E3 = 전압 전극 (A0, A1)',15,'#333'))
    else: s.append(txt(60,420,'D9 → R1 → E1 → 페이스트 → E4 → D8',15,'#333'))
    s.append(txt(60,445,'D9·D8은 번갈아 HIGH/LOW (극성 반전) → 평균 직류 0',14,O))
    s.append('</svg>'); return '\n'.join(s)

def sch_rc(cfg):
    s=[svg_open()]
    s.append(inv(60,90,'74HC14 (1→2번)')); s.append(txt(52,80,'1번',13,'#555','end'))
    s.append(ln([(144,90),(200,90)],O)); s.append(dot(180,90,O)); s.append(txt(150,80,'2번',13,'#555'))
    s.append(box(200,78,90,24,'R1 330 Ω',fs=14))
    s.append(ln([(180,90),(180,30),(400,30)],G)); s.append(inv(400,30,'')); s.append(txt(392,20,'3번',13,'#555','end'))
    s.append(ln([(484,30),(560,30)],G)); s.append(txt(490,20,'4번',13,'#555')); s.append(box(560,12,100,36,'UNO D5',bold=True))
    s.append(vessel(300,180,320,170,'용기 (페이스트에 전극이 직접 닿음)'))
    if cfg==3:
        for xx,nm,c in ((340,'E1','#9aa3ab'),(410,'E2','#ddd'),(500,'E3','#ddd'),(580,'E4','#9aa3ab')): s.append(gbar(xx-6,205,12,120,nm,c))
        x4,y4=580,205
    else:
        s.append(gbar(304,235,10,85,'E1 와셔')); s.append(gbar(606,235,10,85,'E4 와셔')); x4,y4=611,235
    x1=340 if cfg==3 else 309; y1=205 if cfg==3 else 235
    s.append(ln([(290,90),(x1,90),(x1,y1)],O))
    s.append(ln([(x4,y4),(x4,160),(700,160),(700,390),(25,390),(25,90),(60,90)],O)); s.append(dot(700,300,O))
    s.append(ln([(700,300),(760,300)],K)); s.append(box(760,288,110,24,'CF 0.1 µF 필름',fs=13)); s.append(txt(815,335,'→ GND',14,K,'middle',True))
    s.append(txt(60,420,'R = R1 + 페이스트 저항, C = CF → 발진 주파수가 페이스트 저항에 따라 바뀜',14,O))
    s.append(txt(480,130,'전원: 14번 5 V, 7번 GND · 5·9·11·13번 → GND',13,R))
    s.append('</svg>'); return '\n'.join(s)

# ---------- mechanical ----------
def mech_s1(cfg):
    s=[svg_open(370)]
    x0,yb=110,300; k=4
    s.append(f'<rect x="{x0}" y="{yb-45*k}" width="{65*k}" height="{45*k}" fill="none" stroke="#8aa" stroke-width="2"/>')
    s.append(f'<rect x="{x0+3}" y="{yb-32*k}" width="{65*k-6}" height="{32*k-3}" fill="#d2d2cc"/>')
    s.append(f'<line x1="{x0}" y1="{yb-32*k}" x2="{x0+65*k}" y2="{yb-32*k}" stroke="#1D9E75" stroke-dasharray="6 4" stroke-width="2"/>')
    s.append(f'<rect x="{x0-20}" y="{yb-45*k-8}" width="{65*k+40}" height="8" fill="#e9d8a6" stroke="#555"/>')
    used={1:[1,1,1,1],2:[1,0,0,1],3:[1,0,0,1]}[cfg]
    for i in range(4):
        cx=x0+10*k+i*15*k
        s.append(f'<rect x="{cx-7}" y="{yb-45*k-20}" width="14" height="12" fill="#888"/>')
        s.append(f'<rect x="{cx-8}" y="{yb-45*k}" width="16" height="10" fill="#777"/>')
        s.append(f'<rect x="{cx-3}" y="{yb-45*k+10}" width="6" height="{25*k-10}" fill="#222"/>')
        s.append(f'<rect x="{cx-2.5}" y="{yb-45*k+25*k}" width="5" height="{10*k}" fill="#aab"/>')
        s.append(txt(cx,yb-45*k-28,f'E{i+1}',13,'#333' if used[i] else '#aaa','middle',True))
    s.append(txt(x0+65*k+30,yb-45*k-2,'자(25×2) = 용기 테두리 위',13))
    s.append(txt(x0+65*k+30,yb-32*k+4,'충전선 약 32 mm (28~36)',13,'#1D7A5B'))
    s.append(txt(x0+65*k+30,yb-10*k-20+4,'맨 끝 10 mm 노출, 위는 수축튜브',13))
    s.append(txt(x0+65*k+30,yb-4,'끝 ~ 바닥 약 10 mm',13))
    s.append(txt(x0+30*k,yb+24,'옆 단면 · 용기 높이 45 · 안쪽 폭 약 65 · 나사 간격 15',13,'#555','middle'))
    # top view
    tx,ty,t=640,70,3
    s.append(f'<rect x="{tx}" y="{ty}" width="{65*t}" height="{65*t}" fill="none" stroke="#8aa" stroke-width="2"/>')
    for i in range(4):
        cx=tx+10*t+i*15*t; s.append(f'<circle cx="{cx}" cy="{ty+32.5*t}" r="6" fill="{"#555" if used[i] else "#bbb"}"/>')
    s.append(f'<circle cx="{tx+32.5*t}" cy="{ty+52*t}" r="7" fill="none" stroke="{R}" stroke-width="2" stroke-dasharray="3 2"/>')
    s.append(txt(tx+32.5*t,ty+65*t+22,'위에서 본 모습 · 빨간 점선 = 온도센서 자리',13,'#555','middle'))
    s.append(txt(tx+32.5*t,ty+65*t+42,'(측정 전·후에만 넣기)',13,R,'middle'))
    s.append('</svg>'); return '\n'.join(s)

def front_box(x,y,k):
    return f'<rect x="{x}" y="{y}" width="{67*k}" height="{100*k}" fill="none" stroke="#8aa" stroke-width="2"/>'

def mech_s2():
    s=[svg_open(440)]; x,y,k=40,40,3.3
    yb=y+100*k
    s.append(f'<rect x="{x+2}" y="{yb-50*k}" width="{67*k-4}" height="{50*k-2}" fill="#d2d2cc"/>')
    s.append(front_box(x,y,k))
    s.append(f'<line x1="{x}" y1="{yb-50*k}" x2="{x+67*k}" y2="{yb-50*k}" stroke="#1D9E75" stroke-dasharray="6 4" stroke-width="2"/>')
    cx,cy=x+33.5*k,yb-25*k
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{12*k}" fill="#b9c0c6" stroke="#555"/><circle cx="{cx}" cy="{cy}" r="{2.25*k}" fill="#fff" stroke="#555"/>')
    s.append(txt(x+67*k+10,yb-50*k+5,'충전선 50',13,'#1D7A5B')); s.append(txt(x+67*k+10,cy+5,'구멍 중심 25 (Ø4.5)',13))
    s.append(txt(x+67*k+10,y+12,'높이 100',13)); s.append(txt(x+33.5*k,yb+22,'벽 정면 · 폭 67 · 구멍은 폭 중앙',13,'#555','middle'))
    # stack
    sx,cyy=400,215
    parts=[('볼트 머리 M4×40',22,7,'#888'),('M4 와셔',8,9,'#b9c0c6'),('M8 와셔',10,16,'#b9c0c6'),('M12 와셔 = 전극',12,24,'#7fb8a8'),
           ('고무 와셔',10,18,'#e07b5a'),('용기 벽 (Ø4.5 구멍)',8,60,'#c8c2e8'),('M12 와셔 (보강)',12,24,'#b9c0c6'),('M4 와셔',8,9,'#b9c0c6'),
           ('너트 1 (살짝)',18,7,'#888'),('링 단자 → 전선',6,9,'#7fb8a8'),('너트 2 (꽉)',18,7,'#888')]
    s.append(f'<rect x="{sx}" y="{cyy-6}" width="300" height="12" fill="none" stroke="#333"/>')
    xx=sx
    for i,(nm,w,d,c) in enumerate(parts):
        hh=min(d*5,150); cx=xx+w/2
        s.append(f'<rect x="{xx}" y="{cyy-hh/2}" width="{w}" height="{hh}" fill="{c}" stroke="#444"/>')
        up=(i%2==0); ny=cyy-120 if up else cyy+120
        s.append(f'<line x1="{cx}" y1="{cyy-hh/2 if up else cyy+hh/2}" x2="{cx}" y2="{ny+(10 if up else -10)}" stroke="#999" stroke-dasharray="3 3"/>')
        s.append(f'<circle cx="{cx}" cy="{ny}" r="10" fill="#fff" stroke="#555"/>'+txt(cx,ny+5,str(i+1),12,'#333','middle',True))
        s.append(txt(715,70+i*24,f'{i+1}. {nm}',14,'#333'))
        xx+=w+12
    s.append(txt(400,cyy+165,'왼쪽 = 용기 안 (페이스트) · 오른쪽 = 용기 밖',13,'#555'))
    s.append(txt(400,cyy+185,'두께는 과장, 지름만 비율 · 1~4번이 페이스트에 닿는 전극',13,'#555'))
    s.append('</svg>'); return '\n'.join(s)

def mech_s3():
    s=[svg_open(440)]; x,y,k=60,40,3.3; yb=y+100*k
    s.append(f'<rect x="{x+2}" y="{yb-50*k}" width="{67*k-4}" height="{50*k-2}" fill="#d2d2cc"/>')
    s.append(front_box(x,y,k))
    s.append(f'<line x1="{x}" y1="{yb-50*k}" x2="{x+67*k}" y2="{yb-50*k}" stroke="#1D9E75" stroke-dasharray="6 4" stroke-width="2"/>')
    s.append(f'<rect x="{x+23.5*k}" y="{yb-45*k}" width="{20*k}" height="{40*k}" fill="#d9873b" stroke="#8a4b16"/>')
    s.append(f'<rect x="{x+43.5*k-5*k}" y="{yb-45*k-10*k}" width="{5*k}" height="{10*k}" fill="#d9873b" stroke="#8a4b16"/>')
    s.append(txt(x+67*k+10,yb-50*k+5,'충전선 50',13,'#1D7A5B')); s.append(txt(x+67*k+10,yb-45*k+5,'구리 위끝 45',13))
    s.append(txt(x+67*k+10,yb-5*k+5,'구리 아래끝 5',13)); s.append(txt(x+67*k+10,y+12,'높이 100',13))
    s.append(txt(x+33.5*k,yb+22,'바깥 벽 정면 · 구리 20×40, 폭 중앙 · 꼬리 5×10',13,'#555','middle'))
    tx,ty,t=600,150,3
    s.append(f'<rect x="{tx}" y="{ty}" width="{67*t}" height="{67*t}" fill="none" stroke="#8aa" stroke-width="2"/>')
    s.append(f'<rect x="{tx-6}" y="{ty+23.5*t}" width="6" height="{20*t}" fill="#d9873b"/><rect x="{tx+67*t}" y="{ty+23.5*t}" width="6" height="{20*t}" fill="#d9873b"/>')
    s.append(txt(tx+33.5*t,ty+67*t+22,'위에서 본 모습 · 마주 보는 바깥 벽',13,'#555','middle'))
    s.append(txt(tx+33.5*t,ty+67*t+42,'구리는 페이스트에 절대 안 닿음',13,R,'middle'))
    s.append('</svg>'); return '\n'.join(s)

TITLES={1:'구성 1 · S1 자 프로브 · 4전극 + AC (칩 없음)',2:'구성 2 · S1 자 프로브 · 2전극 + AC (칩 없음)',
 3:'구성 3 · S1 자 프로브 · 2전극 + RC — 칩: 74HC14',4:'구성 4 · S2 와셔 전극 · 2전극 + AC (칩 없음)',
 5:'구성 5 · S2 와셔 전극 · 2전극 + RC — 칩: 74HC14',6:'구성 6 · S3 구리테이프 · 비접촉 + AC — 칩: LM358',
 7:'구성 7 · S3 구리테이프 · 비접촉 + RC — 칩: 74HC14'}
SENSOR={1:'S1',2:'S1',3:'S1',4:'S2',5:'S2',6:'S3',7:'S3'}

def hc14(H,pin1,pin2):
    g=lambda k:H[k]
    return dip_svg('74HC14',{1:(pin1,g('U1.1'),O),2:(pin2,g('U1.2'),O),3:('입력 ← 2번',g('U1.3'),O),4:('출력 → UNO D5',g('U1.4'),G),
        5:('입력 → GND',g('U1.5'),K),6:('출력 (비움)',g('U1.6'),N),7:('GND',g('U1.7'),K),8:('출력 (비움)',g('U1.8'),N),
        9:('입력 → GND',g('U1.9'),K),10:('출력 (비움)',g('U1.10'),N),11:('입력 → GND',g('U1.11'),K),12:('출력 (비움)',g('U1.12'),N),
        13:('입력 → GND',g('U1.13'),K),14:('VCC 5 V (CD 0.1 µF)',g('U1.14'),R)},14,'1행 쪽(위)')

def lm358(H):
    return dip_svg('LM358',{1:('출력A → A0, RF, CF',H['U1.1'],B),2:('−입력A ← 전극 B, RF, CF',H['U1.2'],B),
        3:('+입력A ← BIAS 1.6 V',H['U1.3'],B),4:('GND',H['U1.4'],K),5:('+입력B ← BIAS',H['U1.5'],B),
        6:('−입력B → 7번과 연결',H['U1.6'],N),7:('출력B → 6번과 연결',H['U1.7'],N),8:('V+ 5 V (CD 0.1 µF)',H['U1.8'],R)},8,'1행 쪽(위)')

def unomap(d):
    H=d['holes']; rows=[]
    for net,v in d['nets'].items():
        for e in v['ends']:
            if e.startswith('UNO.'): rows.append([e.replace('UNO.',''),net,H.get(e,'')])
    return rows

MECH_STEPS={
 'S1':['플라스틱 자(약 25 × 2 mm) 가운데에 <b>Ø4 구멍 4개</b>를 <b>15 mm 간격</b>으로 한 줄로 뚫어.',
       'M4 × 40 SUS 나사를 위에서 꽂고, 자 아래에서 M4 너트로 고정해.',
       '나사 아래쪽 <b>끝 10 mm만 남기고</b> 위쪽 줄기에 수축튜브(약 25 mm)를 씌워. 끝 10 mm만 페이스트에 닿는 전극이야.',
       '용기: PET 사각 용기(67 × 67 × 100)를 <b>높이 45 mm로 잘라서</b> 써. 원래 둥근 PP 컵(높이 45, 바닥 Ø ≥70)이 있으면 그대로 써도 돼.',
       '자를 용기 테두리에 올려. 나사 줄이 용기 폭 가운데에 오게 하고, 양 끝 나사가 벽에서 약 10 mm 떨어지게 해.',
       '페이스트는 약 32 mm(28~36) 높이까지. 나사 끝 10 mm가 완전히 잠겨야 해.'],
 'S2':['PET 사각 용기(67 × 67 × 100)의 마주 보는 두 벽, <b>폭 중앙 · 안쪽 바닥에서 25 mm</b>에 <b>Ø4.5 구멍</b>을 뚫어 (작게 열로 뚫고 넓히기, 테두리 다듬기).',
       '안쪽에서 볼트에 차례로: <b>볼트 머리 → M4 → M8 → M12(전극) → 고무 와셔</b>, 그 볼트를 벽 구멍으로 밀어 넣기.',
       '바깥쪽에서: <b>M12 → M4 → 너트1</b>(손으로 살짝, 고무가 살짝 눌릴 정도) <b>→ 링 단자 → 너트2</b>(꽉).',
       '반대쪽 벽도 똑같이. 양쪽 와셔 면이 마주 보게 (±2~3 mm는 괜찮음).',
       '<b>물을 50 mm까지 채우고 하루</b> 두어 새는지 확인. 새면 고무 와셔 다시 맞추기.',
       '충전선 50 mm를 바깥에 네임펜으로 표시.'],
 'S3':['PET 사각 용기(67 × 67 × 100) 바깥 벽을 알코올로 닦기.',
       '구리테이프 20 × 40 mm 두 장, 위 모서리에 꼬리 5 × 10 mm 남기기.',
       '마주 보는 두 <b>바깥</b> 벽의 폭 중앙, 바닥에서 <b>5~45 mm</b>에 기포 없이 붙이기.',
       '꼬리를 바깥으로 접고 집게선 연결, 테이프 위는 투명 테이프로 덮기.',
       '충전선 50 mm 표시. 페이스트가 바깥 구리에 묻으면 바로 닦기.']}

CHANGES={
 'S1':['용기: "PP cup H45, 바닥 Ø ≥70" → PET 사각 용기를 높이 45 mm로 자른 것 (원래 컵이 있으면 그대로). 안쪽 폭 약 65 mm라 나사 줄(45 mm)과 벽 사이 약 10 mm 확보.',
       '온도센서: "측정 중 잠김" → <b>측정 직전·직후에만</b> 넣고 측정 중에는 뺌. 금속 끝이 페이스트에 닿으면 세 번째 전극이 되어 전류가 샐 수 있음.',
       '회로·구멍 번호·점퍼: Rev 3.1과 동일 (자동 연결 검증 통과).'],
 'S2':['볼트: M4 × 12 (벽에 나사산 내기) → <b>M4 × 40 SUS 관통 볼트</b>. 구멍 Ø3.5 → <b>Ø4.5</b>.',
       '구멍 높이: 안쪽 바닥에서 16 mm → <b>25 mm</b>. 충전: ≥35 mm → <b>50 mm</b>.',
       '밀봉: 글루건 → <b>고무 와셔</b> (M12 전극 와셔와 벽 사이) + 바깥쪽 M12 보강 와셔.',
       '전선: 바깥 나사 머리에 집게 → <b>너트1과 너트2 사이 링 단자</b>.',
       '용기: 안쪽 폭 40~50 PP → <b>PET 사각 67 × 67 × 100</b>. M12 와셔 지름은 구매품 실측(도면은 27, 일반 규격 약 24).',
       '온도센서: 측정 중 잠김 → <b>측정 직전·직후에만</b>.',
       '회로·구멍 번호·점퍼: Rev 3.1과 동일 (자동 연결 검증 통과).'],
 'S3':['용기: "PP cup H45, 바닥 Ø ≥70" → <b>PET 사각 67 × 67 × 100</b>, 충전선 50 mm. 구리 20 × 40 mm는 바닥에서 5~45 mm.',
       '칩(U1)을 1단계로 올리고 핀별 연결을 그림으로 표시.',
       '회로·구멍 번호·점퍼: Rev 3.1과 동일 (자동 연결 검증 통과).']}

def bom(cfg,d):
    rows=[['Arduino Uno (R3 호환)',1],['브레드보드 830홀',1],['I2C LCD 16×2',1],['방수 온도센서 DS18B20',1]]
    s=SENSOR[cfg]
    if s=='S1': rows+= [['PET 사각 용기 → 높이 45 mm로 자름 (또는 PP 컵 H45, 바닥 Ø≥70)',1],['플라스틱 자 약 25 × 2 mm',1],
                       ['SUS M4 × 40 나사',4],['SUS M4 너트',4],['수축튜브 Ø5, 약 25 mm',4]]
    if s=='S2': rows+= [['PET 사각 용기 67 × 67 × 100',1],['SUS M4 × 40 볼트',2],['SUS M4 너트',4],['M4 와셔',4],['M8 와셔',2],
                       ['M12 와셔 (안쪽 전극 2 + 바깥 보강 2)',4],['고무 와셔 (안지름 4~5, 바깥 ≤ M12 와셔)',2],['M4 링 단자',2]]
    if s=='S3': rows+= [['PET 사각 용기 67 × 67 × 100',1],['구리테이프 20 × 40 + 꼬리',2],['투명 테이프',1]]
    if any(k.startswith('U1.') for k in d['holes']):
        rows.append(['IC U1 — '+('LM358N DIP-8' if cfg==6 else '74HC14 DIP-14'),1])
    for p,v,_ in d['parts']: rows.append([f'{p} {v}',1])
    for r in d['BOM']:
        n=r[1]
        if 'Alligator' in n: rows.append(['집게선 '+r[2].replace('cm','cm').replace('taped down','테이프 고정'),r[3]])
        if 'Jumper wires' in n: rows.append(['점퍼선 ('+r[2].replace('board links','보드').replace('external / clip leads','외부·집게')+')',r[3]])
        if 'Calibration' in n: rows.append(['보정용 저항 100 Ω (전극 대신 시험용)',r[3]])
        if 'Optional reference' in n: rows.append(['선택: 기준 커패시터 10/22/47/100 pF 중 1',r[3]])
        if n=='Optional ADS1115': rows.append(['선택: ADS1115 (별도)',r[3]])
    return [[i+1,a,b] for i,(a,b) in enumerate(rows)]

def checks(cfg):
    if cfg in (1,2,4): return ['전원 켠 뒤 측정 안 할 때: D9·D8 모두 LOW → A0~A3 모두 약 0 V',
        '집게선을 전극 대신 <b>100 Ω 저항</b> 양 끝(E1·E4)에 물리고 측정 → 계산값이 약 100 Ω이면 회로·코드 정상',
        '그다음 소금물 2~3가지 농도: 소금이 많을수록 저항이 단조롭게 감소하는지']+(['구성 1: E2·E3 집게가 E1·E4와 섞이지 않았는지 (A0=E2, A1=E3)'] if cfg==1 else [])
    if cfg in (3,5): return ['칩 14번 핀: <b>5 V</b>, 7번: <b>0 V</b>, 5·9·11·13번: <b>0 V</b>',
        '집게선을 <b>100 Ω 보정 저항</b>에 물리고 D5 주파수가 안정적으로 나오는지 (0이면 칩 방향·전원 확인)',
        '칩 2번 핀을 멀티미터 DC로: 0 V나 5 V가 아닌 중간값이면 발진 중']
    if cfg==6: return ['칩 8번 핀: <b>5 V</b>, 4번: <b>0 V</b>','칩 3번·5번 핀: <b>약 1.6 V</b> (BIAS)',
        '칩 1번 핀 (측정 안 할 때): <b>약 1.6 V</b>. 0 V나 5 V에 붙어 있으면 2번 핀 쪽 배선 확인',
        '전해 커패시터 CB: <b>+다리 = a37(BIAS)</b>, −다리 = T−29(GND)']
    return ['칩 14번 핀: <b>5 V</b>, 7번: <b>0 V</b>, 5·9·11·13번: <b>0 V</b>','전극 연결 후 칩 2번 핀 멀티미터 DC: <b>중간값</b>이면 발진 중',
        'Arduino D5 주파수가 0이 아니면 정상 (빈 용기에서도 발진해야 함)']

def page(cfg):
    d=json.load(open(SRC+f'wiring-{cfg}.json')); H=d['holes']; s=SENSOR[cfg]
    chip=any(k.startswith('U1.') for k in H)
    if cfg==6: p1=('① 칩 핀 연결 (가장 먼저 꽂을 것)', lm358(H))
    elif cfg==7: p1=('① 칩 핀 연결 (가장 먼저 꽂을 것)', hc14(H,'입력 ← 전극 A, RF','출력 → RF, 3번'))
    elif cfg in (3,5): p1=('① 칩 핀 연결 (가장 먼저 꽂을 것)', hc14(H,'입력 ← E4, CF 0.1 µF','출력 → R1 330 Ω, 3번'))
    else: p1=('① Arduino 핀 연결 (이 구성은 칩 없음)', table(unomap(d),['Arduino 핀','넷','브레드보드 구멍']))
    sch={1:sch_ac,2:sch_ac,4:sch_ac,3:sch_rc,5:sch_rc}.get(cfg)
    schs=sch(cfg) if sch else (sch6() if cfg==6 else sch7())
    mech={'S1':lambda:mech_s1(cfg),'S2':mech_s2,'S3':mech_s3}[s]()
    if chip:
        alert=('<b>칩(U1)이 꼭 들어가야 하는 구성이야.</b> Rev 3.1에도 있었지만 "U1"로만 적혀 있어서 빠뜨리기 쉬웠어. '
               '칩이 없으면 아무 신호도 안 나와. 칩부터 꽂고, 반달 홈이 1행 쪽(위)을 보게 해.')
    else:
        alert='<b>이 구성은 칩이 필요 없어.</b> Arduino D9·D8이 직접 전극을 번갈아 구동하고, A0~A3로 전압을 읽어. 브레드보드에는 저항(RT, R1)만 꽂아.'
    csteps=(['<b>칩부터 꽂기.</b> 가운데 홈에 걸치고 반달 홈이 1행 쪽. 왼쪽 줄 = 1번부터, 오른쪽 줄 = 마지막 번호부터.'] if chip else [])+[
        '전원 레일 점퍼(표 1~6번)와 칩·부품 전원 점퍼를 꽂기.','부품 표대로 저항·커패시터 꽂기. 다리 두 개가 같은 행이면 합선.',
        '나머지 신호 점퍼를 표 순서대로.','Arduino·LCD·DS18B20·집게선 연결. 집게선은 짧게, 테이프로 고정.',
        '<b>USB 연결 전에</b> '+('칩 방향과 ' if chip else '')+'5 V·GND 레일을 한 번 더 확인.']
    partsrows=[[p,v,H.get(p+'.1',''),H.get(p+'.2','')] for p,v,_ in d['parts']]
    pinrows=[[k.replace('U1.','')+'번',v] for k,v in sorted([(k,v) for k,v in H.items() if k.startswith('U1.')],key=lambda kv:int(kv[0].split('.')[1]))]
    jrows=[[i+1,j[1],j[2],j[0]] for i,j in enumerate(d['full_jumper_schedule'])]
    loc=(f'<b>칩 U1 핀</b>{table(pinrows,["핀","구멍"])}<br>' if chip else '')+f'<b>저항·커패시터</b>{table(partsrows,["부품","값","다리 1","다리 2"])}'
    doc=f"""<!doctype html><html lang="ko"><meta charset="utf-8"><style>{CSS} h3{{margin:10px 0 4px}}</style><body><div class="sheet">
<header><h1>{TITLES[cfg]}</h1><small>Rev 3.2 · 실제 구매품 기준 수정판 · 회로 연결은 Rev 3.1과 동일(자동 검증)<br>치수 mm · 실제 비율 아님</small></header>
<div class="alert">{alert}</div>
<div class="grid">
<div class="panel"><h2>{p1[0]}</h2><div class="body">{p1[1]}</div></div>
<div class="panel"><h2>② 회로 원리도</h2><div class="body">{schs}</div></div>
<div class="panel full"><h2>③ 센서({s}) 기구 · 치수</h2><div class="body" style="display:flex;justify-content:center"><div style="width:1150px">{mech}</div></div></div>
<div class="panel"><h2>④ 만드는 순서</h2><div class="body"><h3>센서</h3><ol>{''.join(f'<li>{x}</li>' for x in MECH_STEPS[s])}</ol>
<h3>회로</h3><ol>{''.join(f'<li>{x}</li>' for x in csteps)}</ol>
<h3>전원 켠 뒤 확인 (멀티미터 검은 리드 = GND)</h3><ul>{''.join(f'<li>{x}</li>' for x in checks(cfg))}</ul></div></div>
<div class="panel"><h2>⑤ 부품 위치 (구멍 번호)</h2><div class="body">{loc}<br><b>부품 목록 (BOM)</b>{table(bom(cfg,d),['No.','부품','수량'])}</div></div>
<div class="panel full"><h2>⑥ 점퍼·외부선 전체 목록 (Rev 3.1과 동일)</h2><div class="body" style="columns:3;column-gap:24px">{table(jrows,['No.','시작','끝','넷'])}</div></div>
<div class="panel full"><h2>⑦ Rev 3.1 대비 수정 사항</h2><div class="body"><ul>{''.join(f'<li>{x}</li>' for x in CHANGES[s])}</ul></div></div>
</div></div></body></html>"""
    open(OUT+f'config-{cfg}-rev3.2.html','w').write(doc)

if __name__=='__main__':
    for c in range(1,8): page(c)
    print('ok')
