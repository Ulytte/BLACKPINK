import json, html
SRC='/home/claude/rev/src/build-drawings-rev3.1/'
FONT="'Noto Sans CJK KR','Noto Sans KR',sans-serif"

def dip_svg(name, pins, n, notch_label):
    # pins: dict pin->(label, hole, color)
    half=n//2; pitch=58; top=70; chipw=150 if n==8 else 210; cx=470
    h=top+half*pitch+40
    x0=cx-chipw//2; x1=cx+chipw//2
    s=[f'<svg viewBox="0 0 940 {h+30}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">']
    s.append(f'<rect x="{x0}" y="{top-30}" width="{chipw}" height="{half*pitch+20}" rx="8" fill="#222" />')
    s.append(f'<path d="M{cx-18} {top-30} A18 18 0 0 0 {cx+18} {top-30}" fill="#fff"/>')
    s.append(f'<text x="{cx}" y="{top+half*pitch/2-6}" fill="#fff" font-size="24" font-weight="700" text-anchor="middle">{name}</text>')
    s.append(f'<text x="{cx}" y="{top+half*pitch/2+24}" fill="#ddd" font-size="16" text-anchor="middle">위에서 본 모습</text>')
    s.append(f'<text x="{cx}" y="{top-42}" fill="#c0392b" font-size="17" text-anchor="middle">▲ 홈(notch) = {notch_label}</text>')
    s.append(f'<circle cx="{x0+50}" cy="{top-12}" r="6" fill="#fff"/>')
    for i in range(half):
        # left pin i+1
        y=top+i*pitch
        for side,p in (('L',i+1),('R',n-i)):
            lab,hole,col=pins[p]
            if side=='L':
                s.append(f'<rect x="{x0-22}" y="{y-8}" width="22" height="16" fill="#bbb"/>')
                s.append(f'<text x="{x0+12}" y="{y+6}" fill="#fff" font-size="16" font-weight="700">{p}</text>')
                s.append(f'<line x1="{x0-22}" y1="{y}" x2="{x0-60}" y2="{y}" stroke="{col}" stroke-width="3"/>')
                s.append(f'<text x="{x0-66}" y="{y-4}" font-size="17" font-weight="700" fill="{col}" text-anchor="end">{html.escape(lab)}</text>')
                s.append(f'<text x="{x0-66}" y="{y+17}" font-size="14" fill="#555" text-anchor="end">구멍 {hole}</text>')
            else:
                s.append(f'<rect x="{x1}" y="{y-8}" width="22" height="16" fill="#bbb"/>')
                s.append(f'<text x="{x1-12}" y="{y+6}" fill="#fff" font-size="16" font-weight="700" text-anchor="end">{p}</text>')
                s.append(f'<line x1="{x1+22}" y1="{y}" x2="{x1+60}" y2="{y}" stroke="{col}" stroke-width="3"/>')
                s.append(f'<text x="{x1+66}" y="{y-4}" font-size="17" font-weight="700" fill="{col}">{html.escape(lab)}</text>')
                s.append(f'<text x="{x1+66}" y="{y+17}" font-size="14" fill="#555">구멍 {hole}</text>')
    s.append('</svg>')
    return '\n'.join(s)

def table(rows, head):
    t='<table><tr>'+''.join(f'<th>{h}</th>' for h in head)+'</tr>'
    for r in rows: t+='<tr>'+''.join(f'<td>{html.escape(str(c))}</td>' for c in r)+'</tr>'
    return t+'</table>'

CSS=f"""*{{box-sizing:border-box}}body{{margin:0;font-family:{FONT};color:#17324d;background:#fff}}
.sheet{{width:1900px;padding:28px 34px}}header{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:5px solid #153e67;padding-bottom:10px}}
h1{{font-size:34px;margin:0}}header small{{font-size:17px;text-align:right;color:#444}}
.alert{{margin:16px 0;padding:14px 18px;border:3px solid #c0392b;background:#fdecea;border-radius:10px;font-size:20px;line-height:1.5}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.panel{{border:2px solid #b9cbdc;border-radius:10px;overflow:hidden}}.panel h2{{background:#173f66;color:#fff;margin:0;padding:10px 16px;font-size:22px}}
.body{{padding:12px 16px;font-size:18px;line-height:1.5}}table{{border-collapse:collapse;width:100%;font-size:16px}}th{{background:#e9f0f6;text-align:left}}th,td{{border:1px solid #d1dce6;padding:4px 8px}}
ol li{{margin-bottom:6px}}.ok{{color:#1e7d32;font-weight:700}}.full{{grid-column:1/-1}}code{{background:#f1f3f5;padding:0 4px;border-radius:4px}}"""

R='#d62728'; K='#222'; O='#e67e22'; B='#1f6fb2'; G='#2e8b57'; Y='#b8860b'; N='#999'

def box(x,y,w,h,t,fill='#fff',stroke='#17324d',fs=16,bold=False):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'<text x="{x+w/2}" y="{y+h/2+fs*0.35}" font-size="{fs}" text-anchor="middle" font-weight="{700 if bold else 400}">{t}</text>')
def ln(pts,c=K,w=2.2):
    return f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{c}" stroke-width="{w}"/>'
def dot(x,y,c=K): return f'<circle cx="{x}" cy="{y}" r="5" fill="{c}"/>'
def txt(x,y,t,fs=15,c='#17324d',a='start',b=False): return f'<text x="{x}" y="{y}" font-size="{fs}" fill="{c}" text-anchor="{a}" font-weight="{700 if b else 400}">{t}</text>'
def cup(x,label_left,label_right):
    s=[f'<rect x="{x}" y="120" width="150" height="190" fill="none" stroke="#8aa" stroke-width="2"/>',
       f'<rect x="{x+6}" y="175" width="138" height="132" fill="#c9c9c4"/>',
       txt(x+75,250,'페이스트',15,'#444','middle'),
       txt(x+75,112,'PET 용기 (벽)',14,'#555','middle'),
       f'<rect x="{x-12}" y="185" width="12" height="110" fill="#d9873b"/>',
       f'<rect x="{x+150}" y="185" width="12" height="110" fill="#d9873b"/>',
       txt(x-6,330,label_left,15,'#a0522d','middle',True), txt(x+156,330,label_right,15,'#a0522d','middle',True)]
    return '\n'.join(s)

def sch6():
    s=[f'<svg viewBox="0 0 900 450" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">']
    s.append(box(10,180,90,40,'UNO D9',bold=True))
    s.append(ln([(100,200),(130,200)],O)); s.append(box(130,188,80,24,'R1 1 kΩ',fs=14))
    s.append(ln([(210,200),(228,200),(228,240),(238,240)],O))
    s.append(cup(250,'전극 A','전극 B'))
    s.append(ln([(412,240),(440,240),(440,200),(520,200)],B)); s.append(dot(470,200,B))
    s.append(f'<polygon points="520,170 520,290 620,230" fill="#eef4fb" stroke="#17324d" stroke-width="2"/>')
    s.append(txt(545,235,'LM358 A',15,b=True)); s.append(txt(526,206,'−',18,b=True)); s.append(txt(526,266,'+',18,b=True))
    s.append(txt(500,192,'2번',13,'#555','end')); s.append(txt(500,282,'3번',13,'#555','end')); s.append(txt(628,222,'1번',13,'#555'))
    s.append(ln([(470,200),(470,60),(530,60)],B)); s.append(box(530,48,100,24,'CF 47 pF',fs=14)); s.append(ln([(630,60),(690,60),(690,230)],B))
    s.append(ln([(470,110),(530,110)],B)); s.append(box(530,98,100,24,'RF 10 MΩ',fs=14)); s.append(ln([(630,110),(690,110)],B))
    s.append(ln([(620,230),(730,230)],B)); s.append(dot(690,230,B)); s.append(box(730,210,100,40,'UNO A0',bold=True))
    s.append(ln([(520,260),(480,260),(480,345)],B))
    s.append(txt(290,350,'5 V',15,R,'middle',True)); s.append(ln([(310,345),(330,345)],R)); s.append(box(330,333,100,24,'RB1 10 kΩ',fs=14))
    s.append(ln([(430,345),(540,345)],B)); s.append(dot(480,345,B)); s.append(box(540,333,100,24,'RB2 4.7 kΩ',fs=14))
    s.append(ln([(640,345),(665,345)],K)); s.append(txt(670,350,'GND',15,K,b=True))
    s.append(ln([(480,345),(480,380)],B)); s.append(box(440,380,80,24,'CB 10 µF',fs=14)); s.append(ln([(480,404),(480,420)],K)); s.append(txt(480,438,'GND (− 다리)',13,K,'middle'))
    s.append(txt(490,325,'BIAS ≈ 1.6 V → 3번, 5번',14,B))
    s.append(txt(700,300,'B쪽(5·6·7번): 5번 = BIAS,',14,'#555')); s.append(txt(700,320,'6번–7번 서로 연결',14,'#555'))
    s.append(txt(700,370,'전원: 8번 = 5 V, 4번 = GND',14,R,b=True)); s.append(txt(700,390,'CD 0.1 µF: 8번 줄 ↔ GND',14,'#555'))
    s.append('</svg>'); return '\n'.join(s)

def inv(x,y,label):
    return (f'<polygon points="{x},{y-30} {x},{y+30} {x+70},{y}" fill="#eef4fb" stroke="#17324d" stroke-width="2"/>'
            f'<circle cx="{x+77}" cy="{y}" r="7" fill="#fff" stroke="#17324d" stroke-width="2"/>'+txt(x+28,y+52,label,13,'#555','middle'))

def sch7():
    s=[f'<svg viewBox="0 0 900 450" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">']
    s.append(cup(60,'전극 B','전극 A'))
    s.append(ln([(48,240),(30,240),(30,390)],K)); s.append(txt(30,410,'GND',15,K,'middle',True))
    s.append(ln([(222,240),(250,240),(250,200),(320,200)],O)); s.append(dot(280,200,O))
    s.append(inv(320,200,'74HC14 (1→2번)')); s.append(txt(312,190,'1번',13,'#555','end'))
    s.append(ln([(404,200),(470,200)],O)); s.append(dot(440,200,O)); s.append(txt(410,190,'2번',13,'#555'))
    s.append(ln([(280,200),(280,110),(330,110)],O)); s.append(box(330,98,90,24,'RF 1 MΩ',fs=14)); s.append(ln([(420,110),(440,110),(440,200)],O))
    s.append(inv(470,200,'74HC14 (3→4번)')); s.append(txt(462,190,'3번',13,'#555','end'))
    s.append(ln([(554,200),(640,200)],G)); s.append(txt(560,190,'4번',13,'#555')); s.append(box(640,180,110,40,'UNO D5',bold=True))
    s.append(txt(640,250,'주파수 측정 (펄스 수 세기)',14,G))
    s.append(txt(330,300,'전원: 14번 = 5 V, 7번 = GND',15,R,b=True))
    s.append(txt(330,325,'안 쓰는 입력 5·9·11·13번 → GND',14,'#555'))
    s.append(txt(330,348,'안 쓰는 출력 6·8·10·12번 → 비워 둠',14,'#555'))
    s.append(txt(330,371,'CD 0.1 µF: 14번 줄 ↔ GND',14,'#555'))
    s.append(txt(330,400,'전극 사이 정전용량 C와 RF가 발진 주파수를 정함',14,O))
    s.append('</svg>'); return '\n'.join(s)

def sheet(cfg):
    d=json.load(open(SRC+f'wiring-{cfg}.json')); H=d['holes']
    if cfg==6:
        title='구성 6 · 비접촉(구리테이프) + AC 전하증폭기 — 칩: LM358'
        chip=dip_svg('LM358',{
            1:('출력A → A0, RF, CF',H['U1.1'],B),2:('−입력A ← 전극 B, RF, CF',H['U1.2'],B),
            3:('+입력A ← BIAS 1.6 V',H['U1.3'],B),4:('GND',H['U1.4'],K),
            5:('+입력B ← BIAS',H['U1.5'],B),6:('−입력B → 7번과 연결',H['U1.6'],N),
            7:('출력B → 6번과 연결',H['U1.7'],N),8:('V+ 5 V (CD 0.1 µF)',H['U1.8'],R)},8,'1행 쪽(위)')
        sch=sch6()
        check=['칩 8번 핀 ↔ GND: <b>5 V</b>','칩 4번 핀: <b>0 V</b>','칩 3번·5번 핀: <b>약 1.6 V</b> (BIAS)',
               '칩 1번 핀 (측정 안 할 때): <b>약 1.6 V</b>. 0 V나 5 V에 붙어 있으면 2번 핀 쪽 배선 확인',
               '전해 커패시터 CB: <b>+다리 = a37(BIAS)</b>, −다리 = T−29(GND)']
        partsrows=[[p,v,H.get(p+'.1',''),H.get(p+'.2','')] for p,v,_ in d['parts']]
    else:
        title='구성 7 · 비접촉(구리테이프) + RC 발진기 — 칩: 74HC14'
        g=lambda k:H[k]
        chip=dip_svg('74HC14',{
            1:('입력 ← 전극 A, RF',g('U1.1'),O),2:('출력 → RF, 3번',g('U1.2'),O),3:('입력 ← 2번',g('U1.3'),O),
            4:('출력 → UNO D5',g('U1.4'),G),5:('입력 → GND',g('U1.5'),K),6:('출력 (비움)',g('U1.6'),N),
            7:('GND',g('U1.7'),K),8:('출력 (비움)',g('U1.8'),N),9:('입력 → GND',g('U1.9'),K),
            10:('출력 (비움)',g('U1.10'),N),11:('입력 → GND',g('U1.11'),K),12:('출력 (비움)',g('U1.12'),N),
            13:('입력 → GND',g('U1.13'),K),14:('VCC 5 V (CD 0.1 µF)',g('U1.14'),R)},14,'1행 쪽(위)')
        sch=sch7()
        check=['칩 14번 핀: <b>5 V</b>, 7번 핀: <b>0 V</b>','칩 5·9·11·13번 핀: <b>0 V</b> (GND에 묶였는지)',
               '전극 연결 후 칩 2번 핀을 멀티미터 DC로: <b>0 V나 5 V가 아닌 중간값</b>이면 발진 중',
               'Arduino에서 D5 주파수가 0이 아니면 정상 (빈 용기에서도 발진해야 함)']
        partsrows=[[p,v,H.get(p+'.1',''),H.get(p+'.2','')] for p,v,_ in d['parts']]
    pinrows=[[k.replace('U1.','')+'번',v] for k,v in sorted([(k,v) for k,v in H.items() if k.startswith('U1.')],key=lambda kv:int(kv[0].split('.')[1]))]
    jrows=[[i+1,j[1],j[2],j[0]] for i,j in enumerate(d['full_jumper_schedule'])]
    steps=['<b>칩부터 꽂기.</b> 브레드보드 가운데 홈을 칩이 가로지르게 걸치고, 칩의 <b>반달 홈(또는 점)이 1행 쪽</b>을 보게 해. 왼쪽 줄 = 1번부터, 오른쪽 줄 = 마지막 번호부터 (오른쪽 표·그림 참고).',
           '전원 레일 점퍼(표 1~6번)와 칩 전원 점퍼(5 V, GND)를 꽂아.',
           '부품 표대로 저항·커패시터를 꽂아. 다리 두 개가 <b>같은 행에 들어가면 안 돼</b> (합선).',
           '나머지 신호 점퍼를 표 순서대로 꽂아.',
           'Arduino·LCD·DS18B20·전극 집게선을 연결해. 집게선은 10 cm 이하로 짧게, 테이프로 고정.',
           '<b>USB 연결 전에</b> 칩 방향을 한 번 더 확인. 그다음 전원 켜고 아래 "전원 켠 뒤 확인"을 해.']
    html_=f"""<!doctype html><html lang="ko"><meta charset="utf-8"><style>{CSS}</style><body><div class="sheet">
<header><h1>{title}</h1><small>Rev 3.2 · 칩 강조판 · 넷리스트는 Rev 3.1과 동일(자동 검증)<br>치수 mm</small></header>
<div class="alert"><b>왜 이 판을 만들었나:</b> Rev 3.1에도 칩(<b>U1</b>)은 들어 있었어 (BOM 7번, 브레드보드 10행 근처). 하지만 'U1'로만 표기되고 그림이 작아서 빠뜨리기 쉬웠어. 
<b>칩이 없으면 이 회로는 아무 신호도 안 나와.</b> 이 판은 칩을 1단계로 두고, 핀마다 어디에 연결되는지 표시했어.</div>
<div class="grid">
<div class="panel"><h2>① 칩 핀 연결 (가장 먼저 꽂을 것)</h2><div class="body">{chip}</div></div>
<div class="panel"><h2>② 회로 원리도</h2><div class="body">{sch}</div></div>
<div class="panel"><h2>③ 조립 순서</h2><div class="body"><ol>{''.join(f'<li>{s}</li>' for s in steps)}</ol>
<h3 style="margin:8px 0">전원 켠 뒤 확인 (멀티미터, 검은 리드 = GND)</h3><ul>{''.join(f'<li>{c}</li>' for c in check)}</ul></div></div>
<div class="panel"><h2>④ 부품 위치 (구멍 번호)</h2><div class="body">
<b>칩 U1 핀</b>{table(pinrows,['핀','구멍'])}<br><b>저항·커패시터</b>{table(partsrows,['부품','값','다리 1','다리 2'])}</div></div>
<div class="panel full"><h2>⑤ 점퍼·외부선 전체 목록 (Rev 3.1과 동일)</h2><div class="body" style="columns:3;column-gap:24px">{table(jrows,['No.','시작','끝','넷'])}</div></div>
<div class="panel full"><h2>⑥ 기구 수정 사항 (실제 구매품 기준)</h2><div class="body"><ul>
<li><b>용기:</b> Rev 3.1의 "PP cup, H 45, 바닥 Ø ≥70" → <b>PET 사각 용기 67 × 67 × 100 mm</b> (구매품). 충전선 <b>50 mm</b>.</li>
<li><b>구리테이프:</b> 20 × 40 mm, 마주 보는 두 <b>바깥</b> 벽의 폭 중앙, 바닥에서 <b>5~45 mm</b>. 위 모서리에 꼬리 5 × 10 mm를 남겨 바깥으로 접고 집게선 연결.</li>
<li>테이프 위는 투명 테이프로 덮기. 페이스트가 구리에 묻으면 접촉식이 되므로 바로 닦기. 측정 중 온도센서는 뺌.</li>
<li>기구도 사진(둥근 컵)은 실제와 다름 → 새 렌더 프롬프트는 별도 파일 참고.</li></ul></div></div>
</div></div></body></html>"""
    open(f'/home/claude/rev/out/config-{cfg}-rev3.2.html','w').write(html_)

if __name__=='__main__':
    for c in (6,7): sheet(c)
    print('done')
