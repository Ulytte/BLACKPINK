#!/usr/bin/env python3
"""
2조 측정 데이터 분석 — logger.py가 만든 data/*.csv를 읽어 보고서(report.md)와 그림을 만든다.

사용법
  python analyze.py                       # data/ 폴더를 분석 → result/ 에 저장
  python analyze.py --data data --out result --alpha 0.021   # α를 직접 지정 (생략하면 ALPHA 측정에서 추정)

시료 이름(label) 규칙 — 펌웨어에서 'l 이름' 으로 입력
  W050-B1-M1  : W/C 0.50, 배합 1번, 측정 회차 1 (재혼합 후 2회차는 M2)
  CAL-100.4   : 보정 저항 (멀티미터로 잰 값 100.4 Ω을 이름에)
  SALT-4      : 소금물 4 g/L
  ALPHA-12    : 온도계수 측정. 온도 단계마다 이름을 바꿈 (ALPHA-12, ALPHA-15 …). 같은 시료로 측정
  그 밖의 이름은 표에만 나열

필요: pip install numpy matplotlib   (scipy 없어도 됨)
주의: 결과는 "이 장치·이 시료 조건에서"의 값이다. 일반화하지 말 것.
"""
import argparse, csv, math, pathlib, re, statistics as stt, sys
from collections import defaultdict

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
JUDGE_DWC = 0.016   # 판정선: 단위수량 +20 kg/m³ ≈ W/C 0.50 → 0.516 (페이스트 기준, 추정)
MODES = ("SINE", "SQ")
MODE_KO = {"SINE": "사인파", "SQ": "사각파"}


# ---------------- 통계 도우미 ----------------
def betainc(a, b, x):
    """정규화 불완전 베타 함수 (연분수, Numerical Recipes)."""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    def cf(a, b, x):
        qab, qap, qam = a + b, a + 1, a - 1
        c, d = 1.0, 1 - qab * x / qap
        d = 1 / (d if abs(d) > 1e-300 else 1e-300); h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
            de = d * c; h *= de
            if abs(de - 1) < 1e-12: break
        return h
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * cf(a, b, x) / a
    return 1 - math.exp(lb) * cf(b, a, 1 - x) / b


def f_pvalue(F, d1, d2):
    return betainc(d2 / 2, d1 / 2, d2 / (d2 + d1 * F)) if F > 0 else 1.0


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]: j += 1
            for k in range(i, j + 1): r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    return float(np.corrcoef(rx, ry)[0, 1]) if len(x) > 2 else float("nan")


def fnum(v, d=2):
    return "—" if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else f"{v:.{d}f}"


# ---------------- 데이터 읽기 ----------------
def read(path):
    if not path.exists(): return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "data")); ap.add_argument("--out", default=str(HERE / "result"))
    ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--ref", type=float, default=0.50, help="기준 W/C (기본 0.50)")
    a = ap.parse_args()
    D = pathlib.Path(a.data); O = pathlib.Path(a.out); O.mkdir(parents=True, exist_ok=True)
    meas, reps, temps = read(D / "meas.csv"), read(D / "rep.csv"), read(D / "temp.csv")
    if not meas: sys.exit(f"{D}/meas.csv 가 없어. logger.py로 먼저 기록해.")
    rpt = ["# 2조 W/C 판별 실험 분석 보고서", "",
           f"- 데이터: `{D}` (MEAS {len(meas)}줄, REP {len(reps)}줄, TEMP {len(temps)}줄)",
           "- **이 결과는 이 장치·이 시멘트·이 용기 조건에서의 값이다.** 현장 적용 성능을 뜻하지 않는다.", ""]

    # ---- 각 MEAS에 온도 붙이기: 같은 이름의 직전·직후 TEMP 평균 (직후는 10분 안) ----
    tby = defaultdict(list)
    for t in temps:
        if not math.isnan(num(t["T_C"])): tby[t["label"]].append((int(num(t["ms"])), num(t["T_C"])))
    for m in meas:
        ms = int(num(m["ms"])); L = tby.get(m["label"], [])
        before = [T for t, T in L if t <= ms]; after = [T for t, T in L if ms < t <= ms + 600000]
        if before and after: m["T"] = (before[-1] + after[0]) / 2; m["Tsrc"] = "전후평균"
        elif before: m["T"] = before[-1]; m["Tsrc"] = "직전"
        else: m["T"] = num(m["T_C"]); m["Tsrc"] = "펌웨어값"
        m["Zr"] = num(m["Z"])

    # ---- α 추정 (ALPHA-*) ----
    alpha_rows = []
    for mode in MODES:
        pts = [(m["T"], m["Zr"]) for m in meas if m["label"].upper().startswith("ALPHA") and m["mode"] == mode
               and not math.isnan(m["T"]) and m["Zr"] > 0]
        if len(pts) >= 3 and np.ptp([p[0] for p in pts]) >= 2:
            # 보정식과 같은 모델: 1/Z = (1 + α(T−20)) / Z20  →  1/Z 를 (T−20)에 직선 맞춤, α = 기울기/절편
            T = np.array([p[0] for p in pts]); g = 1 / np.array([p[1] for p in pts])
            sl, ic = np.polyfit(T - 20, g, 1); res = g / (sl * (T - 20) + ic) - 1
            alpha_rows.append((mode, sl / ic, len(pts), float(np.ptp(T)), float(np.std(res, ddof=2) if len(pts) > 2 else 0), T, 1 / g))
    if a.alpha is not None:
        alpha = {m: a.alpha for m in MODES}; asrc = "직접 지정"
    elif alpha_rows:
        alpha = {m: next((r[1] for r in alpha_rows if r[0] == m), alpha_rows[0][1]) for m in MODES}; asrc = "ALPHA 측정에서 추정"
    else:
        alpha = {m: 0.02 for m in MODES}; asrc = "기본값 0.02 (**측정 안 함 — 결과 해석에 주의**)"
    for m in meas: m["Z20"] = m["Zr"] * (1 + alpha[m["mode"]] * (m["T"] - 20)) if not math.isnan(m["T"]) else float("nan")

    rpt += ["## 1. 온도계수 α", "", f"- 사용한 α: " + ", ".join(f"{MODE_KO[k]} {alpha[k]:.4f}/°C" for k in MODES) + f" ({asrc})",
            "- 보정식: Z20 = Z × [1 + α(T − 20)]  (전도도 기준 S20 = S ÷ [1 + α(T − 20)] 와 같은 뜻)", ""]
    if alpha_rows:
        rpt += ["| 방식 | α 추정 [1/°C] | 점 수 | 온도 범위 [°C] | 맞춤 잔차 sd (비율) |", "|---|---|---|---|---|"]
        rpt += [f"| {MODE_KO[r[0]]} | {r[1]:.4f} | {r[2]} | {r[3]:.1f} | {r[4]:.4f} |" for r in alpha_rows]
        rpt.append("")

    # ---- 보정 저항 ----
    cal = [m for m in meas if m["label"].upper().startswith("CAL-")]
    if cal:
        rpt += ["## 2. 보정 저항 확인", "", "| 이름 | 방식 | 멀티미터 [Ω] | 측정 Z [Ω] | 오차 |", "|---|---|---|---|---|"]
        for m in cal:
            try: ref = float(m["label"].split("-", 1)[1])
            except ValueError: ref = float("nan")
            rpt.append(f"| {m['label']} | {MODE_KO.get(m['mode'], m['mode'])} | {fnum(ref,1)} | {fnum(m['Zr'])} | {fnum(100*(m['Zr']/ref-1),2)}% |")
        rpt += ["", "- 오차가 ±2%를 넘으면 `r1`·`rq` 명령으로 기준저항 실측값을 넣었는지, 집게가 제대로 물렸는지 확인.", ""]

    # ---- 소금물 ----
    salt = defaultdict(lambda: defaultdict(list))
    for m in meas:
        mm = re.match(r"SALT-([\d.]+)", m["label"].upper())
        if mm and not math.isnan(m["Z20"]): salt[m["mode"]][float(mm.group(1))].append(m["Z20"])
    if salt:
        rpt += ["## 3. 소금물 단조성 (농도↑ → Z↓ 이어야 정상)", "", "| 방식 | 농도 [g/L] → Z20 [Ω] | 단조 감소 |", "|---|---|---|"]
        for mode, dd in salt.items():
            ks = sorted(dd); zs = [float(np.median(dd[k])) for k in ks]
            mono = all(zs[i] > zs[i + 1] for i in range(len(zs) - 1))
            rpt.append(f"| {MODE_KO[mode]} | " + ", ".join(f"{k:g}→{z:.1f}" for k, z in zip(ks, zs)) + f" | {'예' if mono else '**아니오 — 회로·집게 점검**'} |")
        rpt.append("")

    # ---- 본 실험: W/C ----
    W = defaultdict(list)   # (mode, wc, batch) -> [(round, Z20, t_min, T)]
    for m in meas:
        mm = re.match(r"W(\d{3})-B(\d+)(?:-M(\d+))?$", m["label"].upper())
        if mm and not math.isnan(m["Z20"]):
            W[(m["mode"], int(mm.group(1)) / 100, int(mm.group(2)))].append((int(mm.group(3) or 1), m["Z20"], num(m["t_min"]), m["T"]))
    # 기기 반복성: REP 3개 묶음의 CV
    cvs = defaultdict(list); cur = []
    for r in reps:
        if r["rep"] == "1": cur = []
        cur.append(num(r["Z"]))
        if r["rep"] == "3" and len(cur) == 3 and all(z > 0 for z in cur):
            cvs[r["mode"]].append(100 * float(np.std(cur, ddof=1) / np.mean(cur)))
    summary = {}
    rpt += ["## 4. W/C 본 실험", ""]
    if not W:
        rpt += ["- `W050-B1-M1` 형식의 이름이 없어서 건너뜀.", ""]
    for mode in MODES:
        keys = sorted(k for k in W if k[0] == mode)
        if not keys: continue
        levels = sorted({k[1] for k in keys})
        bm = defaultdict(list); within = []; drift = []
        for k in keys:
            vals = [v[1] for v in W[k]]
            bm[k[1]].append(float(np.mean(vals)))
            if len(vals) >= 2: within.append(float(np.var(vals, ddof=1)))
            tz = [(v[2], v[1]) for v in W[k] if not math.isnan(v[2])]
            if len(tz) >= 2 and np.ptp([x[0] for x in tz]) > 0:
                drift.append(100 * np.polyfit([x[0] for x in tz], [x[1] for x in tz], 1)[0] / np.mean([x[1] for x in tz]))
        sd_lv = {L: (float(np.std(bm[L], ddof=1)) if len(bm[L]) >= 2 else float("nan")) for L in levels}
        vs = [v ** 2 for v in sd_lv.values() if not math.isnan(v)]
        s_batch = math.sqrt(sum(vs) / len(vs)) if vs else float("nan")
        s_round = math.sqrt(sum(within) / len(within)) if within else float("nan")
        mean_lv = {L: float(np.mean(bm[L])) for L in levels}
        rpt += [f"### 4-{MODES.index(mode)+1}. {MODE_KO[mode]}", "",
                f"- 기기 반복성 (같은 측정 안 3회, CV 중앙값): **{fnum(float(np.median(cvs[mode])) if cvs[mode] else float('nan'),3)}%**",
                f"- 시료 반복성 (같은 배합, 재혼합 회차 간 sd): **{fnum(s_round)} Ω**",
                f"- 배합 재현성 σ_배합 (독립 배합 간 sd, 수준 합동): **{fnum(s_batch)} Ω**",
                (f"- 수화 경과에 따른 변화: 평균 {fnum(float(np.mean(drift)),3)} %/분 (측정 창 안에서 이 값 × 경과분만큼 흔들림)" if drift else "- 경과 시간 기록 없음 (`w` 명령을 물 넣을 때 쳐야 함)"), "",
                "| W/C | 배합 수 | 배합 평균들 [Ω] | 평균 | sd |", "|---|---|---|---|---|"]
        for L in levels:
            rpt.append(f"| {L:.2f} | {len(bm[L])} | " + ", ".join(f"{v:.1f}" for v in bm[L]) + f" | {mean_lv[L]:.2f} | {fnum(sd_lv[L])} |")
        rpt.append("")
        # 기준 대비
        ref = a.ref if a.ref in mean_lv else levels[0]
        rpt += [f"기준 W/C {ref:.2f} 대비 (판정 규칙: |Δ| ≥ 3σ_배합이면 '구별됨')", "",
                "| W/C | Δ [Ω] | Δ [%] | d = Δ/σ_배합 | 3σ 판정 |", "|---|---|---|---|---|"]
        for L in levels:
            if L == ref: continue
            dlt = mean_lv[L] - mean_lv[ref]; dd = dlt / s_batch if s_batch > 0 else float("nan")
            rpt.append(f"| {L:.2f} | {dlt:+.2f} | {100*dlt/mean_lv[ref]:+.2f} | {fnum(dd)} | {'구별됨' if abs(dd) >= 3 else '구별 안 됨'} |")
        rpt.append("")
        # ANOVA (배합 평균 기준)
        groups = [bm[L] for L in levels if len(bm[L]) >= 1]
        allv = [v for g in groups for v in g]; k_ = len(groups); n_ = len(allv)
        if k_ >= 2 and n_ > k_:
            gm = float(np.mean(allv))
            ssb = sum(len(g) * (np.mean(g) - gm) ** 2 for g in groups); ssw = sum(sum((v - np.mean(g)) ** 2 for v in g) for g in groups)
            F = (ssb / (k_ - 1)) / (ssw / (n_ - k_)) if ssw > 0 else float("inf")
            p = f_pvalue(F, k_ - 1, n_ - k_) if math.isfinite(F) else 0.0
            rpt.append(f"- 일원분산분석 (배합 평균, 수준 {k_}개, 배합 {n_}개): F({k_-1}, {n_-k_}) = {fnum(F)}, p = {p:.2g}")
        rho = spearman([L for L in levels], [mean_lv[L] for L in levels])
        mono = all(np.diff([mean_lv[L] for L in levels]) > 0) or all(np.diff([mean_lv[L] for L in levels]) < 0)
        rpt.append(f"- 단조성: 수준 평균이 {'한 방향으로 단조' if mono else '**단조 아님**'}, Spearman ρ = {fnum(rho)}")
        # 감도와 검출 한계
        xs = [L for L in levels for _ in bm[L]]; ys = [v for L in levels for v in bm[L]]
        slope = float(np.polyfit(xs, ys, 1)[0]) if len(set(xs)) >= 2 else float("nan")
        mdc = 3 * s_batch / abs(slope) if slope and not math.isnan(slope) and s_batch > 0 else float("nan")
        rpt += [f"- 감도 (배합 평균의 직선 기울기): {fnum(slope)} Ω per W/C 1.0 → W/C 0.01당 {fnum(slope/100)} Ω",
                f"- **검출 가능한 최소 W/C 변화 (3σ_배합 / 감도): {fnum(mdc,3)}** — 판정선(+20 kg/m³ ≈ W/C +{JUDGE_DWC}) "
                + ("**이하 → 판정선 수준을 구별 가능**" if mdc <= JUDGE_DWC else "**보다 큼 → 판정선 수준은 구별 못 함**" if not math.isnan(mdc) else "(계산 불가)"), ""]
        summary[mode] = dict(slope=slope, s_batch=s_batch, ratio=abs(slope) / s_batch if s_batch > 0 else float("nan"), mdc=mdc, levels=levels, bm=bm, mean=mean_lv)

    # ---- 방식 비교 ----
    if len(summary) == 2:
        rs, rq = summary["SINE"]["ratio"], summary["SQ"]["ratio"]
        rpt += ["## 5. 사인파 대 사각파 (같은 시료)", "", "| 방식 | 감도 |기울기| / σ_배합 | 검출 최소 ΔW/C |", "|---|---|---|"]
        rpt += [f"| {MODE_KO[m]} | {fnum(summary[m]['ratio'],1)} | {fnum(summary[m]['mdc'],3)} |" for m in MODES]
        if not (math.isnan(rs) or math.isnan(rq)):
            hi, lo = max(rs, rq), min(rs, rq)
            if hi / lo < 1.2: pick = "사각파 (두 방식 차이가 20% 안 → 규칙대로 더 간단한 쪽)"
            else: pick = "사인파" if rs > rq else "사각파"
            rpt += ["", f"- 규칙('차이/σ'가 큰 쪽, 비슷하면 간단한 쪽)에 따른 선택: **{pick}**", ""]

    # ---- 기타 이름 ----
    other = sorted({m["label"] for m in meas} - {m["label"] for m in meas if re.match(r"(W\d{3}-B\d+|CAL-|SALT-|ALPHA)", m["label"].upper())})
    if other: rpt += ["## 6. 규칙 밖 이름 (분석 제외)", "", ", ".join(f"`{x}`" for x in other), ""]
    rpt += ["---", "판정 기준: 차이 ≥ 3σ (σ = 독립 배합 간 표준편차). 펌웨어 LCD의 OK/ABN은 기준 시료 반복 σ나 `sig` 값으로 낸 **보조 표시**이고, 공식 판정은 이 보고서의 σ_배합 기준이다."]

    # ---- 그림 ----
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        if summary:
            fig, ax = plt.subplots(figsize=(6.4, 4.2))
            for mode, mk in zip(MODES, ("o", "s")):
                if mode not in summary: continue
                S = summary[mode]
                for L in S["levels"]: ax.plot([L] * len(S["bm"][L]), S["bm"][L], mk, alpha=.35, color="C0" if mode == "SINE" else "C1")
                ax.errorbar(S["levels"], [S["mean"][L] for L in S["levels"]], yerr=[3 * S["s_batch"]] * len(S["levels"]), fmt=mk + "-", capsize=4,
                            color="C0" if mode == "SINE" else "C1", label=f"{'sine' if mode=='SINE' else 'square'} (bar = ±3σ batch)")
            ax.set_xlabel("W/C"); ax.set_ylabel("Z at 20 °C [ohm]"); ax.grid(alpha=.3); ax.legend(); fig.tight_layout()
            fig.savefig(O / "fig_wc.png", dpi=160); plt.close(fig); rpt.insert(5, "![W/C vs Z20](fig_wc.png)\n")
        if alpha_rows:
            fig, ax = plt.subplots(figsize=(6.4, 4.2))
            for r in alpha_rows:
                ax.plot(r[5], r[6], "o", label=f"{'sine' if r[0]=='SINE' else 'square'}  alpha={r[1]:.4f}/°C")
            ax.set_xlabel("T [°C]"); ax.set_ylabel("Z [ohm]"); ax.grid(alpha=.3); ax.legend(); fig.tight_layout()
            fig.savefig(O / "fig_alpha.png", dpi=160); plt.close(fig)
    except ImportError:
        rpt.append("\n(matplotlib이 없어서 그림은 건너뜀: pip install matplotlib)")
    (O / "report.md").write_text("\n".join(rpt) + "\n", encoding="utf-8")
    print("\n".join(rpt)); print(f"\n저장: {O/'report.md'}")


if __name__ == "__main__":
    main()
