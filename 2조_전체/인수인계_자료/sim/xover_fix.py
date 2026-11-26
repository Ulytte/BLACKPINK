# 남은 시뮬 ②-b: 교차 왜곡·하단 sink 한계 대책 비교 (교차 왜곡 모델 lm358_xover.lib 사용)
#   base : 현재 설계 (MID 89 / AMP 64)
#   fixA : MID 108 / AMP 52  (출력 약 1.09~3.12 V, LM358이 낮은 전압에서 sink 할 일을 줄임)
#   fixAB: fixA + 풀다운 333 Ω(1k×3 병렬, 버퍼 A 출력→GND) + 500 Ω(1k×2 병렬)(가상 접지 버퍼 B 출력→GND) → 두 버퍼가 항상 source만 함(A급 동작)
import numpy as np, json, sim
exec(open('run_all.py').read().split("rows=[]")[0])
exec(open('xover.py').read().split("out={}")[0].split("exec(")[0])   # import only
def thd(t,v):
    m=t>t[-1]-PER*4; tt=t[m]; x=v[m]-v[m].mean()
    a=[abs(np.mean(x*np.exp(-2j*np.pi*k*tt/PER)))*2 for k in range(1,10)]
    return float(np.sqrt(sum(h*h for h in a[1:]))/a[0])
def net(R,mid,amp,pd):
    vic=5*mid/256
    return ("VCC vcc 0 5\n"+stair('src',mid,amp)+FILT+"CS sine vd 10u\nR1 vd node 330\n"+paste('node','vg',R)+
     "RV1 vcc vref 10k\nRV2a vref vr2 4.7k\nRV2b vr2 0 1k\nCV vref 0 10u\nXB vref vg vcc 0 vg LM358\n"+
     ("RPA sine 0 333\nRPB vg 0 500\n" if pd else "")+
     f".ic v(vref)=1.81 v(vg)=1.81 v(vd)=1.81 v(node)=1.81 v(sine)={vic} v(fx)={vic} v(fy)={vic} v(Pm)=1.81 v(xa.n1)={vic} v(xa.n2)={vic} v(xb.n1)=1.81 v(xb.n2)=1.81\n")
LSB=5/1023
out={}
for lib in ('lm358.lib','lm358_xover.lib'):
  sim.LIB=open(lib).read()
  for name,mid,amp,pd in (('base',89,64,0),('fixA',108,52,0),('fixAB',108,52,1)):
    rows=[]
    for R in (100,200,206,400):
        t,c=run(net(R,mid,amp,pd),30e-3,0.2e-6,['vd','node','vg','sine'],f'f_{name}_{R}')
        m=t>t[-1]-PER*2
        vd=periodic_samples(t,c['vd'],t[-1],2000,125e-6); vn=periodic_samples(t,c['node'],t[-1],2000,125e-6,ph0=0.37e-3,seed=2)
        rows.append(dict(R=R,Z_arduino=float(330*vn.std(ddof=1)/(vd.std(ddof=1)-vn.std(ddof=1))),
            Z_exactRMS=float(330*c['node'][m].std()/(c['vd'][m].std()-c['node'][m].std())),
            thd_vd_pct=100*thd(t,c['vd']),vg_pp_mV=1000*float(np.ptp(c['vg'][m])),
            out_min=float(c['sine'][m].min()),out_max=float(c['sine'][m].max()),
            Vn_rms_LSB=float(c['node'][m].std()/LSB)))
    out[f'{lib}:{name}']=rows
    print(lib,name,[{k:round(v,3) for k,v in r.items()} for r in rows])
json.dump(out,open('results_xover.json','w'),indent=1)
