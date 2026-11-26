import json
D='/home/claude/sine_cfg/'
COLOR={'P':'red (5V)','G':'black (GND)','T':'yellow (DATA)','V':'blue (sense / I2C)','I':'orange (drive / sine)','F':'green (frequency)'}
EXTNAME={'UNO.5V':'Arduino 5V','UNO.GND':'Arduino GND','LCD.VCC':'LCD VCC','LCD.GND':'LCD GND','UNO.D2':'Arduino D2','UNO.A4':'Arduino A4',
 'LCD.SDA':'LCD SDA','UNO.A5':'Arduino A5','LCD.SCL':'LCD SCL','UNO.D3':'Arduino D3','UNO.D9':'Arduino D9','UNO.A0':'Arduino A0','UNO.A1':'Arduino A1',
 'E1':'Electrode E1 clip','E4':'Electrode E4 clip','Electrode A':'Electrode A clip','Electrode B':'Electrode B clip'}
def tables(c):
    L=[]
    L.append('NETS (every name on one line is electrically common; do not add or remove any endpoint):')
    for k,v in c['nets'].items(): L.append(f"  {k} [{COLOR[v['color']]}]: "+', '.join(v['ends']))
    L.append('\nPARTS (value; leg .1 hole; leg .2 hole):')
    H=c['holes']
    for p,v,kind in c['parts']:
        extra=' — electrolytic: leg .1 = + (long leg), leg .2 = −' if kind=='electrolytic' else ''
        L.append(f"  {p}: {v}; .1 = {H[p+'.1']}; .2 = {H[p+'.2']}{extra}")
    L.append('\nIC U1 = LM358N DIP-8, notch toward row 1, straddling the center gap:')
    L.append('  '+', '.join(f"pin {i} = {H['U1.'+str(i)]}" for i in range(1,9)))
    L.append('\nDS18B20 factory leads: red = '+H['DS.red']+', black = '+H['DS.black']+', yellow = '+H['DS.yellow'])
    L.append('\nJUMPER SCHEDULE (number them exactly in this order):')
    n=0
    for net,a,b,col in c['board_jumpers']:
        n+=1; L.append(f"  {n}. {a} → {b}  [{net}, {COLOR[col]}]")
    for k,h in c['external_leads']:
        n+=1; net=[nn for nn,v in c['nets'].items() if k in v['ends']][0]; col=c['nets'][net]['color']
        L.append(f"  {n}. {EXTNAME.get(k,k)} → {h}  [{net}, {COLOR[col]}]")
    L.append(f"\nTotal: {len(c['board_jumpers'])} board jumpers + {len(c['external_leads'])} external / clip leads = {n} (DS18B20 factory leads not counted).")
    return '\n'.join(L), n

COMMON_STYLE='''STYLE AND LAYOUT (copy the attached reference sheet exactly):
- One landscape sheet, same look as the attached "configuration-4.png / configuration-6.png": white background, dark-navy title bar, rounded panels with navy headers, Arial-like font, header right side "SINE EDITION · REV 4.0 / Dimensions in mm · not to scale".
- Panels in this order: 1 · Assembled mechanical view | 2 · Exploded view / assembly order | 4 · Dimension view (top row), then 3 · Wiring view (wide), then Bill of Materials, then SELF-CHECK footer.
- Wiring view contains, left to right: NET CONNECTIONS diagram (colored horizontal net lines with endpoint dots and hole labels, same style as reference), 830-hole board top view (rotated 90°, top rail pair T on the left, bottom pair B on the right, rows 1–63 top to bottom, columns a–e | f–j), PART LEGS table, EXTERNAL LEADS table, INSTALL EVERY JUMPER table.
- On the board view the IC must be drawn as a clearly visible black DIP body across the center gap at the listed holes, with the text "LM358" on it and pin numbers, plus a red label "U1 = LM358 — install first". Every resistor/capacitor must be drawn at its two listed holes and labeled with its name and value. Electrolytic capacitors show a "+" at leg .1.
- Wire colors: red 5V, black GND, yellow DATA, blue sense/I2C, orange drive/sine, green frequency. Color legend at the bottom.
- Add a small inset titled "SINE SOURCE" showing a simple schematic of the block described below (PWM → R–R with C to output and C to GND → op-amp buffer → output). Keep it schematic, not a breadboard picture.

STRICT RULES:
- Use ONLY the nets, parts, values, holes and jumpers listed below. Do not move, add, merge or renumber anything. Do not invent extra parts.
- Every hole is used at most once except rail holes; do not reuse a hole for two things.
- Hole addresses are breadboard coordinates (a–j + row number; T+/T−/B+/B− + rail index 1–50, rail split between 25 and 26).
- Do not write any measured result, price or performance claim. Footer must say: "Circuit operation has not been bench-tested."
- Text in English, except Korean is allowed in captions if needed.
'''

def prompt_4S(c, s1=False):
    t,n=tables(c)
    name='2S · S1 ruler probe (2-electrode) + AC SINE' if s1 else '4S · S2 washer electrodes + AC SINE'
    if s1:
        mech='''MECHANICAL (S1 ruler probe, same as Rev 3.1 configuration 2 except the container):
- Container: square clear PET container 67 × 67 × 100 mm CUT DOWN to 45 mm height (or the original PP cup H45, inner bottom Ø ≥70). Inner width ≈65.
- Plastic ruler ≈25 wide × ≈2 thick resting on the rim, four Ø4 holes in one line, pitch 15 mm, centered; outer screws ≈10 mm from the walls.
- Four SUS M4×40 socket-head screws hang through the ruler, M4 nut under the ruler, black heat-shrink sleeve on the upper shaft, bottom 10 mm bare. Tips ≈10 mm above the floor. Fill ≈28–36 mm (target 32).
- ONLY E1 (first) and E4 (fourth) are connected (alligator clips on the screw heads). E2 and E3 are present but unused, no clips.
- Temperature probe: inserted only before and after each reading, removed during measurement (show it outside the container with a note).
- Exploded view: 1 M4×40 screw ×4 → 2 ruler with four Ø4 holes → 3 M4 nut ×4 under ruler → 4 heat-shrink ×4 (leave 10 mm bare) → 5 rest ruler on cut container rim.
- Dimension view: cut height 45, inner width ≈65, pitch 15, bare tip 10, tip-to-floor ≈10, fill ≈32 (28–36).'''
    else:
        mech='''MECHANICAL (S2 washer electrodes, current design):
- Container: square clear PET container, outer 67 × 67 × 100 mm. Fill line 50 mm.
- Two opposite walls: one Ø4.5 mm through-hole each, centered horizontally, center 25 mm above the INNER bottom. Holes face each other.
- Stack per wall, INSIDE → OUTSIDE: SUS M4×40 bolt head → M4 flat washer → M8 flat washer → M12 flat washer (= electrode, flat on the inner wall) → [optional thin rubber washer, only if the water test leaks] → WALL → M12 flat washer (outside reinforcement) → M4 flat washer → M4 hex nut (hand-tight).
- The bolt end sticks out ≈20 mm outside; the alligator clip is clipped to this bolt end. No glue. No ring terminal.
- Items 1–4 (bolt head + M4 + M8 + M12 inside) are in the paste and form the electrode.
- Leak test: fill water to 50 mm and wait one day before using cement.
- Temperature probe: inserted only before and after each reading, removed during measurement.
- Dimension view: 67 wide, 100 tall, fill line 50, hole center 25 above inner bottom, Ø4.5, washer-face gap "≈37, measure on site".'''
    s=f'''Create one engineering build sheet titled "Configuration {name}".
Attach / reference: the previous sheet "configuration-4.png" (Rev 3.1) for style. This new sheet REPLACES the square-wave drive with a filtered sine-wave drive.

{COMMON_STYLE}
WHAT CHANGED (show as a short note box on the sheet):
- Drive: Arduino D3 fast PWM (≈62.5 kHz, duty following a 64-step sine table) → 2nd-order Sallen-Key low-pass filter (RA, RB = 10 kΩ; C1 = 10 nF to op-amp output; C2 = 4.7 nF to GND; fc ≈2.3 kHz) → LM358 amp A as unity buffer → ≈977 Hz sine, ≈0.5–3.0 V.
- CS 10 µF blocks DC; R1 330 Ω is the reference resistor; Arduino A1 reads the drive side, A0 reads the electrode side.
- E4 returns to a virtual ground ≈1.81 V made by RV1 10 kΩ / (RV2a 4.7 kΩ + RV2b 1 kΩ) with CV 10 µF, buffered by LM358 amp B. No DC flows through the paste.
- Arduino D8 and D9 are no longer used in this configuration.

{mech}

{t}

BILL OF MATERIALS (one configuration):
Arduino Uno R3 compatible ×1; 830-hole breadboard ×1; I2C LCD 16×2 ×1; waterproof DS18B20 ×1; LM358N DIP-8 ×1; RT 4.7 kΩ ×1; RA 10 kΩ ×1; RB 10 kΩ ×1; C1 10 nF ceramic (103) ×1; C2 4.7 nF ceramic (472) ×1; CS 10 µF 50 V electrolytic ×1; R1 330 Ω 1% ×1; RV1 10 kΩ ×1; RV2a 4.7 kΩ ×1; RV2b 1 kΩ ×1; CV 10 µF 50 V electrolytic ×1; CD 0.1 µF ceramic (104) ×1; alligator clip leads ×2; jumper wires ×{n}; {"cut PET container, plastic ruler, SUS M4×40 ×4, M4 nut ×4, heat-shrink Ø5 ×4" if s1 else "PET container 67×67×100 ×1, SUS M4×40 bolt ×2, M4 nut ×2, M4 washer ×4, M8 washer ×2, M12 washer ×4, rubber washer ×2 (optional)"}.

SELF-CHECK footer text: "Net list verified by connectivity check (no splits, no shorts, no reused holes). Sine source: D3 Timer2 PWM + 2nd-order LPF + LM358. Pre-check: LM358 pin 8 = 5 V, pin 4 = 0 V, pin 7 ≈ 1.8 V; then a 100 Ω test resistor in place of the electrodes should read ≈100 Ω. Circuit operation has not been bench-tested."
'''
    return s

def prompt_6S(c):
    t,n=tables(c)
    return f'''Create one engineering build sheet titled "Configuration 6S · S3 Non-contact (copper tape) + AC charge amplifier, SINE drive".
Attach / reference: the previous sheet "configuration-6.png" (Rev 3.1) for style. This new sheet keeps the charge amplifier and REPLACES the square-wave drive with a filtered sine-wave drive made from the previously unused LM358 amp B.

{COMMON_STYLE}
WHAT CHANGED vs Rev 3.1 configuration 6 (show as a short note box):
- Arduino D9 now outputs fast PWM (Timer1, ≈62.5 kHz) whose duty follows a sine table.
- LM358 amp B (pins 5, 6, 7) is no longer an unused buffer on BIAS: it is a 2nd-order Sallen-Key low-pass filter (RA, RB = 10 kΩ; C1 = 10 nF from the filter node to pin 7; C2 = 4.7 nF from pin 5 to GND). Pin 6 stays tied to pin 7. Output pin 7 drives R1 1 kΩ → Electrode A with a ≈977 Hz sine.
- BIAS now goes only to pin 3 (jumper a12 → b34); pin 5 is the filter input.
- Removed Rev 3.1 jumpers: i52 → b27, a12 → j13, i13 → b34. Added: i52 → j17, h11 → b27, a12 → b34. All other holes unchanged.
- A0 is read as AC RMS of the charge-amplifier output.

MECHANICAL (S3 copper tape, real container):
- Square clear PET container, outer 67 × 67 × 100 mm, fill line 50 mm (replaces "PP cup H45, inner bottom Ø ≥70").
- Two copper tape strips 20 mm wide × 40 mm tall on the OUTSIDE of two opposite walls, centered horizontally, from 5 mm to 45 mm above the bottom; a 5 × 10 mm tab at the top corner folded outward for the clip; covered with clear tape. The sample never touches copper.
- Temperature probe removed during measurement.
- Dimension view: 67 × 100 container, fill 50, copper 20 × 40, bottom gap 5, top of copper 45.

{t}

BILL OF MATERIALS (one configuration):
Arduino Uno R3 compatible ×1; 830-hole breadboard ×1; I2C LCD 16×2 ×1; waterproof DS18B20 ×1; PET container 67×67×100 ×1; copper tape 20 mm (20 × 40 + tab) ×2; LM358N DIP-8 ×1; RT 4.7 kΩ; R1 1 kΩ; RF 10 MΩ; CF 47 pF (470); RB1 10 kΩ; RB2 4.7 kΩ; CB 10 µF 50 V electrolytic; CD 0.1 µF (104); RA 10 kΩ; RB 10 kΩ; C1 10 nF (103); C2 4.7 nF (472) — one each; alligator clip leads ×2 (≤10 cm, taped down); jumper wires ×{n}.

SELF-CHECK footer text: "Net list verified by connectivity check (no splits, no shorts, no reused holes). High-impedance node SUM kept short: Electrode B lead directly into c11. Pre-check: pin 8 = 5 V, pin 4 = 0 V, pin 3 ≈ 1.6 V, pin 7 ≈ 1.75 V DC. Circuit operation has not been bench-tested."
'''
c4=json.load(open(D+'wiring-4S.json')); c6=json.load(open(D+'wiring-6S.json'))
open(D+'prompt_4S_washer_sine.txt','w').write(prompt_4S(c4))
c2=dict(c4); c2['configuration']='2S'
open(D+'prompt_2S_ruler_sine.txt','w').write(prompt_4S(c2,s1=True))
open(D+'prompt_6S_copper_sine.txt','w').write(prompt_6S(c6))
print(open(D+'prompt_4S_washer_sine.txt').read()[2600:5200])
