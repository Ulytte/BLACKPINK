import pathlib,json,html,base64,re,textwrap
R=pathlib.Path(__file__).parent; OUT=R/'deliverables';OUT.mkdir(exist_ok=True)
C={'P':'#e52b42','G':'#252b33','T':'#b58c00','V':'#2468b6','I':'#ef7c18'}; navy='#183e63'
def esc(s):return html.escape(str(s))
class Sheet:
 def __init__(self):self.a=['<svg xmlns="http://www.w3.org/2000/svg" width="4200" height="2950" viewBox="0 0 4200 2950"><defs><linearGradient id="steel"><stop stop-color="#8896a2"/><stop offset=".45" stop-color="#f8fafb"/><stop offset="1" stop-color="#77848e"/></linearGradient></defs><rect width="4200" height="2950" fill="white"/>']
 def t(self,x,y,s,size=23,color=navy,bold=False,anchor='start'):
  self.a.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{esc(s)}</text>')
 def rect(self,x,y,w,h,fill='white',stroke='#b6c8da',rx=0):self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
 def line(self,x,y,X,Y,col=navy,width=2,dash=''):self.a.append(f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}" stroke="{col}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
 def dot(self,x,y,r=4,col=navy):self.a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>')
 def panel(self,x,y,w,h,title):self.rect(x,y,w,h,rx=12);self.rect(x,y,w,60,navy,navy);self.t(x+24,y+40,title,29,'white',True)
 def lines(self,x,y,ss,size=23,step=35):
  for i,s in enumerate(ss):self.t(x,y+i*step,s,size)
 def image(self,x,y,w,h,path):
  data=base64.b64encode(path.read_bytes()).decode();self.a.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}"/>')
 def table(self,x,y,widths,heads,rows,size=20,rh=34):
  for i,row in enumerate([heads]+rows):
   xx=x
   for w,v in zip(widths,row):
    self.rect(xx,y+i*rh,w,rh,'#eaf0f6' if i==0 else 'white');self.t(xx+9,y+i*rh+rh*.72,v,size,bold=i==0);xx+=w
 def dim(self,x,y,X,Y,label):
  self.line(x,y,X,Y);self.dot(x,y,4);self.dot(X,Y,4);self.t((x+X)/2,(y+Y)/2-14,label,24,anchor='middle')
 def save(self,name):
  svg=''.join(self.a)+'</svg>';(OUT/(name+'.svg')).write_text(svg,encoding='utf8');(OUT/(name+'.html')).write_text('<!doctype html><meta charset="utf-8"><title>'+name+'</title><style>body{margin:0;background:white}svg{width:100%;height:auto} @media print{@page{size:A3 landscape;margin:0}}</style>'+svg,encoding='utf8')

def mechanics(s,cfg):
 s.panel(40,150,1340,810,'1 · Assembled mechanical view')
 s.image(80,220,1260,615,R/f'assembly-{cfg}.png')
 if cfg=='2S':
  s.rect(90,230,760,52,'#fdecea','#c0392b',8);s.t(108,265,'Clip ONLY E1 and E4 (the two OUTER screws).',24,'#c0392b',True)
 s.lines(70,875,['Temperature probe: outside during electrical measurement.','Illustrative render; dimensions and assembly order govern.'],24)
 s.panel(1400,150,1360,810,'2 · Exploded view / assembly order')
 s.panel(2780,150,1380,810,'4 · Dimension view')
 if cfg=='4S':
  s.t(1430,258,'INSIDE → OUTSIDE · repeat on opposite wall ×2',28,bold=True)
  labels=['Bolt head','M4','M8','M12','Rubber*','PET wall','M12','M4','M4 nut']; xs=[1470+i*143 for i in range(9)]
  s.line(1430,465,2730,465,'#aab9c8',2,'8 8')
  for i,(x,l) in enumerate(zip(xs,labels)):
   if i==5:s.rect(x-8,335,16,260,'#e3eff6')
   elif i==0:s.rect(x-20,435,40,60,'url(#steel)');s.line(x+20,465,x+100,465,'#84919c',12)
   else:
    h={1:65,2:110,3:180,4:170,6:180,7:65,8:55}[i];s.a.append(f'<ellipse cx="{x}" cy="465" rx="20" ry="{h/2}" fill="url(#steel)" stroke="#82909e"/><ellipse cx="{x}" cy="465" rx="8" ry="20" fill="white"/>')
   s.dot(x,630,20);s.t(x,638,str(i+1),22,'white',anchor='middle');s.t(x,680,l,21,anchor='middle')
  s.lines(1430,750,['M4×40 bolt · hand-tighten outside nut; clip to projecting end.','* Thin rubber washer only if needed for leaks.','Leak test: fill with water to 50 mm and leave for one day.'],24,45)
 elif cfg=='2S':
  s.t(1430,258,'Four screws in one straight line · pitch 15',28,bold=True)
  for i in range(4):
   x=1580+i*320;s.rect(x-28,315,56,35,'url(#steel)');s.line(x,350,x,430,'#7d8890',12);s.rect(x-30,545,60,35,'url(#steel)');s.rect(x-12,620,24,100,'#232a30');s.line(x,720,x,765,'#aab3ba',14)
   s.t(x,290,['E1','Unused','Unused','E4'][i],25,anchor='middle')
  s.rect(1460,470,1230,32,'#e7f2f8');s.t(1460,450,'Ruler: 25 wide × 2 thick · Ø4 holes ×4',24)
  s.lines(1430,820,['M4×40 ×4 → ruler → M4 nuts ×4 → heat-shrink sleeves ×4.','Rest ruler on cut rim. Wire only first E1 and fourth E4.'],24,42)
 else:
  s.t(1430,258,'OUTSIDE ONLY · identical strip on opposite wall',28,bold=True)
  s.rect(1510,340,280,360,'#a4aaad');s.rect(1870,320,20,400,'#e4f1f8');s.rect(1995,380,14,280,'#ca8248');s.rect(2100,370,12,300,'#eff7fa');s.line(2180,520,2580,520,'#333',8);s.rect(2250,480,130,80,'#df3042',rx=18)
  s.lines(1460,770,['Paste | PET wall | copper foil tape | clear protective tape.','20 × 40 strip; 5 × 10 corner tab folded outward for clip.','Copper stays outside. Short clip leads ≤10 cm; tape down.'],25,45)
  for x,t in [(1610,'Paste'),(1880,'Wall'),(2000,'Copper'),(2130,'Tape'),(2420,'Clip')]:s.t(x,735,t,24,anchor='middle')
 # front dimension sketch
 x,y,w,h=(3000,300,650,450) if cfg=='2S' else (3150,300,302,450);scale=h/(45 if cfg=='2S' else 100);floor=y+h
 s.rect(x,y,w,h,'#f4f9fc',navy);fill=32 if cfg=='2S' else 50;s.rect(x+4,floor-fill*scale,w-8,fill*scale-4,'#c6c9cb','#c6c9cb');s.line(x,floor-fill*scale,x+w,floor-fill*scale,'#26945d',3,'12 7');s.t(x+w+25,floor-fill*scale+8,f'Fill {fill}',25)
 s.dim(x,y-45,x+w,y-45,'67 outer');s.dim(x-80,y,x-80,floor,'45 cut' if cfg=='2S' else '100')
 if cfg=='2S':
  for i in range(4):
   xx=x+100+i*150;s.line(xx,y,xx,floor-20*scale,'#30383f',13);s.line(xx,floor-20*scale,xx,floor-10*scale,'#7b8995',13)
  s.lines(2820,820,['Pitch 15 · exposed tips 10 · tip clearance ≈10.','Fill target 32 (range 28–36). Inner width ≈65.'],25,45)
 elif cfg=='4S':
  for xx in [x,x+w]:s.rect(xx-8,floor-38.5*scale,16,27*scale,'url(#steel)');s.line(xx-75,floor-25*scale,xx+75,floor-25*scale,'#697784',10)
  s.lines(2820,820,['Hole Ø4.5 · center 25 above inner bottom.','M12 washer OD: measure (≈24–27) · bolt end ≈20.','Face gap: measure on site; source ≈37 requires verification.'],24,38)
 else:
  s.rect(x+w/2-45,floor-45*scale,90,40*scale,'#c98750');s.dim(x+w/2-45,floor-45*scale-22,x+w/2+45,floor-45*scale-22,'20');s.lines(2820,820,['Copper 20 × 40 · bottom 5 · top 45.','Opposite walls, centered. Thin tape, no paste contact.'],25,45)

def board(s,d):
 bx,by=1415,1110
 s.t(bx,by-35,'830-hole board · top view',27,bold=True)
 s.rect(bx,by,770,1270,'#fafbfc',rx=9)
 def xy(h):
  m=re.fullmatch(r'([a-j])(\d+)',h)
  if m:
   a,n=m.groups();i=ord(a)-97;return bx+170+i*38+(60 if i>=5 else 0),by+60+(int(n)-1)*18
  a,n=re.fullmatch(r'([TB][+-])(\d+)',h).groups();return bx+({'T+':35,'T-':60,'B+':700,'B-':725}[a]),by+60+(int(n)-1)*22.78
 for a in 'abcdefghij':s.t(xy(a+'1')[0],by+30,a,18,anchor='middle')
 for n in range(1,64):
  s.t(bx+135,by+66+(n-1)*18,n,14,anchor='end')
  for a in 'abcdefghij':s.dot(*xy(a+str(n)),4,'#d2d9df')
 for a in ['T+','T-','B+','B-']:
  s.t(xy(a+'1')[0],by+30,a,15,anchor='middle')
  for n in range(1,51):
   xx,yy=xy(a+str(n));s.dot(xx,yy,3,C['P' if '+' in a else 'V'])
   if '+' in a and n in [1,5,10,15,20,25,26,30,35,40,45,50]:s.t(xx-8,yy+4,n,12,anchor='end')
 # leads map and jumper endpoint dots, use schedule for physical routes
 for net,v in d['nets'].items():
  for e in v['ends']:s.dot(*xy(d['holes'][e]),5,C[v['color']])
 # restrained jumper lines routed directly; all endpoint addresses in schedule
 for net,a,b,c in d['board_jumpers']:
  x,y=xy(a);X,Y=xy(b);s.line(x,y,X,Y,C[c],2)
 # two-terminal parts at their exact holes
 for idx,(ref,val,typ) in enumerate(d['parts']):
  x,y=xy(d['holes'][ref+'.1']);X,Y=xy(d['holes'][ref+'.2']);s.line(x,y,X,Y,'#777',4)
  cx,cy=(x+X)/2,(y+Y)/2
  s.rect(cx-10,cy-10,20,20,'#dbc591' if typ=='resistor' else '#e9b437','#6b7279',3)
  s.t(cx+14,cy-5,ref,14,bold=True)
  if typ=='electrolytic':s.t(x+7,y-7,'+',18,'#d22',True)
 # DIP-8 across central channel
 xe,ye=xy('e10');xf,yf=xy('f13');s.rect(xe+8,ye-11,xf-xe-16,yf-ye+22,'#20272d','#111',5)
 s.t((xe+xf)/2,ye+24,'LM358',15,'white',True,'middle');s.dot((xe+xf)/2,ye-3,6,'#bcc5ca')
 for p in range(1,9):
  x,y=xy(d['holes']['U1.'+str(p)]);s.line(x,y,x+(9 if p<5 else -9),y,'#87949e',5);s.t(x+(-10 if p<5 else 10),y+4,p,14,anchor='end' if p<5 else 'start')
 s.t(bx+10,by+1220,'U1 = LM358 — install first',24,'#d52835',True)
 s.t(bx+10,by+1255,'Notch → row 1 · exact part values in adjacent table',19)
 s.lines(bx,by+1310,['a–e / f–j: separate connected row groups.','T rails left; B rails right. Split at 25–26.','Parts bridge nets; they are NOT wires.','DS factory leads: T+2 / T−2 / j47.'],22,35)

def sine(s,cfg):
 x,y=75,2280;s.t(x,y,'SINE SOURCE · nominal 977 Hz',27,bold=True)
 # 10k two resistors series; feedback cap from FX to output
 for xx,label in [(260,'RA 10 kΩ'),(510,'RB 10 kΩ')]:s.rect(xx,y+65,95,35,'#efe2bf');s.t(xx+47,y+55,label,20,anchor='middle')
 s.t(x,y+90,'D9' if cfg=='6S' else 'D3',24);s.line(125,y+83,260,y+83);s.line(355,y+83,510,y+83);s.line(605,y+83,800,y+83)
 s.a.append(f'<path d="M800 {y+42} L800 {y+145} L900 {y+93} Z" fill="#e5edf4" stroke="{navy}" stroke-width="2"/>');s.t(815,y+83,'+',23);s.t(815,y+128,'−',23);s.line(900,y+93,1200,y+93)
 s.line(1070,y+93,1070,y+175);s.line(1070,y+175,760,y+175);s.line(760,y+175,760,y+126);s.line(760,y+126,800,y+126)
 s.line(420,y+83,420,y+5);s.line(420,y+5,640,y+5);s.line(640,y-10,640,y+20);s.line(655,y-10,655,y+20);s.line(655,y+5,1120,y+5);s.line(1120,y+5,1120,y+93);s.t(660,y-10,'C1 10 nF',21)
 s.line(680,y+83,680,y+118);s.line(660,y+118,700,y+118);s.line(660,y+133,700,y+133);s.line(680,y+133,680,y+200);s.line(655,y+200,705,y+200);s.t(530,y+222,'C2 4.7 nF → GND',21)
 s.t(940,y+130,'U1B → R1' if cfg=='6S' else 'U1A → CS → R1',22)

for cfg in ['2S','4S','6S']:
 d=json.loads((R/'source'/f'wiring-{"6S" if cfg=="6S" else "4S"}.json').read_text(encoding='utf8'));s=Sheet()
 title={'2S':'S1 ruler probe (2-electrode) + AC SINE','4S':'S2 washer electrodes + AC SINE','6S':'S3 copper tape + AC charge amplifier, SINE drive'}[cfg]
 s.t(45,75,'Configuration '+cfg+' · '+title,43,bold=True);s.t(4150,60,'SINE EDITION · REV 4.0',27,anchor='end');s.t(4150,100,'Dimensions in mm · not to scale',22,anchor='end');s.line(40,125,4160,125,navy,5)
 mechanics(s,cfg);s.panel(40,990,4120,1580,'3 · Wiring view — exact net map, component placement and physical jumper schedule')
 s.t(75,1100,'NET CONNECTIONS · endpoints on one line are common',26,bold=True)
 for i,(net,v) in enumerate(d['nets'].items()):
  y=1150+i*75;col=C[v['color']];s.t(75,y+9,net,23,col,True);ends=v['ends'];xx=[240+j*1100/max(1,len(ends)-1) for j in range(len(ends))];s.line(xx[0],y,xx[-1],y,col,4)
  for x,e in zip(xx,ends):s.dot(x,y,5,col);s.t(x,y-13,e,18,bold=True,anchor='middle');s.t(x,y+28,d['holes'][e],17,anchor='middle')
 board(s,d);sine(s,cfg)
 x=2225;s.t(x,1100,'PART LEGS · .1 / .2',25,bold=True)
 rows=[[ref,val,d['holes'][ref+'.1']+' / '+d['holes'][ref+'.2']] for ref,val,_ in d['parts']]
 s.table(x,1120,[90,235,220],['Ref','Value','Holes'],rows,20,37)
 s.t(x,1655,'U1 · LM358N DIP-8',25,bold=True);s.table(x,1680,[150,180,215],['Pin','Hole','Pin / hole'],[[str(i),d['holes']['U1.'+str(i)],str(9-i)+' / '+d['holes']['U1.'+str(9-i)]] for i in range(1,5)],21,37)
 s.lines(x,1910,['Electrolytic leg .1 is +.','Check polarity before power.','Do not use Arduino pins 0 / 1.'],22,35)
 s.t(2800,1100,'EXTERNAL LEADS',25,bold=True);s.table(2800,1120,[240,145],['Lead','Hole'],d['external_leads'],20,37)
 s.lines(2800,1800,['DS18B20 factory leads:','red → T+2','black → T−2','yellow → j47','Not included in jumper count.'],21,35)
 s.t(3220,1100,'INSTALL EVERY JUMPER',25,bold=True)
 js=[[str(i),a+' → '+b,n+' / '+{'P':'red','G':'black','T':'yellow','V':'blue','I':'orange'}[c]] for i,(n,a,b,c) in enumerate(d['board_jumpers'],1)]
 en={e:(n,v['color']) for n,v in d['nets'].items() for e in v['ends']}
 for i,(e,h) in enumerate(d['external_leads'],len(js)+1):
  n,c=en[e];js.append([str(i),e+' → '+h,n+' / '+{'P':'red','G':'black','T':'yellow','V':'blue','I':'orange'}[c]])
 s.table(3220,1120,[55,475,365],['No.','From → To','Net / color'],js,21,34)
 s.lines(3220,2410,[f'{len(d["board_jumpers"])} board + {len(d["external_leads"])} external = {len(js)} jumpers.','DS factory leads excluded.','Hole addresses are coordinates, not dimensions.'],22,38)
 changes=['D9 Timer1 PWM → U1B Sallen–Key filter.','BIAS → pin 3 only; pin 5 is filter input.','RF 10 MΩ; one CF 47 pF. SUM lead direct to c11.'] if cfg=='6S' else ['D3 Timer2 PWM → U1A Sallen–Key filter.','CS blocks DC; R1 330 Ω; A1 drive / A0 electrode.','U1B provides virtual ground. D8 / D9 unused.']
 s.rect(2225,2080,950,200,'#f1f6fb');s.t(2245,2120,'SINE REVISION',24,bold=True);s.lines(2245,2160,changes,22,38)
 s.t(2225,2360,'Design pre-check (expected, not measured):',23,bold=True);s.lines(2225,2400,['Pin 8 = 5 V; pin 4 = 0 V.','Pin 3 ≈1.6 V; pin 7 ≈1.75 V DC.' if cfg=='6S' else 'Pin 7 ≈1.8 V; test with 100 Ω in place of electrodes.'],22,38)
 for xx,cc,lab in [(80,'P','5V'),(260,'G','GND'),(470,'I','drive / sine'),(770,'V','sense / I2C'),(1110,'T','DATA')]:
  s.line(xx,2540,xx+35,2540,C[cc],5);s.t(xx+45,2547,lab,20)
 s.t(40,2630,'Bill of Materials · one configuration · repeated views count once',30,bold=True)
 common=[('Arduino Uno R3 compatible','1'),('830-hole breadboard','1'),('I2C LCD 16×2','1'),('Waterproof DS18B20','1'),('LM358N DIP-8','1')]+[(r+' '+v,'1') for r,v,_ in d['parts']]+[('Alligator clip leads','2'),('Jumpers (including external leads)',str(len(js)))]
 mech={'2S':[('Cut PET container · H45','1'),('Plastic ruler 25 × 2','1'),('SUS M4×40 / M4 nut / sleeve','4 each')],'4S':[('PET 67×67×100','1'),('SUS M4×40 / M4 nut','2 each'),('M4 / M8 / M12 washers','4 / 2 / 4'),('Thin rubber washer (optional)','2')],'6S':[('PET 67×67×100','1'),('Copper 20×40 + tab / clear tape','2')]}[cfg]
 items=common+mech
 for i in range(3):
  chunk=items[i*8:(i+1)*8];s.table(40+i*1380,2650,[1160,180],['Part / specification','Qty.'],chunk,20,27)
 s.t(40,2920,'SELF-CHECK: no net splits, shorts or reused signal holes. Circuit operation has not been bench-tested.',25,bold=True)
 s.save('configuration-'+cfg)
print('Built 3 SVG + HTML sheets')
