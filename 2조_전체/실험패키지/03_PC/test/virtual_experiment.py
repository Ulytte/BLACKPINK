# 가상 실험: 실험 절차서 그대로의 명령 순서를 펌웨어 시뮬레이터(wc_host)에 넣고,
# 나온 시리얼 출력 → logger.py --from-file → analyze.py 까지 통과하는지 + 넣은 "정답"을 되찾는지 확인
# 정답(가정): R20(W/C) = 200 × (1 − 1.0 × (W/C − 0.5)) Ω, 배합 간 sd 1.5 %, α = 0.020,
#            수화 드리프트 +0.1 %/분, 측정마다 온도 19~23 °C 랜덤
import random, subprocess, pathlib, shutil, sys, re, json
HERE=pathlib.Path(__file__).parent; PC=HERE.parent; HOST=PC/'../02_펌웨어/host_test/wc_host'
rng=random.Random(2026)
S=[]; add=S.append
def R20(wc): return 200*(1-1.0*(wc-0.5))
# 0) 보정 저항 (집게를 저항에 물림)
for Rv,lab in ((100,'CAL-100.4'),(1000,'CAL-996')):
    rv=100.4 if Rv==100 else 996
    add('set alphaT 0'); add(f'set R {rv}'); add('set T 20'); add(f'cmd l {lab}'); add('cmd t')
    add('set clip sine'); add('cmd s'); add('set clip sq'); add('cmd q')
# 1) 소금물 (농도↑ → R↓)
for g,R in ((2,620),(4,330),(8,175)):
    add(f'set R {R}'); add('set alphaT 0.02'); add(f'cmd l SALT-{g}'); add('cmd t'); add('set clip sine'); add('cmd s'); add('set clip sq'); add('cmd q')
# 2) α: 같은 시료를 온도 바꿔 가며
add('set R 200')
for T in (12,15,18,21,24,27):
    add(f'set T {T}'); add(f'cmd l ALPHA-{T}'); add('cmd t'); add('set clip sine'); add('cmd s'); add('set clip sq'); add('cmd q')
# 3) 본 실험
truth={}
for wc in (0.40,0.50,0.60,0.53,0.56,0.59):
    for b in (1,2,3):
        lab0=f'W{int(round(wc*100)):03d}-B{b}'
        Rb=R20(wc)*(1+rng.gauss(0,0.015)); truth[lab0]=Rb
        add('cmd w')                                   # 물 넣은 순간
        add('wait 600000')                             # 10분 뒤 측정 시작
        for mr in (1,2):
            tmin=10+ (mr-1)*5
            T=rng.uniform(19,23)
            Rt=Rb*(1+0.001*tmin)                       # 수화 드리프트
            add(f'set R {Rt:.3f}'); add(f'set T {T:.2f}'); add(f'cmd l {lab0}-M{mr}')
            add('cmd t'); add('set clip sine'); add('cmd s'); add('set clip sq'); add('cmd q')
            add(f'set T {T+rng.uniform(-0.2,0.2):.2f}'); add('cmd t')
            if mr==1: add('wait 240000')
out=subprocess.run([str(HOST)],input='\n'.join(S)+'\n',capture_output=True,text=True).stdout
raw=HERE/'virtual_serial.txt'; raw.write_text(out,encoding='utf8')
print('serial lines',out.count('\n'),' MEAS',out.count('\nMEAS'),' WARN',out.count('\nWARN'))
dd=HERE/'data'; shutil.rmtree(dd,ignore_errors=True)
subprocess.run([sys.executable,str(PC/'logger.py'),'--from-file',str(raw)],check=True,cwd=HERE)
shutil.move(str(PC/'data'),str(dd)) if (PC/'data').exists() and not dd.exists() else None
r=subprocess.run([sys.executable,str(PC/'analyze.py'),'--data',str(dd),'--out',str(HERE/'result')],capture_output=True,text=True)
print(r.stdout[-200:] if r.returncode==0 else r.stderr)
(HERE/'truth.json').write_text(json.dumps(truth,indent=1))
