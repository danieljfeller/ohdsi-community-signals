"""Build the blog post HTML with to-scale inline SVG figures from report/figure_data.json."""
import json, math, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
D = json.load(open(ROOT / "report" / "figure_data.json"))
OUT = ROOT / "report" / "blog" / "ohdsi-community-signals.html"

def esc(s): return html.escape(str(s))
QS = list(D["composition"].keys())
QL = [q.replace("20", "'").replace(" ", " ") for q in QS]  # '24 Q4

# ---------- Fig 1: composition by quarter (stacked columns, 2 series) ----------
def fig1():
    W, H = 680, 320; ml, mr, mt, mb = 44, 16, 28, 44
    pw, ph = W - ml - mr, H - mt - mb
    subst = [sum(D["composition"][q][k] for k in ["question", "bug", "discussion", "feature_request"]) for q in QS]
    other = [sum(D["composition"][q][k] for k in ["announcement", "job_or_event", "other"]) for q in QS]
    ymax = 125; y = lambda v: mt + ph - v / ymax * ph
    band = pw / len(QS); bw = min(24, band * 0.55)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f1t"><title id="f1t">Forum topics per quarter, substantive versus announcements</title>']
    for t in [0, 25, 50, 75, 100, 125]:
        s.append(f'<line x1="{ml}" x2="{W-mr}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/><text x="{ml-8}" y="{y(t)+4:.1f}" class="tick" text-anchor="end">{t}</text>')
    for i, q in enumerate(QS):
        cx = ml + band * (i + 0.5); x0 = cx - bw / 2
        a, b = subst[i], other[i]
        s.append(f'<rect x="{x0:.1f}" y="{y(a):.1f}" width="{bw:.1f}" height="{(ph*a/ymax):.1f}" class="m1"><title>{q}: {a} substantive threads</title></rect>')
        s.append(f'<rect x="{x0:.1f}" y="{y(a+b):.1f}" width="{bw:.1f}" height="{max(ph*b/ymax-2,0):.1f}" class="mg"><title>{q}: {b} announcements, events and other</title></rect>')
        s.append(f'<text x="{cx:.1f}" y="{H-mb+18}" class="tick" text-anchor="middle">{QL[i]}</text>')
        if i in (0, len(QS) - 1):
            s.append(f'<text x="{cx:.1f}" y="{y(a)+ (ph*a/ymax)/2 + 4:.1f}" class="inlbl" text-anchor="middle">{a}</text>')
            s.append(f'<text x="{cx:.1f}" y="{y(a+b)-6:.1f}" class="lbl" text-anchor="middle">{a+b} total</text>')
    s.append(f'<line x1="{ml}" x2="{W-mr}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axis"/>')
    s.append(f'<text x="{ml}" y="16" class="lbl">Topics per quarter</text>')
    s.append('</svg>')
    legend = '<div class="legend"><span><i class="sw m1"></i>Substantive (questions, bugs, feature requests, discussions)</span><span><i class="sw mg"></i>Announcements, events, other</span></div>'
    rows = "".join(f"<tr><td>{q}</td><td>{subst[i]}</td><td>{other[i]}</td><td>{subst[i]+other[i]}</td></tr>" for i, q in enumerate(QS))
    table = f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Quarter</th><th>Substantive</th><th>Announcements, events, other</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table></details>'
    return "".join(s) + legend + table

# ---------- Fig 2: resolution of substantive threads (ordinal stacked bar) ----------
def fig2():
    r = D["resolution"]; order = [("no_reply", "No reply", "o1"), ("unresolved", "Unresolved", "o2"), ("partially", "Partially answered", "o3"), ("resolved", "Resolved", "o4"), ("unclear", "Unclear", "mg")]
    vals = {"no_reply": r["no_reply"], "unresolved": r["unresolved"], "partially": r["partially"], "resolved": r["resolved"] + r.get("resolved_self", 0), "unclear": r["unclear"]}
    N = sum(vals.values()); W, H = 680, 118; ml, mr = 8, 8; pw = W - ml - mr; y0, bh = 46, 26
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f2t"><title id="f2t">Resolution status of {N} substantive threads</title>']
    x = ml; unmet_w = 0
    for k, lab, cls in order:
        w = pw * vals[k] / N
        s.append(f'<rect x="{x+1:.1f}" y="{y0}" width="{max(w-2,0):.1f}" height="{bh}" class="{cls}"><title>{lab}: {vals[k]} threads ({vals[k]/N:.0%})</title></rect>')
        if w > 54: s.append(f'<text x="{x+w/2:.1f}" y="{y0+bh/2+4}" class="inlbl" text-anchor="middle">{vals[k]/N:.0%}</text>')
        if k in ("no_reply", "unresolved", "partially"): unmet_w += w
        x += w
    s.append(f'<path d="M{ml+2} 36 v-8 H{ml+unmet_w-2:.1f} v8" class="bracket"/><text x="{ml+unmet_w/2:.1f}" y="18" class="lbl" text-anchor="middle">{(vals["no_reply"]+vals["unresolved"]+vals["partially"])/N:.0%} not fully resolved</text>')
    s.append(f'<text x="{W-mr}" y="{y0+bh+24}" class="tick" text-anchor="end">n = {N} substantive threads</text></svg>')
    legend = '<div class="legend">' + "".join(f'<span><i class="sw {cls}"></i>{lab}</span>' for _, lab, cls in order) + '</div>'
    rows = "".join(f"<tr><td>{lab}</td><td>{vals[k]}</td><td>{vals[k]/N:.0%}</td></tr>" for k, lab, _ in order)
    return "".join(s) + legend + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Status</th><th>Threads</th><th>Share</th></tr></thead><tbody>{rows}</tbody></table></details>'

# ---------- Fig 3: lifecycle bubble scatter ----------
NAMES = {"data_quality": "Data quality", "infrastructure_deployment": "Infrastructure & deployment", "characterization": "Characterization", "estimation": "Estimation", "etl_cdm_conversion": "ETL / CDM conversion", "vocabulary_mapping": "Vocabulary mapping", "community_process": "Community process", "governance_privacy": "Governance & privacy", "network_study_execution": "Network study execution", "learning_onboarding": "Learning & onboarding", "cohort_definition": "Cohort definition", "prediction_ml": "Prediction / ML", "results_sharing_dissemination": "Results sharing"}
def fig3():
    L = D["lifecycle"]; W, H = 680, 420; ml, mr, mt, mb = 56, 170, 28, 48; pw, ph = W - ml - mr, H - mt - mb
    xmin, xmax, ymin, ymax = 0, 140, 1.0, 2.5
    X = lambda v: ml + (v - xmin) / (xmax - xmin) * pw; Y = lambda v: mt + ph - (v - ymin) / (ymax - ymin) * ph
    R = lambda b: 5 + b * 40   # radius encodes blocker share
    place = {"infrastructure_deployment": ("right",), "data_quality": ("right",), "characterization": ("right",), "learning_onboarding": ("right",), "community_process": ("right",),
             "vocabulary_mapping": ("at", 96, 1.34, "start"), "etl_cdm_conversion": ("at", 86, 1.50, "start"), "governance_privacy": ("at", 4, 2.42, "start"), "estimation": ("at", 4, 2.32, "start"),
             "network_study_execution": ("at", 4, 2.20, "start"), "prediction_ml": ("at", 24, 2.0, "start"), "cohort_definition": ("at", 44, 1.40, "start"), "results_sharing_dissemination": ("at", 0, 1.36, "start")}
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f3t"><title id="f3t">Lifecycle stages by volume and severity</title>']
    for t in [1.0, 1.5, 2.0, 2.5]:
        s.append(f'<line x1="{ml}" x2="{X(xmax):.1f}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="grid"/><text x="{ml-8}" y="{Y(t)+4:.1f}" class="tick" text-anchor="end">{t:.1f}</text>')
    for t in [0, 25, 50, 75, 100, 125]:
        s.append(f'<line y1="{mt}" y2="{mt+ph}" x1="{X(t):.1f}" x2="{X(t):.1f}" class="grid"/><text y="{mt+ph+18}" x="{X(t):.1f}" class="tick" text-anchor="middle">{t}</text>')
    s.append(f'<text x="{ml+pw/2:.1f}" y="{H-8}" class="lbl" text-anchor="middle">Need threads tagged with the stage</text>')
    s.append(f'<text transform="translate(14 {mt+ph/2:.1f}) rotate(-90)" class="lbl" text-anchor="middle">Mean severity (0 none to 3 blocker)</text>')
    byk = {r["lifecycle_stage"]: r for r in L}
    for row in sorted(L, key=lambda r: -r["blocker_share"]):
        k = row["lifecycle_stage"]; cx, cy, r = X(row["n_need_threads"]), Y(row["mean_severity"]), R(row["blocker_share"])
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="bub"><title>{NAMES[k]}: {row["n_need_threads"]} need threads, mean severity {row["mean_severity"]:.2f}, {row["blocker_share"]:.0%} blockers</title></circle>')
    for k, spec in place.items():
        row = byk[k]; cx, cy, r = X(row["n_need_threads"]), Y(row["mean_severity"]), R(row["blocker_share"]); label = f'{NAMES[k]} <tspan class="tick">({row["n_need_threads"]})</tspan>'
        if spec[0] == "right": s.append(f'<text x="{cx+r+6:.1f}" y="{cy+4:.1f}" class="lbl">{label}</text>')
        else:
            _, lx, ly, anc = spec; tx, ty = X(lx), Y(ly)
            dx, dy = tx - cx, ty - cy; d = math.hypot(dx, dy) or 1; ex, ey = cx + dx / d * r, cy + dy / d * r
            s.append(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" class="leader"/>')
            s.append(f'<text x="{tx+4:.1f}" y="{ty+4:.1f}" class="lbl" text-anchor="{anc}">{label}</text>')
    s.append(f'<text x="{X(xmax):.1f}" y="{mt-8}" class="tick" text-anchor="end">Bubble radius encodes share of threads rated blocker; hover for values</text></svg>')
    rows = "".join(f'<tr><td>{NAMES[r["lifecycle_stage"]]}</td><td>{r["n_need_threads"]}</td><td>{r["mean_severity"]:.2f}</td><td>{r["blocker_share"]:.0%}</td><td>{r["unresolved_rate"]:.0%}</td><td>{r["unmet_need_index"]:.2f}</td></tr>' for r in sorted(L, key=lambda r: -r["n_need_threads"]))
    return "".join(s) + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Lifecycle stage</th><th>Need threads</th><th>Mean severity</th><th>Blocker share</th><th>Unresolved</th><th>Unmet Need Index</th></tr></thead><tbody>{rows}</tbody></table></details>'

# ---------- Fig T: tools named in substantive threads ----------
def figT():
    T = D["tools"]; rowh = 22; ml, mr, mt, mb = 150, 60, 26, 30; W = 680; H = mt + rowh * len(T) + mb; pw = W - ml - mr; xmax = 140
    X = lambda v: ml + v / xmax * pw
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ftt"><title id="ftt">OHDSI tools named in substantive threads</title>']
    for t in [0, 25, 50, 75, 100, 125]:
        s.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{mt-4}" y2="{H-mb+4}" class="grid"/><text x="{X(t):.1f}" y="{H-mb+18}" class="tick" text-anchor="middle">{t}</text>')
    for i, r in enumerate(T):
        yy = mt + i * rowh + 3
        s.append(f'<rect x="{ml}" y="{yy}" width="{X(r["n"])-ml:.1f}" height="{rowh-6}" class="m1"><title>{r["t"]}: named in {r["n"]} substantive threads</title></rect>')
        s.append(f'<text x="{ml-8}" y="{yy+rowh-9}" class="lbl" text-anchor="end">{r["t"]}</text><text x="{X(r["n"])+6:.1f}" y="{yy+rowh-9}" class="tick">{r["n"]}</text>')
    s.append(f'<text x="{ml}" y="14" class="lbl">Substantive threads naming the tool (n = 429; a thread may name several)</text></svg>')
    rows = "".join(f'<tr><td>{r["t"]}</td><td>{r["n"]}</td></tr>' for r in T)
    return "".join(s) + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Tool</th><th>Threads</th></tr></thead><tbody>{rows}</tbody></table></details>'

# ---------- Fig 4: needs taxonomy bars ----------
FIT = {"data_harmonization": ("m1", "Data harmonization"), "federated_analytics": ("m2", "Federated analytics"), "none": ("mg", "No Rhino fit (tooling, deployment, process)")}
def fig4():
    N = sorted(D["needs"], key=lambda r: -r["unmet_need_index"]); rowh = 21; ml, mr, mt, mb = 335, 76, 26, 30; W = 800; H = mt + rowh * len(N) + mb; pw = W - ml - mr
    X = lambda v: ml + v / 0.8 * pw
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f4t"><title id="f4t">Twenty-nine community needs ranked by Unmet Need Index</title>']
    for t in [0, 0.2, 0.4, 0.6, 0.8]:
        s.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{mt-4}" y2="{H-mb+4}" class="grid"/><text x="{X(t):.1f}" y="{H-mb+18}" class="tick" text-anchor="middle">{t:.1f}</text>')
    for i, r in enumerate(N):
        yy = mt + i * rowh + 3; cls, _ = FIT[r["rhino_fit"]]; lab = r["label"]
        s.append(f'<rect x="{ml}" y="{yy}" width="{(X(r["unmet_need_index"])-ml):.1f}" height="{rowh-6}" class="{cls}" rx="0"><title>{esc(lab)}: index {r["unmet_need_index"]:.2f}, {r["n_need_threads"]} threads, {r["unresolved_rate"]:.0%} unresolved</title></rect>')
        s.append(f'<text x="{ml-8}" y="{yy+rowh-9}" class="lbl" text-anchor="end">{esc(lab)}</text>')
        s.append(f'<text x="{X(r["unmet_need_index"])+6:.1f}" y="{yy+rowh-9}" class="tick">{r["n_need_threads"]} thr · {r["unresolved_rate"]:.0%}</text>')
    s.append(f'<text x="{ml}" y="14" class="lbl">Unmet Need Index (0 to 1)</text><text x="{W-mr}" y="14" class="tick" text-anchor="end">threads · unresolved</text></svg>')
    legend = '<div class="legend">' + "".join(f'<span><i class="sw {c}"></i>{l}</span>' for c, l in FIT.values()) + '</div>'
    rows = "".join(f'<tr><td>{esc(r["label"])}</td><td>{r["n_need_threads"]}</td><td>{r["unresolved_rate"]:.0%}</td><td>{r["mean_severity"]:.2f}</td><td>{r["unmet_need_index"]:.2f}</td><td>{FIT[r["rhino_fit"]][1]}</td></tr>' for r in N)
    return "".join(s) + legend + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Need</th><th>Threads</th><th>Unresolved</th><th>Mean severity</th><th>Index</th><th>Fit</th></tr></thead><tbody>{rows}</tbody></table></details>'

# ---------- Fig 5: multi-site threads as dots per quarter ----------
def fig5():
    M = D["multisite_q"]; T = D["multisite_total"]; W, H = 680, 250; ml, mb, mt = 24, 40, 30; band = (W - 2 * ml) / len(QS); r = 6; gap = 16
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f5t"><title id="f5t">Multi-site threads per quarter, unresolved versus resolved</title>']
    base = H - mb
    for i, q in enumerate(QS):
        m = M.get(q, {"n": 0, "unmet": 0}); n, u = int(m["n"]), int(m["unmet"]); cx = ml + band * (i + 0.5)
        for j in range(n):
            cy = base - 8 - j * gap; cls = "dotf" if j < u else "doto"
            s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" class="{cls}"><title>{q}: {n} multi-site threads, {u} not resolved</title></circle>')
        s.append(f'<text x="{cx:.1f}" y="{H-mb+20}" class="tick" text-anchor="middle">{QL[i]}</text>')
        if n: s.append(f'<text x="{cx:.1f}" y="{base-8-n*gap+2:.1f}" class="tick" text-anchor="middle">{n}</text>')
    s.append(f'<line x1="{ml}" x2="{W-ml}" y1="{base}" y2="{base}" class="axis"/>')
    s.append(f'<text x="{ml}" y="16" class="lbl">{T["unmet"]} of {T["n"]} multi-site threads not fully resolved ({T["unmet"]/T["n"]:.0%}), against {T["all_unmet"]/T["all_n"]:.0%} for all substantive threads</text></svg>')
    legend = '<div class="legend"><span><i class="sw dotf round"></i>Not fully resolved</span><span><i class="sw doto round"></i>Resolved</span></div>'
    rows = "".join(f'<tr><td>{q}</td><td>{int(M.get(q,{"n":0})["n"])}</td><td>{int(M.get(q,{"unmet":0})["unmet"])}</td></tr>' for q in QS)
    return "".join(s) + legend + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Quarter</th><th>Multi-site threads</th><th>Not fully resolved</th></tr></thead><tbody>{rows}</tbody></table></details>'

# ---------- Fig 6: inter-coder agreement ----------
def fig6():
    K = [k for k in D["kappa"] if k["cohen_kappa"] == k["cohen_kappa"]]  # drop NaN (lifecycle Jaccard)
    names = {"post_type": "Post type", "severity": "Severity", "resolution_status": "Resolution status", "multi_site_context": "Multi-site context", "harmonization_context": "Harmonization context", "workaround_present": "Workaround present", "pain_point_present": "Pain point present"}
    K = sorted(K, key=lambda k: -k["cohen_kappa"]); W, H = 680, 40 + 26 * len(K) + 50; ml, mr, mt = 170, 90, 40; pw = W - ml - mr
    X = lambda v: ml + v * pw
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f6t"><title id="f6t">Inter-coder agreement, Cohen\'s kappa by field</title>']
    bands = [(0.0, 0.2, "slight"), (0.2, 0.4, "fair"), (0.4, 0.6, "moderate"), (0.6, 0.8, "substantial"), (0.8, 1.0, "almost perfect")]
    for a, b, lab in bands:
        s.append(f'<rect x="{X(a):.1f}" y="{mt-10}" width="{X(b)-X(a):.1f}" height="{26*len(K)+10}" class="{"bandA" if bands.index((a,b,lab))%2 else "bandB"}"/><text x="{(X(a)+X(b))/2:.1f}" y="{mt-16}" class="tick" text-anchor="middle">{lab}</text>')
    for t in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        s.append(f'<text x="{X(t):.1f}" y="{H-14}" class="tick" text-anchor="middle">{t:.1f}</text>')
    for i, k in enumerate(K):
        yy = mt + i * 26 + 10
        s.append(f'<line x1="{ml}" x2="{X(1):.1f}" y1="{yy}" y2="{yy}" class="grid"/>')
        s.append(f'<text x="{ml-10}" y="{yy+4}" class="lbl" text-anchor="end">{names[k["field"]]}</text>')
        s.append(f'<circle cx="{X(k["cohen_kappa"]):.1f}" cy="{yy}" r="6" class="dotf"><title>{names[k["field"]]}: kappa {k["cohen_kappa"]:.2f}, {k["percent_agreement"]:.0%} agreement</title></circle>')
        s.append(f'<text x="{X(1)+10:.1f}" y="{yy+4}" class="tick">κ {k["cohen_kappa"]:.2f} · {k["percent_agreement"]:.0%}</text>')
    s.append(f'<text x="{ml+pw/2:.1f}" y="{H-0}" class="lbl" text-anchor="middle" dy="-0.2em"></text></svg>')
    rows = "".join(f'<tr><td>{names[k["field"]]}</td><td>{k["percent_agreement"]:.0%}</td><td>{k["cohen_kappa"]:.2f}</td></tr>' for k in K)
    return "".join(s) + f'<details class="tbl"><summary>Data table</summary><table><thead><tr><th>Field</th><th>Percent agreement</th><th>Cohen\'s kappa</th></tr></thead><tbody>{rows}</tbody></table></details>'

FIGS = {"f3": fig3(), "fT": figT(), "f4": fig4(), "f5": fig5(), "f6": fig6()}

CSS = """
<meta charset="utf-8">
<title>OHDSI Community Signals</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: a single reading column (65ch) for prose; figures break out to 760px and sit on a chart surface with a numbered caption, journal style. */
:root{
  --bg:#f6f7f8; --surface:#fcfcfb; --fg:#15181c; --fg2:#4d5560; --muted:#848b94; --grid:#e3e5e8; --axis:#c2c7cd; --border:rgba(21,24,28,.10);
  --accent:#2a78d6; --m1:#2a78d6; --m2:#eb6834; --m3:#1baf7a; --mg:#b9bec5;
  --o1:#184f95; --o2:#256abf; --o3:#5598e7; --o4:#86b6ef; --bandA:rgba(42,120,214,.06); --bandB:rgba(42,120,214,.02);
  --wash:rgba(42,120,214,.14); --quote:#eef3fa;
  --serif:"Newsreader",Georgia,"Times New Roman",serif; --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#111417; --surface:#1a1d21; --fg:#f2f3f4; --fg2:#c3c7cc; --muted:#8c929a; --grid:#2b3036; --axis:#3a4047; --border:rgba(255,255,255,.10);
  --accent:#3987e5; --m1:#3987e5; --m2:#d95926; --m3:#199e70; --mg:#4a5058;
  --o1:#184f95; --o2:#256abf; --o3:#5598e7; --o4:#86b6ef; --bandA:rgba(57,135,229,.10); --bandB:rgba(57,135,229,.04); --wash:rgba(57,135,229,.18); --quote:#1d242e; color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#111417; --surface:#1a1d21; --fg:#f2f3f4; --fg2:#c3c7cc; --muted:#8c929a; --grid:#2b3036; --axis:#3a4047; --border:rgba(255,255,255,.10);
  --accent:#3987e5; --m1:#3987e5; --m2:#d95926; --m3:#199e70; --mg:#4a5058;
  --o1:#184f95; --o2:#256abf; --o3:#5598e7; --o4:#86b6ef; --bandA:rgba(57,135,229,.10); --bandB:rgba(57,135,229,.04); --wash:rgba(57,135,229,.18); --quote:#1d242e; color-scheme:dark }
body{background:var(--bg);color:var(--fg);font-family:var(--serif);font-size:19px;line-height:1.55;margin:0;padding-block:0 64px;padding-inline:16px}
.wrap{max-width:760px;margin:0 auto}
.prose{max-width:65ch;margin:0 auto}
h1,h2,h3{font-family:var(--serif);text-wrap:balance;line-height:1.15;margin:0}
h1{font-size:clamp(34px,6vw,52px);font-weight:500;letter-spacing:-.01em;margin-top:56px}
h2{font-size:clamp(25px,3.6vw,31px);font-weight:500;margin-top:56px;margin-bottom:14px}
h3{font-size:21px;font-weight:600;margin-top:28px;margin-bottom:8px}
p{margin:0 0 1.1em}
.kicker{font-family:var(--sans);font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--fg2);margin-top:40px}
.standfirst{font-size:23px;line-height:1.4;color:var(--fg2);margin:18px 0 10px;font-weight:400}
.byline{font-family:var(--sans);font-size:14px;color:var(--muted);margin:14px 0 44px;display:flex;gap:18px;flex-wrap:wrap}
.abstract{border-top:1px solid var(--fg);border-bottom:1px solid var(--border);padding:20px 0 8px;margin:0 0 40px;font-size:17px;line-height:1.5}
.abstract dt{font-family:var(--sans);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--fg2);margin-top:12px}
.abstract dd{margin:4px 0 0}
.figure{background:var(--surface);border:1px solid var(--border);padding:18px 20px 14px;margin:30px 0 36px;font-family:var(--sans)}
.figure .fig{width:100%;height:auto;display:block}
figcaption{font-size:14px;line-height:1.5;color:var(--fg2);margin-top:12px}
figcaption b{color:var(--fg);font-weight:600}
.legend{display:flex;flex-wrap:wrap;gap:10px 20px;font-size:13px;color:var(--fg2);margin-top:10px}
.sw{display:inline-block;width:12px;height:12px;margin-right:7px;vertical-align:-1px}
.sw.round{border-radius:50%}
.m1{fill:var(--m1);background:var(--m1)} .m2{fill:var(--m2);background:var(--m2)} .m3{fill:var(--m3);background:var(--m3)} .mg{fill:var(--mg);background:var(--mg)}
.o1{fill:var(--o1);background:var(--o1)} .o2{fill:var(--o2);background:var(--o2)} .o3{fill:var(--o3);background:var(--o3)} .o4{fill:var(--o4);background:var(--o4)}
.grid{stroke:var(--grid);stroke-width:1} .axis{stroke:var(--axis);stroke-width:1} .bracket{fill:none;stroke:var(--fg2);stroke-width:1} .leader{stroke:var(--axis);stroke-width:1}
.tick{font-family:var(--sans);font-size:12px;fill:var(--muted)} .lbl{font-family:var(--sans);font-size:12.5px;fill:var(--fg2)} .inlbl{font-family:var(--sans);font-size:12px;fill:#fff;font-weight:600}
.bub{fill:var(--wash);stroke:var(--m1);stroke-width:2}
.dotf{fill:var(--m1);stroke:var(--surface);stroke-width:2;background:var(--m1)} .doto{fill:var(--surface);stroke:var(--m1);stroke-width:2;background:transparent;box-shadow:inset 0 0 0 2px var(--m1)}
.bandA{fill:var(--bandA)} .bandB{fill:var(--bandB)}
rect.m1,rect.m2,rect.m3,rect.mg,rect.o1,rect.o2,rect.o3,rect.o4{rx:0}
.tbl{margin-top:10px;font-size:13px;color:var(--fg2)} .tbl summary{cursor:pointer;color:var(--accent)} .tbl table{border-collapse:collapse;margin-top:8px;width:100%;font-variant-numeric:tabular-nums} .tbl th,.tbl td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--grid)} .tbl th{font-weight:600;color:var(--fg)}
.tblwrap{overflow-x:auto}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:28px 0 8px;font-family:var(--sans)}
.stat{border-top:2px solid var(--fg);padding-top:10px} .stat b{display:block;font-size:34px;font-weight:600;line-height:1.1;color:var(--fg)} .stat span{display:block;font-size:13px;color:var(--fg2);margin-top:6px;line-height:1.35}
blockquote{margin:22px 0;padding:14px 20px;background:var(--quote);border-left:3px solid var(--accent);font-style:italic;font-size:18px;color:var(--fg)}
blockquote cite{display:block;font-style:normal;font-family:var(--sans);font-size:12.5px;color:var(--muted);margin-top:6px}
.note{font-family:var(--sans);font-size:15px;line-height:1.5;color:var(--fg2);border:1px solid var(--border);padding:16px 18px;margin:28px 0}
.note h3{font-family:var(--sans);font-size:14px;letter-spacing:.06em;text-transform:uppercase;margin:0 0 8px;color:var(--fg)}
ul,ol{padding-left:1.2em} li{margin-bottom:.45em}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.foot{font-family:var(--sans);font-size:14px;color:var(--muted);border-top:1px solid var(--border);margin-top:56px;padding-top:18px;line-height:1.55}
@media (max-width:520px){ body{font-size:17px} .figure{padding:12px 10px} .standfirst{font-size:20px} }
@media (prefers-reduced-motion: no-preference){ details[open] summary ~ *{animation:fade .25s ease} } @keyframes fade{from{opacity:.3}to{opacity:1}}
</style>
"""

BODY = f"""
<div class="wrap">
<div class="prose">
<p class="kicker">Community research \u00b7 Observational health data</p>
<h1>What two years of OHDSI forum threads say about the community\u2019s technology needs</h1>
<p class="standfirst">We read every public thread posted to the OHDSI Forums between October 2024 and October 2026 and coded each one for the technical problem behind it. The result is a ranked map of 29 needs. The hardest are not about running studies. They are about getting data into OMOP faithfully, keeping the platform running, and trusting that two sites mean the same thing.</p>
<div class="byline"><span>Daniel Feller, PhD \u00b7 Rhino Federated Computing</span><span>October 2026</span><span>11 min read</span></div>

<dl class="abstract">
<dt>Background</dt><dd>OHDSI is the largest open community working with observational health data on a shared model, the OMOP Common Data Model. Its public forum is one of the few places where the technical friction of that work is written down in the words of the people doing it.</dd>
<dt>Methods</dt><dd>776 forum topics (2,164 posts) were collected through the forum\u2019s public API, pseudonymized, and coded by a language model against a fixed schema: post type, lifecycle stage, tools, pain point, severity and multi-site context. An independent second coder re-coded an 80-thread sample. Pain-point sentences were clustered into a bottom-up taxonomy of 29 needs and scored on volume, severity, unresolved share and trend.</dd>
<dt>Results</dt><dd>429 threads carried a technical need. Vocabulary mapping and ETL accounted for 43% of need statements and 12 of 29 need clusters; infrastructure and data quality carried the highest severity, with a third of infrastructure threads rated blockers. Threads involving more than one site were 11% of the corpus and concerned comparability of results rather than execution of studies.</dd>
<dt>Conclusions</dt><dd>The community\u2019s dominant technology need is harmonization, at the level of specific failures: combination drugs, oncology and genomic concepts, lab domains, hierarchy-unreachable mappings. The federated need expressed is cross-site comparability and sharing without patient-level data. Federated learning does not appear.</dd>
</dl>

<h2>Why read a forum?</h2>
<p>Every research community leaves a record of what it finds hard. Papers describe what worked. Forums describe what did not, in the moment, in the words of the person who was stuck. For OHDSI (the Observational Health Data Sciences and Informatics collaborative), that record sits at forums.ohdsi.org, a public Discourse site with more than 8,000 topics since 2014.</p>
<p>We work on federated computing for healthcare, and OHDSI\u2019s network studies, where analysis code travels to data partners and only aggregate results travel back, are a close cousin of what we build. Before deciding what to build next for this community, we wanted a reading of its needs that did not start from our product. So we started from the text.</p>
<p>One limitation shapes everything that follows and is stated up front. Much of OHDSI\u2019s working conversation has moved to Microsoft Teams, which is not public. The forum is therefore the public, implementer-heavy slice of the community: 72% of the people who posted a substantive thread posted once. It is a good instrument for what first-time and solo implementers run into, and a poor one for what experienced network-study coordinators discuss among themselves. The needs below are real; their relative weights would shift with a Teams corpus, and we say where we think they would shift.</p>

<h2>1. Where the pain concentrates</h2>
<p>Each of the 429 substantive threads was tagged with the stage of the OHDSI lifecycle it concerned, from converting source data, through vocabulary mapping and data quality, to cohort building, analysis and sharing results. Figure 1 places each stage by how many threads it attracted and how severe they were.</p>
</div>

<figure class="figure" id="fig1">{FIGS['f3']}<figcaption><b>Figure 1.</b> Thirteen lifecycle stages positioned by the number of need threads tagged with the stage (horizontal; a thread may carry several tags) and mean coded severity (vertical; 0 none, 1 minor, 2 major, 3 blocker). Bubble radius encodes the share of the stage\u2019s threads rated blocking. Harmonization stages have the volume; infrastructure has the severity.</figcaption></figure>

<div class="prose">
<p>Two regions matter. Far right and moderate severity: <b>vocabulary mapping</b> (127 need threads) and <b>ETL / CDM conversion</b> (114). Together they account for 43% of all need statements. Their severity is mostly \u201cmajor\u201d rather than \u201cblocker\u201d because the work continues around the gap, with lost information rather than a halted pipeline.</p>
<p>Upper middle and large bubbles: <b>infrastructure and deployment</b> (64) and <b>data quality</b> (60). These are the threads about installing Atlas and WebAPI, authenticating against LDAP, and running Achilles or the Data Quality Dashboard on a large database. A third of infrastructure threads were blockers, the highest share of any stage.</p>
<p>Notice what is small. <b>Network study execution</b>, the activity OHDSI is best known for, appears in 13 threads. Strategus, the framework that runs network studies, is named seven times in two years. This is partly the Teams effect described above: study coordinators are the group most likely to have left the forum. But it is also consistent with what the multi-site threads that do exist say (section 4): the difficulty people describe is not executing a study across sites, it is trusting the result.</p>

<h2>2. The tools people get stuck on</h2>
<p>The coder recorded every OHDSI tool a thread named or clearly implied. Figure 2 counts them.</p>
</div>

<figure class="figure" id="fig2">{FIGS['fT']}<figcaption><b>Figure 2.</b> OHDSI tools named in the 429 substantive threads. The CDM itself, Atlas, the standard vocabularies and Athena (the vocabulary download service) dominate; the back-end stack (WebAPI, HADES, Achilles, Broadsea, DatabaseConnector) forms a second tier. Programming languages are omitted.</figcaption></figure>

<div class="prose">
<p>Four things account for most of the stuck moments: the CDM specification itself (which table, which domain, which type concept), Atlas (cohort logic, concept sets, installation, authentication), the standard vocabularies (missing or wrong concepts), and Athena. The second tier is the deployment stack. Analysis packages are rare: PatientLevelPrediction and Strategus are named seven times each, CohortMethod and CohortDiagnostics fewer. People on the forum are, overwhelmingly, trying to build and keep a CDM, not yet to analyze one.</p>

<h2>3. A taxonomy of 29 needs</h2>
<p>Topic models over raw forum text are easy to run and hard to read; on this corpus one produced topics called \u201csymposium\u201d and \u201ccommunity calls.\u201d We took a different route. The coder wrote a one-sentence pain point for each thread that had one (392 sentences), and we clustered those sentences instead. Each cluster was then labeled, given a need statement grounded in its members, and scored.</p>
<p>The score, which we call the Unmet Need Index, is a weighted rank of five components: volume (0.35), unresolved share (0.25), mean severity (0.20), positive trend (0.10) and unresolved volume (0.10). It is deliberately simple and every component is published so a reader can re-weight it. Unresolved share is included because a question the community could not answer is a stronger signal of a gap than one it could, but we treat it with caution given the Teams limitation.</p>
</div>

<figure class="figure" id="fig3">{FIGS['f4']}<figcaption><b>Figure 3.</b> Twenty-nine bottom-up need clusters ranked by Unmet Need Index. Bar color shows the capability area the need maps to after discovery: data harmonization (12 clusters, 194 pain points), federated analytics (1 cluster, 18), or none, meaning tool bugs, installation, authentication, performance and community process (16 clusters, 177). Right-hand labels give thread count and the share not fully resolved on the forum.</figcaption></figure>

<div class="prose">
<p>Half of all pain points (194 of 389 clustered) fall into twelve harmonization clusters. Three of the top four needs are about getting data into OMOP. Merging the two vocabulary clusters, as the labeling review suggested, makes \u201cvocabulary content gaps and defects\u201d the single largest need at 55 threads. What follows is the technical substance of each group, drawn from the need statements and the threads behind them.</p>

<h3>3.1 Harmonization: getting data into OMOP without losing it</h3>
<p><b>Vocabulary gaps and defects (55 threads).</b> Source codes with no standard concept to map to: ICD-O-3 site, histology and behavior combinations from tumor registries, ATC vaccine classes, rare-disease codes, DRGs, compounded drugs. Where concepts exist they are sometimes wrong: duplicate TNM pathological M concepts with inconsistent classification, concepts deprecated without a replacement, NAACCR names truncated, pathology nodal groupings the vocabulary cannot express. Usagi, the mapping tool, cannot load a custom vocabulary for fuzzy matching, so a site that builds its own extension gets no tooling help with it.</p>
<blockquote>Several ICD-O-3 site/histology/behavior code combinations present in our source data do not exist.<cite>Tumor registry conversion, 2025.</cite></blockquote>
<p><b>Mapping complex source data (26).</b> Combination drugs where strength is known for the product but not per ingredient; clinical-trial instruments such as cognitive scales and randomization variables; compound survey concepts from a national specification; family history; radiotherapy. The guidance is unclear or absent and the mappings that exist lose granularity.</p>
<blockquote>I don\u2019t have information on how the total 55 mg dose is split between the two ingredients.<cite>Mapping a combination product to RxNorm ingredients discards strength.</cite></blockquote>
<p><b>Hierarchy-unreachable and overly broad mappings (7, but quantified).</b> Two threads measured the consequence of mapping defects rather than describing it. An ICD-10-CM code mapped to a sibling SNOMED concept that is not reachable through CONCEPT_ANCESTOR made 897 coded patients invisible to any hierarchy-based cohort. Another member compared hierarchy-generated ICD-10 code lists against manual enumeration for congenital heart disease and found 21,667 patients missing. These are the strongest arguments on the forum for mapping validation as a product feature rather than a review step.</p>
<p><b>CDM conventions (39 across two clusters).</b> Where to put derived age, pregnancy episodes, stillbirths, migration events, missed visits, patient-reported drugs without dates, dispensed versus prescribed records, observation-type visits, unmapped values and visit-level costs; how observation_period relates to visit_occurrence; what to do with records that have no observation period at all. The answers members receive conflict with one another. An opinionated, maintained conventions reference does not exist and would resolve a measurable share of this.</p>
<p><b>Oncology and genomics (32 across two clusters).</b> Disease status, imaging findings, biopsies, screening phases, regimens and first-course treatment do not fit the Episode table as currently specified; recording a procedure in several tables risks duplication. For genomics there is no production pattern at all: how to represent NGS and comprehensive genomic profiling results, germline versus somatic variants, specimen-level entities, and how to link variants to phenotypes at scale. The OMOP Genomic extension is described by its own call for input as having gaps.</p>
<blockquote>Most CDMs don\u2019t yet have genomic data.<cite>On the feasibility of Mendelian randomization across OMOP sites, 2026.</cite></blockquote>
<p><b>Lab domain assignment (14), drug class mapping (6), ETL pipelines (9), notes and NLP (6).</b> The boundary between Procedure, Measurement and Observation is ambiguous for tests without results, screening encounters and qualitative findings; LOINC answer relationships are incomplete. ATC to RxNorm relationships come in several inconsistent types and ingredient mapping drops dose. Reusable open-source ETL pipelines are missing for CPRD, OpenMRS and microbiology data, and the Synthea ETL exists only in R. Conventions for NOTE and NOTE_NLP, and for linking extracted mentions to clinical events, are unclear.</p>

<h3>3.2 Platform: keeping the stack running</h3>
<p>These needs carry the forum\u2019s highest severity. <b>Installing Atlas and WebAPI (10)</b>: Maven dependency resolution fails when the OHDSI Nexus repository is down, download links break, and documentation for current Linux distributions is thin. <b>Authentication and permissions (16 across two clusters)</b>: LDAP and Active Directory return \u201cBad credentials\u201d despite verified configuration; users authenticate but have no permissions despite assigned roles; SAML and Entra ID on Azure are undocumented or unsupported; errors are not logged. <b>Achilles at scale (10)</b>: a single analysis that runs in 18 seconds one day and over an hour the next, runs that time out past 20 hours on large tables, output tables that are silently not created, multi-threading that breaks. <b>Data Quality Dashboard on large data (15 across two clusters)</b>: a plausibility check that ran 40 hours without completing on a large measurement table, JVM memory settings that are ignored, a viewer that renders blank. <b>Back-end support (4)</b>: DatabaseConnector does not support Trino, Spark or Doris, which rules out platforms such as the UK Biobank research environment.</p>
<blockquote>Analysis 117 normally runs in 18 seconds but sometimes takes an hour or more.<cite>Achilles on PostgreSQL, 2025.</cite></blockquote>
<p>None of these are research problems. They are the daily experience of the people who would run any new platform, and they set the bar: anything that requires a comparable installation effort will be judged against the weeks it took to get Atlas working.</p>

<h3>3.3 Analytics tooling: expressing the question</h3>
<p><b>Complex cohort logic in Atlas (32).</b> Cohorts that need the Episode table, a pre-defined list of patient IDs, cohort start defined as the latest of several events, negation logic, or export of the definition as an R package for a regulatory submission. Atlas supports none of these directly, and its date and inclusion-rule behavior surprises experienced users. <b>Portable phenotypes and concept sets (20 across two clusters)</b>: Circe concept-set expressions support hierarchy but not lateral relationships; the Phenotype Library has to be downloaded by hand; published definitions are hard to reproduce outside OHDSI; vocabulary updates break existing concept sets, and there is no supported way to create thousands of them programmatically. <b>CDM compliance validation (13)</b>: no single authoritative, machine-readable source of truth for the CDM, so CSV validators, cdmInspection and the Data Quality Dashboard disagree or crash.</p>

<h2>4. The multi-site slice</h2>
<p>Forty-six substantive threads (11%) involved more than one institution, a network study, or data that could not leave a site. We flagged these conservatively: a thread had to describe multiple sites or partners, not merely use the word \u201cnetwork.\u201d</p>
</div>

<figure class="figure" id="fig4">{FIGS['f5']}<figcaption><b>Figure 4.</b> Each dot is one substantive thread involving more than one site, placed in the quarter it was posted. Filled dots were not fully resolved on the forum; hollow dots were. Multi-site questions arrived steadily across the two years.</figcaption></figure>

<div class="prose">
<p>Read together, the 35 multi-site threads with a stated pain point make one argument. Nobody asks how to run a study across sites. They ask how to trust the result when they do.</p>
<blockquote>When two sites report a cohort of heart failure patients, they may not mean the same thing.<cite>A call for collaborators on detecting cross-site semantic divergence, 2026.</cite></blockquote>
<blockquote>Any differences could reflect differences in how each dataset was mapped, undermining conclusions.<cite>On validating two independently converted OMOP datasets against each other.</cite></blockquote>
<blockquote>Sites map drugs to different levels of granularity \u2026 populate their quantity differently.<cite>On deriving a daily dose consistently across a network.</cite></blockquote>
<blockquote>I want to share the prediction results with external collaborators, I\u2019m not allowed to share patient level tables.<cite>On publishing a prediction model\u2019s outputs without the underlying data.</cite></blockquote>
<p>The technical asks fall into three groups.</p>
<ul>
<li><b>Comparability.</b> Detect when sites encode the same clinical concept differently; validate one site\u2019s conversion against another\u2019s; stratify cohort counts and characterization results by site, which Atlas cannot do; derive doses consistently when sites populate quantity differently; handle trial criteria that are observable at some sites and only proxied at others.</li>
<li><b>Sharing without moving patient data.</b> Prediction model outputs and aggregate results that collaborators can use without access to patient-level tables; phenotype definitions that travel with their implementation rather than \u201cburied in 200 lines of SQL with implicit assumptions.\u201d</li>
<li><b>Provenance and governance.</b> Tagging which registry or source a record came from when several share one CDM, so that data stewards \u201ccan check and verify the data they are supposed to have\u201d; understanding what staffing and capability a sustainable OMOP infrastructure requires.</li>
</ul>
<p>In two years exactly one thread reported a federated execution failing (a Korean FeederNet estimation run). Federated learning, as a request, does not appear. With a Teams corpus we would expect more execution questions, since that is where Strategus studies are coordinated; we would not expect the comparability theme to disappear, because it is a property of the data, not the venue.</p>

<h2>5. What this means</h2>
<h3>For OHDSI</h3>
<p>The vocabulary and convention questions repeat. Members ask the same thing about pregnancy episodes, patient-reported drugs without dates, lab domains and oncology episodes, and the answers they receive conflict. An opinionated conventions reference maintained alongside the CDM, and a mapping validator that reports hierarchy-unreachable codes, would address the two most quantified complaints on the forum. The genomic and oncology gaps are known to the relevant workgroups; the forum shows how many implementers are waiting on them.</p>
<h3>For industry</h3>
<p>Anyone building for this community should expect to be compared against an Atlas installation that took weeks and an LDAP integration that never worked. Deployment is table stakes. Beyond that, the data points to two things worth building and one thing not to claim.</p>
<ul>
<li><b>Build for harmonization at the level of the specific failure.</b> Dose preserved through combination-drug mapping, oncology and genomic concepts that exist, lab domains assigned consistently, and validation that flags hierarchy-unreachable codes before they silently drop patients from a cohort.</li>
<li><b>Build for cross-site comparability.</b> The federated need the forum expresses is \u201cprove the sites agree,\u201d not \u201crun the study.\u201d Detecting semantic divergence between sites, validating two conversions against each other, and site-stratified summaries are where federated analytics and harmonization meet.</li>
<li><b>Do not position federated learning as a response to OHDSI demand.</b> It is not in the record, and difficulty executing network studies is barely in it. The struggle is comparability and sharing.</li>
</ul>
<p>Our own interest is declared: Rhino Federated Computing builds harmonization and federated analytics tooling, and the Cancer AI Alliance work we support sits squarely in the oncology and genomics gaps the forum describes. That is a reason to be transparent about method, which is why every table behind these figures and the full coding schema are published with the report.</p>

<h2>Methods in brief</h2>
<div class="note">
<p><b>Corpus.</b> All public topics on forums.ohdsi.org created 1 Oct 2024 to 1 Oct 2026, collected 4 Oct 2026 through the Discourse JSON API at one request per 1.6 seconds. 776 topics, 2,164 posts, 334 distinct authors. Author handles replaced by salted hashes; emails and @-mentions scrubbed before any text left the machine. GitHub issues from OHDSI\u2019s 390 repositories were collected and excluded after a pilot showed 73% were maintainers\u2019 own task tracking.</p>
<p><b>Coding.</b> Each thread was reduced to a digest (title, opening post to 350 words, up to four replies) and coded by Claude Haiku 4.5 against a fixed schema in batches of 45, orchestrated through Claude Code. Fields: post type, lifecycle stage (multi-label), tools, pain point, job-to-be-done, severity, workaround present, resolution status, multi-site context, harmonization context, a verbatim evidence quote under 25 words, and confidence. 773 of 776 threads were coded; 429 were substantive (questions, bug reports, feature requests, discussions) and the rest announcements and event or job notices.</p>
<p><b>Reliability.</b> An 80-thread sample stratified by forum category was independently re-coded by Claude Sonnet 5.5, which did not see the first coder\u2019s output.</p>
</div>
</div>

<figure class="figure" id="fig5">{FIGS['f6']}<figcaption><b>Figure 5.</b> Agreement between the primary coder and an independent re-coder on 80 threads, as Cohen\u2019s \u03ba with percent agreement. Shaded bands follow the Landis and Koch convention. Lifecycle stage, a multi-label field, had a mean Jaccard overlap of 0.69 (not shown).</figcaption></figure>

<div class="prose">
<div class="note">
<p>Agreement was strong on the fields this post depends on: whether a thread contained a pain point (\u03ba 0.90), whether it concerned harmonization (0.77), post type (0.70) and severity (0.60). Resolution status was weak (0.36), with disagreement concentrated between \u201cpartially\u201d and \u201cresolved.\u201d We therefore anchored \u201cno reply\u201d on thread metadata (no post by anyone other than the author) and use the coder\u2019s judgment only for answered threads. Unresolved share enters the index with that definition.</p>
<p><b>Taxonomy.</b> 392 pain-point sentences were embedded (bge-small-en-v1.5) and clustered with Ward linkage into 30 clusters; three singletons were dropped. Clusters were labeled and mapped to a capability area with a written rationale by Claude Opus 5.5, then reviewed by the author. A BERTopic model over raw opening posts served as a cross-check and recovered the same major themes.</p>
<p><b>Scoring.</b> The Unmet Need Index is a weighted sum of rank-normalized volume (0.35), unresolved share (0.25), mean severity (0.20), positive quarterly trend (0.10) and unresolved volume (0.10).</p>
</div>

<h2>AI use, provenance and code</h2>
<div class="note">
<p><b>Date of analysis.</b> Data were collected and analyzed on 4 October 2026. The window covers topics created 1 October 2024 to 1 October 2026.</p>
<p><b>AI disclosure.</b> This study used large language models as instruments, and this post was drafted with one. Specifically: the collection, processing and analysis pipeline was written and run with Claude Code, using Claude Fable 5.1 (claude-fable-5-1) as the orchestrating model; the 773 threads were coded by Claude Haiku 4.5; the 80-thread reliability sample was independently re-coded by Claude Sonnet 5.5; the 29 need clusters were labeled, given need statements and mapped to capability areas by Claude Opus 5.5; the figures and the text of this post were drafted by Claude Fable 5.1 from the resulting tables. The author set the research questions, the coding schema, the scope decisions (including excluding GitHub issues), reviewed the cluster labels and capability mappings, and edited the text. Every quantitative claim in the post traces to a table in the repository; the model-generated labels and need statements are published alongside the metrics so readers can judge them.</p>
<p><b>Code and data.</b> The collector, the normalization and pseudonymization step, the coding schema and prompts, the clustering and scoring scripts, the figure generator for this post, the coded dataset (one row per thread, pseudonymized) and the needs taxonomy are at <a href="https://github.com/danieljfeller/ohdsi-community-signals">github.com/danieljfeller/ohdsi-community-signals</a>. Raw forum text is not redistributed; the collector reproduces it from the public API.</p>
</div>

<h2>Limitations</h2>
<ul>
<li><b>The Teams migration.</b> OHDSI workgroups and network studies are coordinated in Microsoft Teams, which is not public and was not available to us. The forum over-represents first-time and solo implementers and under-represents study coordinators and methodologists. Two consequences follow. Platform and harmonization needs are probably over-weighted relative to analysis and execution needs. And the forum\u2019s falling reply rates over the window reflect the venue losing its answerers to Teams at least as much as any change in the problems themselves, which is why this post does not interpret them.</li>
<li><b>Survivorship.</b> People who abandoned OHDSI tooling without posting leave no trace.</li>
<li><b>Machine coding.</b> The coder is a language model; its agreement with an independent coder is reported rather than assumed, and the weakest field was replaced with a metadata definition.</li>
<li><b>Small counts.</b> Many need clusters have fewer than ten threads. Rankings within the lower half of Figure 3 should be read as groups, not an order.</li>
</ul>

<p class="foot">Data and code: the coded dataset (one row per thread, pseudonymized), the 29-need taxonomy with metrics and rationales, all figure tables, the coding schema and the collection and analysis scripts are at <a href="https://github.com/danieljfeller/ohdsi-community-signals">github.com/danieljfeller/ohdsi-community-signals</a>. Quotes are reproduced verbatim, shortened to under 25 words, and unattributed; the forum is public, but the people on it did not post for a study. If one of the quotes is yours and you would prefer it removed, write to the author.</p>
</div>
</div>
"""
OUT.write_text(CSS + BODY)
print("wrote", OUT, OUT.stat().st_size, "bytes")
