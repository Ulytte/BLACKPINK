# 실험 보드 배선 자동 검증 (union-find)
# 검사: 넷 끊김, 넷 간 합선, 구멍 중복, 부품 두 다리가 같은 줄(자기 합선), 점퍼 넷 이름 불일치,
#       아무 데도 안 이어진 부품 다리, 레일 25/26 끊김 반영, 구멍 번호 범위
import json, re, collections, pathlib, sys
d=json.loads((pathlib.Path(__file__).parent/'wiring-EXP.json').read_text(encoding='utf8'))
H=d['holes']; err=[]; warn=[]
def grp(h):
    m=re.fullmatch(r'([a-j])(\d+)',h)
    if m:
        n=int(m.group(2)); assert 1<=n<=63,h; return ('L' if m.group(1)<='e' else 'R')+str(n)
    m=re.fullmatch(r'([TB][+-])(\d+)',h); assert m,h
    n=int(m.group(2)); assert 1<=n<=50,h; return m.group(1)+('a' if n<=25 else 'b')
P={}
def f(x):
    P.setdefault(x,x)
    while P[x]!=x: P[x]=P[P[x]]; x=P[x]
    return x
def u(a,b): P[f(a)]=f(b)
for net,a,b,c in d['board_jumpers']: u(grp(a),grp(b))
# 택트 스위치: 홈을 건너는 다리끼리는 항상 연결(1-3, 2-4), 누를 때만 1-2 연결
u(grp(H['SW.1']),grp(H['SW.3'])); u(grp(H['SW.2']),grp(H['SW.4']))
owner={}
for net,v in d['nets'].items():
    gs={f(grp(H[e])) for e in v['ends']}
    if len(gs)!=1: err.append(f'끊김: {net} → {sorted(gs)}')
    for g in gs:
        if g in owner and owner[g]!=net: err.append(f'합선: {net} ↔ {owner[g]}')
        owner[g]=net
for net,a,b,c in d['board_jumpers']:
    g=f(grp(a))
    if owner.get(g)!=net: err.append(f'점퍼 넷 이름 불일치: {net} {a}-{b} (실제 {owner.get(g)})')
occ=collections.defaultdict(list)
for e,h in H.items(): occ[h].append(e)
for i,(net,a,b,c) in enumerate(d['board_jumpers'],1): occ[a].append(f'J{i}'); occ[b].append(f'J{i}')
for h,es in occ.items():
    if len(es)>1: err.append(f'구멍 중복: {h} {es}')
for p,val,kind in d['parts']:
    legs=[k for k in H if k.startswith(p+'.')]
    if len(legs)<2: err.append(f'다리 부족: {p}')
    if kind!='button' and f(grp(H[p+'.1']))==f(grp(H[p+'.2'])): err.append(f'자기 합선(두 다리 같은 넷): {p}')
    for k in legs:
        if f(grp(H[k])) not in owner: err.append(f'허공에 뜬 다리: {k} @ {H[k]}')
ext={e for e,_ in d['external_leads']}
for e,h in d['external_leads']:
    if H.get(e)!=h: err.append(f'외부선 구멍 불일치: {e}')
rep={'configuration':d['configuration'],'nets':len(d['nets']),'parts':len(d['parts']),
     'board_jumpers':len(d['board_jumpers']),'external_leads':len(d['external_leads']),'errors':err,
     'scope':'연결(토폴로지)만 검사. 전기적 동작은 spice_from_wiring.py로 확인.'}
pathlib.Path(__file__).with_name('validation-EXP.json').write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding='utf8')
print(json.dumps(rep,ensure_ascii=False,indent=1))
sys.exit(1 if err else 0)
