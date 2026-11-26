import numpy as np
from sim import *
exec(open('run_all.py').read().split("res={}")[0])
def wave4S(R):
    net=("VCC vcc 0 5\n"+stair('src',89,64)+FILT+"CS sine vd 10u\nR1 vd node 330\n"+paste('node','vg',R)+
         "RV1 vcc vref 10k\nRV2a vref vr2 4.7k\nRV2b vr2 0 1k\nCV vref 0 10u\nXB vref vg vcc 0 vg LM358\n"
         ".ic v(vref)=1.81 v(vg)=1.81 v(vd)=1.81 v(node)=1.81 v(sine)=1.74 v(fx)=1.74 v(fy)=1.74 v(Pm)=1.81 v(xa.n1)=1.74 v(xa.n2)=1.74 v(xb.n1)=1.81 v(xb.n2)=1.81\n")
    return run(net,30e-3,0.5e-6,['vd','node'],f'n4_{R}')
def wave4(R):
    net=("Vd9 d9i 0 PULSE(0 5 0 50n 50n 0.5m 1m)\nVd8 d8i 0 PULSE(5 0 0 50n 50n 0.5m 1m)\nRp9 d9i d9 25\nRp8 d8i d8 25\nR1 d9 e1 330\n"+paste('e1','e4',R)+"Rx e4 d8 0.001\n")
    return run(net,40e-3,1e-6,['d9','e1','e4'],f'nq_{R}')
rng=np.random.default_rng(7); LSB=5/1023
def q(x,s): return np.round((x+rng.normal(0,s*LSB,len(x)))/LSB)*LSB
def sineZ(t,c,s):
    def samp(v,ph): ts=ph+np.arange(2000)*125e-6+rng.uniform(-3e-6,3e-6,2000); return q(np.interp(t[-1]-2*PER+np.mod(ts,PER),t,v),s)
    vd=samp(c['vd'],rng.uniform(0,PER)).std(ddof=1); vn=samp(c['node'],rng.uniform(0,PER)).std(ddof=1); return 330*vn/(vd-vn)
def sqZ(t,c,s,cycles=100):
    est=[]
    base=39e-3
    for k in range(cycles):
        for off in (0,0.5e-3):
            a2=q(np.interp([base+off+150e-6],t,c['d9']),s)[0]; a0=q(np.interp([base+off+262e-6],t,c['e1']),s)[0]; a1=q(np.interp([base+off+374e-6],t,c['e4']),s)[0]
            est.append(330*(a0-a1)/(a2-a0))
    return np.mean(est)
out={}
for R in (200,206):
    ts,cs=wave4S(R); tq,cq=wave4(R)
    for s in (0.5,1.0,2.0):
        zs=[sineZ(ts,cs,s) for _ in range(30)]; zq=[sqZ(tq,cq,s) for _ in range(30)]
        out[(R,s)]=(np.mean(zs),np.std(zs),np.mean(zq),np.std(zq))
        print(f'R={R} noise={s} LSB | sine mean {np.mean(zs):.2f} sd {np.std(zs):.3f} | square mean {np.mean(zq):.2f} sd {np.std(zq):.3f}')
