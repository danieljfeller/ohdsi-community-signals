"""Agreement between the primary coder (Haiku batches) and a stronger re-coder on the reliability sample."""
import json, glob
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
A = {json.loads(l)["thread_id"]: json.loads(l) for f in sorted(glob.glob(str(OUT / "coding_out" / "batch_*.jsonl"))) for l in open(f) if l.strip()}
B = {json.loads(l)["thread_id"]: json.loads(l) for l in open(OUT / "coding_reliability" / "recoded.jsonl") if l.strip()}
ids = [t for t in B if t in A]; print(f"paired threads: {len(ids)}")
rows = []
for field in ["post_type", "severity", "resolution_status", "multi_site_context", "harmonization_context", "workaround_present"]:
    a = [str(A[t].get(field)) for t in ids]; b = [str(B[t].get(field)) for t in ids]
    agree = sum(x == y for x, y in zip(a, b)) / len(ids); kappa = cohen_kappa_score(a, b)
    rows.append({"field": field, "percent_agreement": round(agree, 2), "cohen_kappa": round(kappa, 2)})
# pain point presence and lifecycle overlap
a = [A[t].get("pain_point") is not None for t in ids]; b = [B[t].get("pain_point") is not None for t in ids]
rows.append({"field": "pain_point_present", "percent_agreement": round(sum(x == y for x, y in zip(a, b)) / len(ids), 2), "cohen_kappa": round(cohen_kappa_score(a, b), 2)})
jac = []
for t in ids:
    sa, sb = set(A[t].get("lifecycle_stage") or []), set(B[t].get("lifecycle_stage") or [])
    jac.append(1.0 if not sa and not sb else len(sa & sb) / len(sa | sb))
rows.append({"field": "lifecycle_stage (mean Jaccard)", "percent_agreement": round(sum(jac) / len(jac), 2), "cohen_kappa": None})
R = pd.DataFrame(rows); R.to_csv(OUT / "coding_reliability" / "agreement.csv", index=False); print(R.to_string(index=False))
# disagreements on severity direction and resolution for inspection
dis = [(t, A[t].get("resolution_status"), B[t].get("resolution_status"), A[t].get("severity"), B[t].get("severity")) for t in ids
       if A[t].get("resolution_status") != B[t].get("resolution_status") or A[t].get("severity") != B[t].get("severity")]
pd.DataFrame(dis, columns=["thread_id", "res_A", "res_B", "sev_A", "sev_B"]).to_csv(OUT / "coding_reliability" / "disagreements.csv", index=False)
print(f"threads with severity/resolution disagreement: {len(dis)}")
