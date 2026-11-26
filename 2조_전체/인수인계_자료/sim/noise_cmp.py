# 남은 시뮬 ①: ADC 잡음을 넣은 30회 반복 → 사인파(4S) vs 사각파(구성 4) σ 비교
# 가정: ADC 잡음은 읽기마다 독립 가우시안(0.5/1/2 LSB), 3 µs 샘플 지터, 1 LSB = 5/1023 V
import numpy as np, json
from sim import *
exec(open('run_all.py').read().split("res={}")[0])   # stair, FILT, PER, paste 재사용
LSB=5/1023
def wave4S(R):
    net=("VCC vcc 0 5\n"+stair('src',89,64)+FILT+"CS sine vd 10u\nR1 vd node 330\n"+paste('node','vg',R)+
         "RV1 vcc vref 10k\nRV2a vref vr2 4.7k\nRV2b vr2 0 1k\nCV vref 0 10u\nXB vref vg vcc 0 vg LM358\n"
         ".ic v(vref)=1.81 v(vg)=1.81 v(vd)=1.81 v(node)=1.81 v(sine)=1.74 v(fx)=1.74 v(fy)=1.74 v(Pm)=1.81 v(xa.n1)=1.74 v(xa.n2)=1.74 v(xb.n1)=1.81 v(xb.n2)=1.81\n")
    return run(net,30e-3,0.5e-6,['vd','node'],f'n4_{R}')
def wave4(R):
    net=("Vd9 d9i 0 PULSE(0 5 0 50n 50n 0.5m 1m)\nVd8 d8i 0 PULSE(5 0 0 50n 50n 0.5m 1m)\nRp9 d9i d9 25\nRp8 d8i d8 25\nR1 d9 e1 330\n"+paste('e1','e4',R)+"Rx e4 d8 0.001\n")
    return run(net,40e-3,1e-6,['d9','e1','e4'],f'nq_{R}')
def q(rng,x,s): return np.round((x+rng.normal(0,s*LSB,np.shape(x)))/LSB)*LSB
def sineZ(rng,t,c,s,N=2000):
    def samp(v):
        ts=rng.uniform(0,PER)+np.arange(N)*125e-6+rng.uniform(-3e-6,3e-6,N)
        return q(rng,np.interp(t[-1]-2*PER+np.mod(ts,PER),t,v),s)
    vd=samp(c['vd']).std(ddof=1); vn=samp(c['node']).std(ddof=1); return 330*vn/(vd-vn)
def sqZ(rng,t,c,s,cycles):
    # 마지막 정상상태 1주기(39~40 ms)의 파형을 반복 사용. 엣지 후 150/262/374 µs에 A2→A0→A1 순차 읽기
    est=[]
    for off in (0,0.5e-3):
        b=39e-3+off
        a2=np.interp(b+150e-6,t,c['d9']); a0=np.interp(b+262e-6,t,c['e1']); a1=np.interp(b+374e-6,t,c['e4'])
        A2=q(rng,np.full(cycles,a2),s); A0=q(rng,np.full(cycles,a0),s); A1=q(rng,np.full(cycles,a1),s)
        est.append(330*(A0-A1)/(A2-A0))
    return float(np.mean(est))
rng=np.random.default_rng(7); REP=30
W={R:(wave4S(R),wave4(R)) for R in (200,206)}
out=[]
for s in (0.5,1.0,2.0):
    row=dict(noise_LSB=s)
    for name,fn in (('sine_4000reads',lambda w:sineZ(rng,*w[0],s)),
                    ('square_600reads',lambda w:sqZ(rng,*w[1],s,100)),
                    ('square_4000reads',lambda w:sqZ(rng,*w[1],s,667))):
        z={R:np.array([fn(W[R]) for _ in range(REP)]) for R in (200,206)}
        m0,m1=z[200].mean(),z[206].mean(); sp=np.sqrt((z[200].var(ddof=1)+z[206].var(ddof=1))/2)
        row[name]=dict(mean200=m0,mean206=m1,sd=sp,cv_pct=100*sp/m0,d=(m1-m0)/sp,pass_3sigma=bool(m1-m0>=3*sp))
    out.append(row)
    print(json.dumps(row,ensure_ascii=False,default=float))
json.dump(out,open('results_noise.json','w'),indent=1,default=float)
