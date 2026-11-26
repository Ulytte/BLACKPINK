# 남은 시뮬 ①-b: 60 Hz 전원 유도 잡음(추정 진폭)을 전극 쪽 노드에 더했을 때
#   사인파 RMS(현재 펌웨어) / 사인파 동기검파(lock-in, 제안) / 사각파(구성 4) 비교
# 가정: 유도 잡음은 고임피던스 쪽(4S: node, 구성 4: e1)에만 실림, 위상은 측정마다 무작위, ADC 잡음 1 LSB
import numpy as np, json
from sim import *
exec(open('noise_cmp.py').read().split("rng=np.random.default_rng(7)")[0])
F0=1/PER
def hum(rng,ts,A): return A*np.sin(2*np.pi*60*ts+rng.uniform(0,2*np.pi))
def sine_meas(rng,t,c,A,s=1.0,N=2000):
    res={}
    T={}
    V={}
    for k,ph in (('vd',0.0),('node',N*125e-6)):           # vd 먼저 0.25 s, 그다음 node 0.25 s
        ts=ph+np.arange(N)*125e-6+rng.uniform(-3e-6,3e-6,N)
        x=np.interp(t[-1]-2*PER+np.mod(ts,PER),t,c[k])
        if k=='node': x=x+hum(rng,ts,A)
        V[k]=q(rng,x,s); T[k]=ts
    rms=330*V['node'].std(ddof=1)/(V['vd'].std(ddof=1)-V['node'].std(ddof=1))
    ph={k:np.mean((V[k]-V[k].mean())*np.exp(-2j*np.pi*F0*T[k]))*2 for k in V}   # 사인 테이블 위상 기준 단일 주파수 DFT
    lock=abs(330*ph['node']/(ph['vd']-ph['node']))
    return rms,lock
def sq_meas(rng,t,c,A,cycles=100,s=1.0):
    est=[]
    for off in (0,0.5e-3):
        b=39e-3+off
        a2=np.interp(b+150e-6,t,c['d9']); a0=np.interp(b+262e-6,t,c['e1']); a1=np.interp(b+374e-6,t,c['e4'])
        tk=np.arange(cycles)*1e-3+off+262e-6
        A0=q(rng,a0+hum(rng,tk,A),s)
        A2=q(rng,np.full(cycles,a2),s); A1=q(rng,np.full(cycles,a1),s)
        est.append(330*(A0-A1)/(A2-A0))
    return float(np.mean(est))
W={R:(wave4S(R),wave4(R)) for R in (200,206)}
rng=np.random.default_rng(11); REP=30
out=[]
for A in (0.0,0.005,0.02,0.05):
    r={'hum_V':A}
    S={R:np.array([sine_meas(rng,*W[R][0],A) for _ in range(REP)]) for R in (200,206)}
    Q={R:np.array([sq_meas(rng,*W[R][1],A) for _ in range(REP)]) for R in (200,206)}
    for name,z in (('sine_rms',{R:S[R][:,0] for R in S}),('sine_lockin',{R:S[R][:,1] for R in S}),('square',Q)):
        sp=np.sqrt((z[200].var(ddof=1)+z[206].var(ddof=1))/2); m0,m1=z[200].mean(),z[206].mean()
        r[name]=dict(mean200=m0,mean206=m1,sd=sp,d=(m1-m0)/sp)
    out.append(r)
    print(A, {k:(round(v['mean200'],2),round(v['sd'],3),round(v['d'],1)) for k,v in r.items() if k!='hum_V'})
json.dump(out,open('results_mains.json','w'),indent=1,default=float)
