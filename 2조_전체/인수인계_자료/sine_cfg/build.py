import json, copy, re
SRC='/home/claude/rev/src/build-drawings-rev3.1/'
OUT='/home/claude/sine_cfg/'
STD_EXT=[('5V','UNO.5V','T+1','P'),('GND','UNO.GND','T-1','G'),('5V','LCD.VCC','T+3','P'),('GND','LCD.GND','T-3','G')]
RAILS=[('5V','T+25','T+26','P'),('GND','T-25','T-26','G'),('5V','B+25','B+26','P'),('GND','B-25','B-26','G'),('5V','T+50','B+50','P'),('GND','T-50','B-50','G')]

# ---------- 4S : washer contact + sine (also 2S with S1 probe) ----------
c4={'configuration':'4S',
 'nets':{
  '5V':{'color':'P','ends':['UNO.5V','DS.red','LCD.VCC','RT.1','U1.8','RV1.1','CD.1']},
  'GND':{'color':'G','ends':['UNO.GND','DS.black','LCD.GND','U1.4','C2.2','RV2b.2','CV.2','CD.2']},
  'DATA':{'color':'T','ends':['UNO.D2','DS.yellow','RT.2']},
  'SDA':{'color':'V','ends':['UNO.A4','LCD.SDA']},'SCL':{'color':'V','ends':['UNO.A5','LCD.SCL']},
  'PWM':{'color':'I','ends':['UNO.D3','RA.1']},
  'FX':{'color':'I','ends':['RA.2','RB.1','C1.1']},
  'FY':{'color':'I','ends':['RB.2','C2.1','U1.3']},
  'SINE':{'color':'I','ends':['U1.1','U1.2','C1.2','CS.1']},
  'VD':{'color':'V','ends':['CS.2','R1.1','UNO.A1']},
  'NODE':{'color':'V','ends':['R1.2','E1','UNO.A0']},
  'VG':{'color':'V','ends':['U1.7','U1.6','E4']},
  'VREF':{'color':'V','ends':['RV1.2','RV2a.1','CV.1','U1.5']},
  'VR2':{'color':'V','ends':['RV2a.2','RV2b.1']}},
 'parts':[['RT','4.7 kΩ','resistor'],['RA','10 kΩ','resistor'],['RB','10 kΩ','resistor'],['C1','10 nF (103)','capacitor'],
          ['C2','4.7 nF (472)','capacitor'],['CS','10 µF 50 V (+/−)','electrolytic'],['R1','330 Ω 1%','resistor'],
          ['RV1','10 kΩ','resistor'],['RV2a','4.7 kΩ','resistor'],['RV2b','1 kΩ','resistor'],['CV','10 µF 50 V (+/−)','electrolytic'],['CD','0.1 µF (104)','capacitor']],
 'holes':{'U1.1':'e10','U1.2':'e11','U1.3':'e12','U1.4':'e13','U1.5':'f13','U1.6':'f12','U1.7':'f11','U1.8':'f10',
  'RT.1':'T+20','RT.2':'a26','RA.1':'b17','RA.2':'b15','RB.1':'d15','RB.2':'d12','C1.1':'c15','C1.2':'c10',
  'C2.1':'b12','C2.2':'T-9','CS.1':'c30','CS.2':'c32','R1.1':'a32','R1.2':'a34','RV1.1':'T+32','RV1.2':'a40',
  'RV2a.1':'b40','RV2a.2':'b42','RV2b.1':'a42','RV2b.2':'T-34','CV.1':'c40','CV.2':'T-32','CD.1':'j10','CD.2':'B-8',
  'UNO.5V':'T+1','UNO.GND':'T-1','DS.red':'T+2','DS.black':'T-2','LCD.VCC':'T+3','LCD.GND':'T-3',
  'UNO.D2':'j46','DS.yellow':'j47','UNO.A4':'j48','LCD.SDA':'j49','UNO.A5':'j50','LCD.SCL':'j51',
  'UNO.D3':'j52','E1':'j54','UNO.A0':'j55','E4':'j56','UNO.A1':'j58'},
 'board_jumpers':RAILS+[('5V','i10','B+8','P'),('GND','a13','T-10','G'),('DATA','i46','i47','T'),('DATA','h47','b26','T'),
   ('SDA','i48','i49','V'),('SCL','i50','i51','V'),('PWM','i52','a17','I'),('SINE','a10','a11','I'),('SINE','b10','b30','I'),
   ('VD','d32','i58','V'),('NODE','b34','i54','V'),('NODE','h54','i55','V'),('VG','j12','j11','V'),('VG','h11','i56','V'),('VREF','d40','i13','V')]}

# ---------- 6S : copper non-contact + sine ----------
d6=json.load(open(SRC+'wiring-6.json'))
c6=copy.deepcopy(d6); c6['configuration']='6S'
n=c6['nets']
n['DRIVE']={'color':'I','ends':['UNO.D9','RA.1']}
n['FX']={'color':'I','ends':['RA.2','RB.1','C1.1']}
n['FY']={'color':'I','ends':['RB.2','C2.1','U1.5']}
n['AMP B']={'color':'I','ends':['U1.6','U1.7','C1.2','R1.1']}
n['BIAS']['ends']=['U1.3','RB1.2','RB2.1','CB.1']
n['GND']['ends']=n['GND']['ends']+['C2.2']
c6['parts']=d6['parts']+[['RA','10 kΩ','resistor'],['RB','10 kΩ','resistor'],['C1','10 nF (103)','capacitor'],['C2','4.7 nF (472)','capacitor']]
c6['parts']=[[p,v.replace('47 pF ceramic','47 pF (470)').replace('0.1 µF ceramic','0.1 µF (104)'),k] for p,v,k in c6['parts']]
H=c6['holes']; H.update({'RA.1':'i17','RA.2':'i15','RB.1':'h15','RB.2':'h13','C1.1':'g15','C1.2':'g11','C2.1':'j13','C2.2':'B-10'})
bj=[tuple(j) for j in d6['jumpers']]
bj.remove(('DRIVE','i52','b27','I')); bj.remove(('BIAS','a12','j13','V')); bj.remove(('BIAS','i13','b34','V'))
bj+= [('DRIVE','i52','j17','I'),('AMP B','h11','b27','I'),('BIAS','a12','b34','V')]
c6['board_jumpers']=bj
for k in ('jumpers','full_jumper_schedule','BOM'): c6.pop(k,None)

def node(h):
    m=re.fullmatch(r'([a-j])(\d+)',h)
    if m: return ('L' if m.group(1)<='e' else 'R')+m.group(2)
    m=re.fullmatch(r'([TB])([+\-])(\d+)',h)
    if m: return f'{m.group(1)}{m.group(2)}{"a" if int(m.group(3))<=25 else "b"}'
    return h
def verify(c):
    H=c['holes']; par={}
    def f(x):
        par.setdefault(x,x)
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    def u(a,b): par[f(a)]=f(b)
    for _,a,b,_ in c['board_jumpers']: u(node(a),node(b))
    for k,h in H.items(): u(k,node(h))
    errs=[]
    # every hole used once
    from collections import Counter
    cnt=Counter(H.values()); cnt.update([j[1] for j in c['board_jumpers']]+[j[2] for j in c['board_jumpers']])
    dup=[h for h,v in cnt.items() if v>1 and not h.startswith(('T','B'))]
    rd=[h for h,v in cnt.items() if v>1 and h.startswith(('T','B'))]
    if dup: errs.append('hole used twice: '+str(dup))
    if rd: errs.append('rail hole used twice: '+str(rd))
    roots={}
    for net,v in c['nets'].items():
        rs={f(e) for e in v['ends']}
        if len(rs)>1: errs.append(f'net {net} split '+str({e:f(e) for e in v['ends']}))
        roots[net]=f(v['ends'][0])
    nets=list(roots)
    for i in range(len(nets)):
        for j in range(i+1,len(nets)):
            if roots[nets[i]]==roots[nets[j]]: errs.append(f'short {nets[i]}-{nets[j]}')
    allends={e for v in c['nets'].values() for e in v['ends']}
    for k in H:
        if k not in allends: errs.append('hole key not in any net: '+k)
    for p,_,_ in c['parts']:
        for leg in ('.1','.2'):
            if p+leg not in H: errs.append('missing leg '+p+leg)
        if node(H[p+'.1'])==node(H[p+'.2']): errs.append('part shorted '+p)
    return errs
for c in (c4,c6):
    print(c['configuration'], verify(c) or 'OK')
    ext=[]
    for k,h in c['holes'].items():
        if k.startswith(('UNO.','LCD.','E1','E4','Electrode')) : ext.append((k,h))
    c['external_leads']=ext
    json.dump(c,open(OUT+f"wiring-{c['configuration']}.json",'w'),ensure_ascii=False,indent=1)
