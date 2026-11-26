import json, re, html
SRC='/home/claude/rev/src/build-drawings-rev3.1/'; OUT='/home/claude/rev/out/'
FONT="'Noto Sans CJK KR',sans-serif"
COL={'P':'#d62728','G':'#222222','T':'#d4a017','V':'#1f6fb2','I':'#e67e22','F':'#2e8b57'}
P=24; X0=150
YROW={'T+':200,'T-':226}; 
for i,c in enumerate('abcde'): YROW[c]=276+i*P
for i,c in enumerate('fghij'): YROW[c]=420+i*P
YROW['B-']=570; YROW['B+']=596
def railrow(n): g=(n-1)//5; k=(n-1)%5; return 3+g*6+k
def pos(h):
    m=re.fullmatch(r'([a-j])(\d+)',h)
    if m: return X0+(int(m.group(2))-1)*P, YROW[m.group(1)]
    m=re.fullmatch(r'([TB])([+\-])(\d+)',h)
    if m: return X0+(railrow(int(m.group(3)))-1)*P, YROW[m.group(1)+m.group(2)]
    raise ValueError(h)
def t(x,y,s,fs=13,c='#17324d',a='middle',b=False,rot=None):
    tr=f' transform="rotate({rot} {x} {y})"' if rot is not None else ''
    return f'<text x="{x}" y="{y}" font-size="{fs}" fill="{c}" text-anchor="{a}" font-weight="{700 if b else 400}"{tr}>{html.escape(s)}</text>'
KNAME={'UNO':'Arduino','LCD':'LCD','DS':'온도센서'}
def extname(k):
    if k.startswith('UNO.'): return 'Arduino '+k[4:]
    if k.startswith('LCD.'): return 'LCD '+k[4:]
    if k.startswith('DS.'): return '온도센서 '+{'red':'빨강(5V)','black':'검정(GND)','yellow':'노랑(DATA)'}[k[3:]]
    if k.startswith('Electrode'): return '전극 '+k.split()[-1]+' 집게'
    if re.fullmatch(r'E\d',k): return '전극 '+k+' 집게'
    return k
def is_ext(k): return k.startswith(('UNO.','LCD.','DS.','Electrode')) or re.fullmatch(r'E\d',k)

def board(cfg):
    d=json.load(open(SRC+f'wiring-{cfg}.json')); H=d['holes']
    netcol={}
    for net,v in d['nets'].items():
        for e in v['ends']: netcol[e]=COL[v['color']]
    W=X0+63*P+60; Hh=910
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" width="{W}" height="{Hh}" font-family="{FONT}">']
    s.append(f'<rect x="{X0-40}" y="178" width="{63*P+56}" height="440" rx="14" fill="#f4f1e8" stroke="#c9c2ad" stroke-width="2"/>')
    s.append(f'<rect x="{X0-30}" y="390" width="{63*P+36}" height="6" fill="#ddd6c1"/>')
    # rails
    for r,c in (('T+','#d62728'),('T-','#1f6fb2'),('B-','#1f6fb2'),('B+','#d62728')):
        y=YROW[r]; s.append(f'<line x1="{X0-20}" y1="{y+ (-12 if r in ("T+","B-") else 12)}" x2="{X0+62*P+20}" y2="{y+(-12 if r in ("T+","B-") else 12)}" stroke="{c}" stroke-width="2" opacity=".5"/>')
        s.append(t(X0-30,y+5,('＋' if '+' in r else '－'),18,c,'end',True))
        s.append(t(X0+62*P+30,y+5,('＋' if '+' in r else '－'),18,c,'start',True))
        for n in range(1,51):
            x,_=pos(f'{r[0]}{r[1]}{n}'); s.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="#bdb6a0"/>')
    xs=X0+(railrow(25)-1)*P+ P*1; s.append(t(xs,190,'레일 25/26 사이 끊김',11,'#999'))
    for c in 'abcdefghij':
        s.append(t(X0-18,YROW[c]+4,c,13,'#777','end'))
        for r in range(1,64):
            x=X0+(r-1)*P; s.append(f'<rect x="{x-4}" y="{YROW[c]-4}" width="8" height="8" fill="#cfc8b2"/>')
    for r in (1,5,10,15,20,25,30,35,40,45,50,55,60,63):
        x=X0+(r-1)*P; s.append(t(x,256,str(r),11,'#777')); s.append(t(x,548,str(r),11,'#777'))
    # IC
    u=sorted([(int(k.split('.')[1]),v) for k,v in H.items() if k.startswith('U1.')])
    if u:
        n=len(u); rows=[int(v[1:]) for _,v in u]; r0,r1=min(rows),max(rows)
        x0=X0+(r0-1)*P-12; x1=X0+(r1-1)*P+12
        s.append(f'<rect x="{x0}" y="{YROW["e"]-10}" width="{x1-x0}" height="{YROW["f"]-YROW["e"]+20}" rx="4" fill="#1c1c1c"/>')
        s.append(f'<path d="M{x0} {(YROW["e"]+YROW["f"])/2-9} A9 9 0 0 1 {x0} {(YROW["e"]+YROW["f"])/2+9}" fill="#f4f1e8"/>')
        nm='LM358' if n==8 else '74HC14'
        s.append(t(x0-22,(YROW['e']+YROW['f'])/2+22,nm,15,'#111','end',True))
        for p,v in u:
            x,y=pos(v); yy=y+18 if v[0]=='e' else y-10
            s.append(t(x,yy,str(p),12,'#ffd54f','middle',True))
        s.append(t(x0-14,(YROW['e']+YROW['f'])/2+2,'칩 홈 ◀',12,'#c0392b','end',True))
    # parts
    for p,val,kind in d['parts']:
        a,b=H[p+'.1'],H[p+'.2']; (x1,y1),(x2,y2)=pos(a),pos(b)
        mx,my=(x1+x2)/2,(y1+y2)/2
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#888" stroke-width="2.5"/>')
        fill={'resistor':'#e3c493','capacitor':'#f2d35b','electrolytic':'#3d5f9e'}.get(kind,'#e3c493')
        import math
        ang=math.degrees(math.atan2(y2-y1,x2-x1)); L=min(26,max(10,math.hypot(x2-x1,y2-y1)-8))
        s.append(f'<rect x="{mx-L/2}" y="{my-6}" width="{L}" height="12" rx="5" fill="{fill}" stroke="#6b5a3a" transform="rotate({ang} {mx} {my})"/>')
        for hx,hy in ((x1,y1),(x2,y2)): s.append(f'<circle cx="{hx}" cy="{hy}" r="4.5" fill="#888"/>')
        lab=f'{p} {val}'.replace(' ceramic','').replace(' (+/−)','')
        if abs(x2-x1)<=abs(y2-y1):
            s.append(t(mx+14,my,lab,12,'#5a3d00','middle',True,-90))
        else:
            s.append(t(min(x1,x2)-10,my+4,lab,12,'#5a3d00','end',True))
        if kind=='electrolytic': s.append(t(x1+8,y1-6,'+',14,'#d62728','start',True))
    # jumpers on board
    num=0
    for i,(net,a,b,c) in enumerate(d['full_jumper_schedule']):
        if is_ext(a) or is_ext(b): continue
        (x1,y1),(x2,y2)=pos(a),pos(b); col=COL[c]
        dx,dy=x2-x1,y2-y1; L=(dx*dx+dy*dy)**.5 or 1
        bend=min(40,0.18*L); cx=(x1+x2)/2 - dy/L*bend; cy=(y1+y2)/2 + dx/L*bend
        s.append(f'<path d="M{x1} {y1} Q{cx} {cy} {x2} {y2}" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round" opacity=".9"/>')
        for hx,hy in ((x1,y1),(x2,y2)): s.append(f'<circle cx="{hx}" cy="{hy}" r="4" fill="{col}" stroke="#fff"/>')
        tt=0.3; qx=(1-tt)**2*x1+2*(1-tt)*tt*cx+tt*tt*x2; qy=(1-tt)**2*y1+2*(1-tt)*tt*cy+tt*tt*y2
        s.append(f'<circle cx="{qx}" cy="{qy}" r="9" fill="#fff" stroke="{col}" stroke-width="1.5"/>'+t(qx,qy+4,str(i+1),10,col,'middle',True))
    # external leads (spread labels so they never overlap)
    leads=[]
    for k,h in H.items():
        if not is_ext(k): continue
        x,y=pos(h); leads.append((x,y,k,h,(h[0]=='T') or (h[0] in 'abcde')))
    for top in (True,False):
        L=sorted([l for l in leads if l[4]==top], key=lambda l:(l[0],l[1]))
        last=-1e9; 
        for x,y,k,h,_ in L:
            lx=max(x,last+24); last=lx; col=netcol.get(k,'#555')
            if top:
                s.append(f'<polyline points="{x},{y} {x},166 {lx},146 {lx},138" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="7 4"/>')
                s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{col}" stroke="#fff"/>')
                s.append(t(lx+5,132,extname(k),14,col,'start',True,-90))
            else:
                s.append(f'<polyline points="{x},{y} {x},616 {lx},636 {lx},644" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="7 4"/>')
                s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{col}" stroke="#fff"/>')
                s.append(t(lx+5,650,extname(k),14,col,'end',True,-90))
    # legend
    lx=X0; ly=860
    items=[('#d62728','5 V'),('#222','GND'),('#d4a017','온도 DATA'),('#1f6fb2','측정·I2C'),('#e67e22','구동·전극'),('#2e8b57','주파수')]
    for i,(c,nm) in enumerate(items):
        s.append(f'<line x1="{lx+i*150}" y1="{ly-5}" x2="{lx+i*150+30}" y2="{ly-5}" stroke="{c}" stroke-width="5"/>'+t(lx+i*150+38,ly,nm,14,'#333','start'))
    s.append(t(lx,ly+26,'실선 = 브레드보드 점퍼 (원 안 숫자 = 점퍼 표 번호) · 점선 = 바깥 장치로 가는 선 · 베이지 막대 = 저항, 노랑 = 세라믹 C, 파랑 = 전해 C',13,'#555','start'))
    s.append('</svg>')
    return '\n'.join(s)

TITLE={1:'구성 1 · S1 4전극 + AC (칩 없음)',2:'구성 2 · S1 2전극 + AC (칩 없음)',3:'구성 3 · S1 2전극 + RC (74HC14)',
       4:'구성 4 · S2 와셔 + AC (칩 없음)',5:'구성 5 · S2 와셔 + RC (74HC14)',6:'구성 6 · S3 구리테이프 + AC (LM358)',7:'구성 7 · S3 구리테이프 + RC (74HC14)'}
def page(cfg):
    sv=board(cfg)
    doc=f"""<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#fff;font-family:{FONT}">
<div style="padding:20px 30px"><div style="font-size:30px;font-weight:700;color:#153e67">{TITLE[cfg]} — 브레드보드 배선 그림</div>
<div style="font-size:17px;color:#444;margin:6px 0 4px">브레드보드를 이 그림과 같은 방향(1행이 왼쪽, a줄이 위)으로 놓고, <b>칩 → 레일 점퍼 → 저항·커패시터 → 점퍼(번호 순) → 바깥 장치</b> 순서로 꽂아. a~e는 한 세로줄(같은 번호)끼리, f~j도 같은 번호끼리 연결돼 있고, 가운데 홈을 넘어서는 연결 안 됨.</div>
{sv}</div></body></html>"""
    open(OUT+f'breadboard-{cfg}.html','w').write(doc)
if __name__=='__main__':
    for c in range(1,8): page(c)
    print('ok')
