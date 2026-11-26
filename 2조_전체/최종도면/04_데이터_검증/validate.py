import json,re,collections,pathlib
root=pathlib.Path(__file__).parent
reports=[]
for cfg in ['4S','6S']:
 d=json.loads((root/'source'/f'wiring-{cfg}.json').read_text(encoding='utf8'))
 p={}
 def base(h):
  m=re.fullmatch(r'([a-j])(\d+)',h)
  if m:
   a,n=m.groups();assert 1<=int(n)<=63;return ('L' if a<'f' else 'R')+n
  m=re.fullmatch(r'([TB][+-])(\d+)',h);assert m,h
  a,n=m.groups();assert 1<=int(n)<=50;return a+str((int(n)-1)//25)
 def find(x):
  p.setdefault(x,x)
  if p[x]!=x:p[x]=find(p[x])
  return p[x]
 for _,a,b,_ in d['board_jumpers']:p[find(base(a))]=find(base(b))
 seen={};errors=[]
 for net,v in d['nets'].items():
  rs={find(base(d['holes'][e])) for e in v['ends']}
  if len(rs)!=1:errors.append('split '+net)
  for r in rs:
   if r in seen:errors.append('short '+net+' / '+seen[r])
   seen[r]=net
 occ=collections.defaultdict(list)
 for e,h in d['holes'].items():occ[h].append(e)
 for i,(_,a,b,_) in enumerate(d['board_jumpers'],1):
  occ[a].append('J'+str(i));occ[b].append('J'+str(i))
 for h,es in occ.items():
  if len(es)>1 and not h.startswith(('T','B')):errors.append('reused '+h+str(es))
 reports.append({'configuration':cfg,'nets':len(d['nets']),'board_jumpers':len(d['board_jumpers']),'external_leads':len(d['external_leads']),'errors':errors,'scope':'Connectivity only; no bench test.'})
(root/'validation.json').write_text(json.dumps(reports,indent=2),encoding='utf8')
print(json.dumps(reports,indent=2))
assert not any(r['errors'] for r in reports)
