# 배선표(wiring-EXP.json)를 그대로 SPICE 넷리스트로 바꿔서 시뮬레이션 (배선 = 회로인지 확인)
# - 넷 이름은 union-find로 구한 실제 연결에서 나온다 (사람이 따로 그린 회로도 아님)
# - LM358은 교차 왜곡·sink 한계 모델(추정), 페이스트 = R + 이중층 40 µF ∥ 100 kΩ (추정)
# - 펌웨어와 같은 계산식(동기검파 / 사각 대칭식)으로 Z를 구한다
import json, re, pathlib, subprocess, numpy as np, os, sys
HERE=pathlib.Path(__file__).parent
d=json.loads((HERE/'wiring-EXP.json').read_text(encoding='utf8')); H=d['holes']
ino=(HERE/'../02_펌웨어/wc_meter/wc_meter.ino').read_text(encoding='utf8')
MID=int(re.search(r'MID\s*=\s*(\d+)',ino).group(1)); AMP=int(re.search(r'AMP\s*=\s*(\d+)',ino).group(1))
LIB=(HERE/'../../인수인계_자료/sim/lm358_xover.lib').read_text()
def grp(h):
    m=re.fullmatch(r'([a-j])(\d+)',h)
    if m: return ('L' if m.group(1)<='e' else 'R')+m.group(2)
    m=re.fullmatch(r'([TB][+-])(\d+)',h); return m.group(1)+('a' if int(m.group(2))<=25 else 'b')
P={}
def f(x):
    P.setdefault(x,x)
    while P[x]!=x: x=P[x]
    return x
for _,a,b,_ in d['board_jumpers']: P[f(grp(a))]=f(grp(b))
P[f(grp(H['SW.1']))]=f(grp(H['SW.3'])); P[f(grp(H['SW.2']))]=f(grp(H['SW.4']))
g2net={}
for net,v in d['nets'].items():
    for e in v['ends']: g2net[f(grp(H[e]))]=net
def N(end):
    n=g2net[f(grp(H[end]))]; return '0' if n=='GND' else re.sub(r'\W','_',n).lower()
def val(s):
    m=re.match(r'([\d.]+)\s*(k|M|µ|n|p)?',s); x=float(m.group(1)); return x*{'k':1e3,'M':1e6,'µ':1e-6,'n':1e-9,'p':1e-12,None:1}[m.group(2)]
def netlist(scenario,R):
    L=['* from wiring-EXP.json',LIB,f'VCC {N("UNO.5V")} 0 5']
    for p,v,kind in d['parts']:
        if kind=='button': continue
        a,b=N(p+'.1'),N(p+'.2')
        if kind=='resistor': L.append(f'R{p} {a} {b} {val(v)}')
        else: L.append(f'C{p} {a} {b} {val(v)}')
    U=lambda k:N(f'U1.{k}')
    L.append(f'XUA {U(3)} {U(2)} {U(8)} {U(4)} {U(1)} LM358'); L.append(f'XUB {U(5)} {U(6)} {U(8)} {U(4)} {U(7)} LM358')
    if scenario=='sine':
        L.append(f'BPWM pwm_i 0 V = 5*({MID}+{AMP}*sin(6.283185307*floor(time*62500)/64))/256'); L.append(f'RPIN pwm_i {N("UNO.D3")} 25')
        a,b=N('E1'),N('E4')
    else:
        L.append(f'BPWM pwm_i 0 V = 5*{MID}/256'); L.append(f'RPIN pwm_i {N("UNO.D3")} 25')
        L.append(f'V9 d9i 0 PULSE(5 0 0 50n 50n 0.5m 1m)'); L.append(f'R9 d9i {N("UNO.D9")} 26')
        L.append(f'V8 d8i 0 PULSE(0 5 0 50n 50n 0.5m 1m)'); L.append(f'R8 d8i {N("UNO.D8")} 26')
        a,b=N('Q1'),N('Q4')
    for k in ('UNO.A0','UNO.A1','UNO.A2','UNO.A3','UNO.D9','UNO.D8','Q4','E1'):   # 입력 핀 누설(약 100 MΩ) → 떠 있는 넷 방지
        L.append(f'RLK_{k.replace(".","_")} {N(k)} 0 100meg')
    if R: L+= [f'RBULK {a} pm {R}', f'CDL pm {b} 40u', f'RLK pm {b} 100k']
    return '\n'.join(L)
def op(scenario,R):
    # DC 동작점 (PWM = 중심 듀티 DC, 사각 핀 = 입력(띄움)) → 사전 점검표 + 과도해석 초기값
    net=netlist(scenario,R).replace(f'BPWM pwm_i 0 V = 5*({MID}+{AMP}*sin(6.283185307*floor(time*62500)/64))/256',f'BPWM pwm_i 0 V = {5*MID/256}')
    net='\n'.join(l for l in net.split('\n') if not l.startswith(('V9','V8','R9 ','R8 ')))
    if R: net=net.replace('CDL pm','RDLDC pm').replace(' 40u',' 1e12')   # DC에서 이중층 = 개방
    cir=net+"\n.op\n.control\nrun\nprint all\nquit\n.endc\n.end\n"
    pathlib.Path('/tmp/wo.cir').write_text(cir)
    r=subprocess.run(['ngspice','-b','/tmp/wo.cir'],capture_output=True,text=True).stdout
    return {re.sub(r'^v\((.*)\)$',r'\1',m.group(1)):float(m.group(2)) for m in re.finditer(r'^(\S+) = ([-\d.e+]+)',r,re.M) if '#' not in m.group(1)}
def run(scenario,R,tstop,probes):
    net=netlist(scenario,R)
    ic=op(scenario,R)
    net+='\n.ic '+' '.join(f'v({k})={v}' for k,v in ic.items() if k not in ('5v','pwm_i','d9i','d8i'))
    cir=net+f"\n.options reltol=1e-4 method=gear\n.tran 0.5u {tstop} 0 0.5u uic\n.control\nrun\nwrdata /tmp/wx.dat {' '.join('v('+p+')' for p in probes)} i(vcc)\nquit\n.endc\n.end\n"
    pathlib.Path('/tmp/wx.cir').write_text(cir)
    r=subprocess.run(['ngspice','-b','/tmp/wx.cir'],capture_output=True,text=True)
    if not os.path.exists('/tmp/wx.dat'): print(r.stdout[-1500:]); sys.exit(1)
    a=np.loadtxt('/tmp/wx.dat'); os.remove('/tmp/wx.dat'); t=a[:,0]
    return t,{p:a[:,2*i+1] for i,p in enumerate(probes)}, a[:,2*len(probes)+1]
PER=64/62500
def lockin(t,v,t0):
    m=t>t0; tt=t[m]; x=v[m]; M=np.c_[np.cos(2*np.pi*tt/PER),np.sin(2*np.pi*tt/PER),np.ones_like(tt)]
    c=np.linalg.lstsq(M,x,rcond=None)[0]; return c[0]+1j*c[1], c[2]
out={'MID':MID,'AMP':AMP,'nodes':{}}
pins={'U1.1':'LM358 1번(사인 출력)','U1.3':'LM358 3번','U1.5':'LM358 5번(기준)','U1.7':'LM358 7번(가상 접지)','U1.8':'LM358 8번(전원)','UNO.A1':'A1(구동)','UNO.A0':'A0(전극)'}
probes=sorted({N(k) for k in pins}|{N('CS.1'),N('CS.2')}-{'0'})
for R in (200,206,None):
    t,c,iv=run('sine',R,0.06,probes)
    t0=t[-1]-4*PER; m=t>t0
    Vd,_=lockin(t,c[N('UNO.A1')],t0); Vn,_=lockin(t,c[N('UNO.A0')],t0)
    Z=330*Vn/(Vd-Vn)
    row={'Z_lockin':abs(Z),'phase_deg':float(np.degrees(np.angle(Z))),
         'sine_min':float(c[N('U1.1')][m].min()),'sine_max':float(c[N('U1.1')][m].max()),
         'CS_dc_V(+쪽-−쪽)':float((c[N('CS.1')][m]-c[N('CS.2')][m]).mean()),
         'vg_pp_mV':float(np.ptp(c[N('U1.7')][m])*1000)}
    if R is None:  # 집게 안 꽂은 상태 = 사전 점검 기준 DC (.op)
        o=op('sine',None); row['DC_op']={pins[k]:round(o.get(N(k),0.0),3) for k in pins}
        o=op('sine',200); row['DC_op_R200']={pins[k]:round(o.get(N(k),0.0),3) for k in pins}
    out['sine_R'+str(R)]=row; print('sine',R,{k:(round(v,3) if isinstance(v,float) else v) for k,v in row.items()})
qp=[N('UNO.A2'),N('UNO.A3'),N('Q4')]
for R in (200,206):
    t,c,iv=run('sq',R,0.03,qp)
    ix=lambda tt:np.interp(tt,t,c[qp[0]]),
    S9=[];S1=[]
    for k in range(20,29):
        b=k*1e-3
        p9=np.interp(b+150e-6,t,c[qp[0]]); p1=np.interp(b+262e-6,t,c[qp[1]])
        n9=np.interp(b+0.5e-3+150e-6,t,c[qp[0]]); n1=np.interp(b+0.5e-3+262e-6,t,c[qp[1]])
        S9.append(p9-n9); S1.append(p1-n1)
    s9,s1=np.mean(S9),np.mean(S1); Z=330*(s1+s9)/(s9-s1)
    out['sq_R'+str(R)]={'Z_sym':float(Z),'S9':float(s9),'S1':float(s1)}; print('sq',R,round(Z,2))
(HERE/'spice_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
