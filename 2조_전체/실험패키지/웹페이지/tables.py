import json, html
d=json.load(open('/home/user/BLACKPINK/2조_전체/실험패키지/01_회로/wiring-EXP.json',encoding='utf8')); H=d['holes']
NEW={'RPA1','RPA2','RPA3','RPB1','RPB2','RQ','SW'}
e=html.escape
role={1:'A 출력 = 사인파',2:'A − 입력 (1번과 연결)',3:'A + 입력 (필터 출력)',4:'GND',5:'B + 입력 (기준 1.8 V)',6:'B − 입력 (7번과 연결)',7:'B 출력 = 가상 접지',8:'5 V'}
o=['<h4>① 칩 LM358 (반달 홈이 1행 쪽)</h4><div class="tw"><table><thead><tr><th>핀</th><th>구멍</th><th>역할</th></tr></thead><tbody>']
for k in range(1,9): o.append(f'<tr><td class="n">{k}</td><td class="m">{H[f"U1.{k}"]}</td><td>{role[k]}</td></tr>')
o.append('</tbody></table></div><h4>② 저항·커패시터·버튼</h4><div class="tw"><table><thead><tr><th>부품</th><th>값</th><th>다리 1</th><th>다리 2</th><th></th></tr></thead><tbody>')
for p,v,kind in d['parts']:
    tag=' <span class="chip new">Rev 5</span>' if p in NEW else ''
    if kind=='button': o.append(f'<tr class="hl"><td class="m">{p}</td><td>택트 스위치</td><td class="m">e20·e22</td><td class="m">f20·f22</td><td>가운데 홈에 걸침{tag}</td></tr>'); continue
    note='<span class="chip warn">긴 다리 = + = 다리 1</span>' if kind=='electrolytic' else ''
    o.append(f'<tr{" class=hl" if p in NEW else ""}><td class="m">{p}</td><td>{e(v)}</td><td class="m">{H[p+".1"]}</td><td class="m">{H[p+".2"]}</td><td>{note}{tag}</td></tr>')
o.append('</tbody></table></div><h4>③ 보드 위 점퍼 (그림의 원 안 번호)</h4><div class="tw"><table><thead><tr><th>번호</th><th>넷</th><th>시작</th><th>끝</th></tr></thead><tbody>')
for i,(n,a,b,c) in enumerate(d['board_jumpers'],1):
    nw=i==len(d['board_jumpers'])
    o.append(f'<tr{" class=hl" if nw else ""}><td class="n">{i}</td><td>{e(n)}{" <span class=\"chip new\">Rev 5</span>" if nw else ""}</td><td class="m">{a}</td><td class="m">{b}</td></tr>')
def ext(k):
    for a_,b_ in {'UNO.':'Arduino ','LCD.':'LCD ','DS.':'온도센서 '}.items():
        if k.startswith(a_): return b_+{'red':'빨강','black':'검정','yellow':'노랑'}.get(k[len(a_):],k[len(a_):])
    return {'E1':'사인 집게 E1 (와셔 A)','E4':'사인 집게 E4 (와셔 B)','Q1':'사각 집게 Q1 (와셔 A)','Q4':'사각 집게 Q4 (와셔 B)'}.get(k,k)
o.append('</tbody></table></div><h4>④ 바깥 장치로 가는 선</h4><div class="tw"><table><thead><tr><th>장치 쪽</th><th>구멍</th></tr></thead><tbody>')
for k,h in d['external_leads']: o.append(f'<tr><td>{e(ext(k))}</td><td class="m">{h}</td></tr>')
o.append('</tbody></table></div>')
open('holes.html','w').write('\n'.join(o)); print(len(d['parts']),len(d['board_jumpers']),len(d['external_leads']))
