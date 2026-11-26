import numpy as np, json
from sim import *
PER=64/62500.0
def stair(node,mid,amp):
    return f"Bs {node} 0 V = 5*({mid}+{amp}*sin(6.283185307*floor(time*62500)/64))/256\n"
FILT="RA src fx 10k\nRB fx fy 10k\nC1 fx sine 10n\nC2 fy 0 4.7n\nXA fy sine vcc 0 sine LM358\n"
def periodic_samples(t,v,t_end,N,dt,ph0=0.0,jit=3e-6,seed=1):
    rng=np.random.default_rng(seed)
    ts=ph0+np.arange(N)*dt+rng.uniform(-jit,jit,N)
    tt=t_end-PER*2+np.mod(ts,PER)       # use last steady periods
    x=np.interp(tt,t,v); return np.round(x/5*1023)*5/1023
res={}
# ---------- 4S contact sine ----------
def sim4S(R,tag):
    net=("VCC vcc 0 5\n"+stair('src',89,64)+FILT+
         "CS sine vd 10u\nR1 vd node 330\n"+paste('node','vg',R)+
         "RV1 vcc vref 10k\nRV2a vref vr2 4.7k\nRV2b vr2 0 1k\nCV vref 0 10u\nXB vref vg vcc 0 vg LM358\n"
         ".ic v(vref)=1.81 v(vg)=1.81 v(vd)=1.81 v(node)=1.81 v(sine)=1.74 v(fx)=1.74 v(fy)=1.74 v(Pm)=1.81 v(xa.n1)=1.74 v(xa.n2)=1.74 v(xb.n1)=1.81 v(xb.n2)=1.81\n")
    t,c=run(net,30e-3,0.5e-6,['vd','node','sine','vg'],tag)
    vd=periodic_samples(t,c['vd'],t[-1],2000,125e-6); vn=periodic_samples(t,c['node'],t[-1],2000,125e-6,ph0=0.37e-3,seed=2)
    rd,rn=vd.std(ddof=1),vn.std(ddof=1)
    # exact (no ADC) for reference
    m=t>t[-1]-PER*2
    return dict(R=R,Z_arduino=330*rn/(rd-rn),Vd_rms=rd,Vn_rms=rn,sine_min=float(c['sine'][m].min()),sine_max=float(c['sine'][m].max()),vg=float(c['vg'][m].mean()),
                idc=float((c['node'][m]-c['vg'][m]).mean()/R))
rows=[]
for R in (100,150,200,206,300,400):
    r=sim4S(R,f's4_{R}'); rows.append(r); print('4S',{k:(round(v,4) if isinstance(v,float) else v) for k,v in r.items()})
res['4S']=rows
# ---------- PWM fidelity check (true PWM, short) ----------
net=("VCC vcc 0 5\n"+pwm_src('pw','src',89,64)+FILT+".ic v(sine)=1.74 v(fx)=1.74 v(fy)=1.74 v(xa.n1)=1.74 v(xa.n2)=1.74\n")
t,c=run(net,6e-3,0.02e-6,['sine'],'pwm')
m=t>3e-3; tt=t[m]; s=c['sine'][m]
fit=np.linalg.lstsq(np.c_[np.sin(2*np.pi*tt/PER),np.cos(2*np.pi*tt/PER),np.ones_like(tt)],s,rcond=None)[0]
resid=s-(np.c_[np.sin(2*np.pi*tt/PER),np.cos(2*np.pi*tt/PER),np.ones_like(tt)]@fit)
res['pwm']=dict(amp=float(np.hypot(*fit[:2])),dc=float(fit[2]),resid_rms=float(resid.std()),freq=1/PER,min=float(s.min()),max=float(s.max()))
print('PWM',res['pwm'])
# ---------- config 4 square (D9/D8 polarity reversal) ----------
def sim4(R,tag):
    net=("Vd9 d9i 0 PULSE(0 5 0 50n 50n 0.5m 1m)\nVd8 d8i 0 PULSE(5 0 0 50n 50n 0.5m 1m)\nRp9 d9i d9 25\nRp8 d8i d8 25\n"
         "R1 d9 e1 330\n"+paste('e1','e4',R)+"Rx e4 d8 0.001\n")
    t,c=run(net,40e-3,1e-6,['d9','e1','e4'],tag)
    # read A2(d9), A0(e1), A1(e4) sequentially starting 150 us after rising edge, 112 us apart; average 200 cycles of both polarities
    est=[]
    for k in range(20):
        t0=30e-3+k*1e-3*0  # periodic steady state
    def at(tt,n): return np.round(np.interp(tt,t,c[n])/5*1023)*5/1023
    base=39e-3
    for pol,off in ((1,0.0),(-1,0.5e-3)):
        a2=at(base+off+150e-6,'d9'); a0=at(base+off+262e-6,'e1'); a1=at(base+off+374e-6,'e4')
        est.append(330*(a0-a1)/(a2-a0))
    return dict(R=R,Z_arduino=float(np.mean(est)),pos=float(est[0]),neg=float(est[1]))
rows=[]
for R in (100,150,200,206,300,400):
    r=sim4(R,f'q4_{R}'); rows.append(r); print('4 square',r)
res['4']=rows
# ---------- 6S non-contact ----------
def sim6(R,Cw,tag):
    net=("VCC vcc 0 5\n"+stair('src',89,64)+FILT.replace('XA fy sine','XB fy sine')+
         "R1 sine ea 1k\n"
         f"Cwa ea pa {Cw}\nRp pa pb {R}\nCwb pb sum {Cw}\nCab ea sum 0.5p\nCsb sum 0 5p\n"
         "RF out sum 10meg\nCF out sum 47p\n"
         "RB1 vcc bias 10k\nRB2 bias 0 4.7k\nCB bias 0 10u\nXA bias sum vcc 0 out LM358\n"
         ".ic v(bias)=1.6 v(out)=1.6 v(sum)=1.6 v(sine)=1.74 v(fx)=1.74 v(fy)=1.74 v(xa.n1)=1.6 v(xa.n2)=1.6 v(xb.n1)=1.74 v(xb.n2)=1.74\n")
    t,c=run(net,30e-3,0.5e-6,['out'],tag)
    m=t>t[-1]-PER*2
    exact=c['out'][m].std()
    q=periodic_samples(t,c['out'],t[-1],2000,125e-6).std(ddof=1)
    return dict(R=R,Cw=Cw,A0_rms_exact=float(exact),A0_rms_arduino=float(q))
rows=[]
for R,Cw in ((100,'16p'),(103,'16p'),(100,'16.16p'),(1e9,'16p')):
    r=sim6(R,Cw,f's6_{R}_{Cw}'); rows.append(r); print('6S',r)
res['6S']=rows
json.dump(res,open('results.json','w'),indent=1)
