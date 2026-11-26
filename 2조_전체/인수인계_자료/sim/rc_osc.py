# 남은 시뮬 ③: 74HC14 RC 발진 주파수가 페이스트 저항에 얼마나 민감한가
#   구성 3·5 (접촉): 2번 출력 → R1 330 → E1 …페이스트… E4 → 1번 입력, CF 0.1 µF → GND
#   구성 7 (비접촉): 2번 출력 → RF 1 MΩ → 1번 입력 = 전극 A, 전극 B = GND (벽 C 16 pF ×2 직렬)
# 74HC14 모델(추정): VT+ 2.7 V, VT− 1.6 V @5 V, 출력 저항 50 Ω, 전파 지연 무시
import numpy as np, json, sim
from sim import run
SCH=("Bth th 0 V = 1.6 + 1.1*V(sq)/5\n"
     "Bst st 0 V = 2.5*(1 - tanh((V(in)-V(th))/0.005))\n"
     "Rd st sq 1k\nCd sq 0 1p\nBo o 0 V = V(sq)\n")
def f_of(t,v):
    m=t>t[-1]*0.4; tt=t[m]; x=v[m]-2.5
    up=tt[1:][(x[:-1]<0)&(x[1:]>=0)]
    return (len(up)-1)/(up[-1]-up[0])
def cfg3(R,Rout=50):
    net=(SCH+f"Ro o out {Rout}\nR1 out e1 330\n"+sim.paste('e1','in',R)+"CF in 0 0.1u\n.ic v(sq)=5 v(in)=0\n")
    t,c=run(net,1.5e-3,0.05e-6,['out'],f'rc3_{R}_{Rout}'); return f_of(t,c['out'])
def cfg7(R,Cw=16e-12,Cs=8.5e-12):
    net=(SCH+f"Ro o out 50\nRF out in 1meg\nCwa in pa {Cw}\nRp pa pb {R}\nCwb pb 0 {Cw}\nCab in 0 0.5p\nCst in 0 {Cs}\n.ic v(sq)=5 v(in)=0\n")
    t,c=run(net,1.5e-3,0.01e-6,['out'],f'rc7_{R}_{Cw}_{Cs}'); return f_of(t,c['out'])
res={'cfg3_5':[], 'cfg7':[]}
base3=cfg3(200)
for R,Ro in ((100,50),(200,50),(206,50),(300,50),(400,50),(200,60)):
    f=cfg3(R,Ro); res['cfg3_5'].append(dict(R=R,Rout=Ro,f_Hz=f,df_pct=100*(f/base3-1))); print('cfg3/5',res['cfg3_5'][-1])
base7=cfg7(100)
for R,Cw,Cs in ((100,16e-12,8.5e-12),(103,16e-12,8.5e-12),(100,16.16e-12,8.5e-12),(100,16e-12,9.5e-12),(1e9,16e-12,8.5e-12)):
    f=cfg7(R,Cw,Cs); res['cfg7'].append(dict(R=R,Cw_pF=Cw*1e12,Cstray_pF=Cs*1e12,f_Hz=f,df_pct=100*(f/base7-1))); print('cfg7',res['cfg7'][-1])
json.dump(res,open('results_rc.json','w'),indent=1)
