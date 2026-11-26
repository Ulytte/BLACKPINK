import subprocess, numpy as np, os, sys
LIB=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lm358.lib')).read()
PWMF=62500.0
def pwm_src(name,node,mid,amp,start=0):
    # Arduino 8-bit fast PWM, duty follows a 64-step sine table; 25 ohm pin resistance
    return (f"B{name} {node}_i 0 V = 5*u( ({mid}+{amp}*sin(6.283185307*floor(time*{PWMF})/64)) /256 - (time*{PWMF}-floor(time*{PWMF})) )\n"
            f"R{name}p {node}_i {node} 25\n")
def run(net, tstop, step, nodes, tag):
    cir=f"* {tag}\n{LIB}\n{net}\n.options reltol=1e-4 method=gear\n.tran {step} {tstop} 0 {step} uic\n.control\nrun\nwrdata {tag}.dat {' '.join('v('+n+')' for n in nodes)}\nquit\n.endc\n.end\n"
    open(tag+'.cir','w').write(cir)
    r=subprocess.run(['ngspice','-b',tag+'.cir'],capture_output=True,text=True)
    if not os.path.exists(tag+'.dat'): print(r.stdout[-2000:],r.stderr[-2000:]); sys.exit(1)
    a=np.loadtxt(tag+'.dat'); t=a[:,0]; cols={n:a[:,2*i+1] for i,n in enumerate(nodes)}
    os.remove(tag+'.dat'); return t,cols
def adc_rms(t,v,t0,n=2000,dt=112e-6,offset=0.0):
    ts=t0+offset+np.arange(n)*dt
    x=np.interp(ts,t,v); q=np.round(x/5*1023)*5/1023
    return q.std(ddof=1)
def paste(n1,n2,R,tag='P'):
    # bulk resistance + double layer (2 electrodes in series ~40 uF) with leakage
    return f"Rb{tag} {n1} {tag}m {R}\nCdl{tag} {tag}m {n2} 40u\nRlk{tag} {tag}m {n2} 100k\n"
