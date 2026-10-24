import json, sys, datetime
S = sys.argv[1]; log = sys.argv[2]
t = open(f"{S}/template.html").read()
rows = [json.loads(l) for l in open(log)] if __import__("os").path.exists(log) else []
seq, head = (rows[-1]["seq"], rows[-1]["head"]) if rows else (7, "df1f54cd847a7b08f4ab8b4f108a9306b651af77ae487f47d0b744d2561a2906")
tr = ""
for i, r in enumerate(rows):
    cls = ' class="final"' if i == len(rows) - 1 else ""
    k = r["key"]
    tr += (f'          <tr{cls}><td class="seq">{r["seq"]}</td><td class="ev">{"OOS_SELECTED ×17 (sealed)" if r["group"] == "SEL" else f"RESULTS ×{r['records']} · g{r['group']} {k[0].split('_')[0]} {k[1].split('_')[0]} {k[2]}"}</td>'
           f'<td class="h">{r["head"]}</td><td class="t">{r["utc"][:19].replace("T", " ")}</td></tr>\n')
out = (t.replace("{{ROWS}}", tr).replace("{{SEQ}}", str(seq)).replace("{{HEAD}}", head)
        .replace("{{OPENCLASS}}", "" if rows else ' class="final"')
        .replace("{{UPDATED}}", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")))
open(f"{S}/nexa-registry-checkpoints.html", "w").write(out)
print("page head:", seq, head[:12], "| batches:", len(rows))
