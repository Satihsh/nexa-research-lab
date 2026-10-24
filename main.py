from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
NEXA = ROOT / "workspace" / "nexa"
SOURCE = NEXA / "source"
INDEX = NEXA / "nexa_index.json"
DEBATES = NEXA / "debates"

ASTRA_MODEL = "openai/gpt-6-astra"
OPUS_MODEL = "anthropic/claude-opus-5.5"

# Hard local limits — deliberately conservative.
MAX_CONTEXT_CHARS = 2600
MAX_FILE_CHARS = 850
MAX_FILES = 2
MAX_OUTPUT_TOKENS = 150


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path):
    return path.read_text(encoding="utf-8", errors="ignore")


def retrieve(terms, max_files=MAX_FILES):
    """
    Local-only content retrieval.
    Searches filenames AND file contents.
    Never calls OpenRouter.
    """
    index = load_json(INDEX)
    candidates = []

    excluded = (
        "baseline_backup",
        "/baseline/",
        "/backups/",
        ".zip",
        ".tar",
        ".gz",
    )

    normalized_terms = [t.lower() for t in terms]

    for item in index["files"]:
        rel_path = item["path"]
        path_lower = rel_path.lower()

        if any(x in path_lower for x in excluded):
            continue

        path = SOURCE / rel_path

        if not path.is_file():
            continue

        try:
            content = load_text(path)
        except Exception:
            continue

        searchable = path_lower + "\n" + content.lower()

        score = 0
        for term in normalized_terms:
            if term in path_lower:
                score += 4
            elif term in searchable:
                score += 1

        if score:
            candidates.append((score, rel_path, content))

    candidates.sort(key=lambda x: (-x[0], x[1]))

    selected = []
    total = 0

    for _, rel_path, content in candidates:
        content = content[:MAX_FILE_CHARS]

        block = (
            f"\\n===== FILE: {rel_path} =====\\n"
            f"{content}\\n"
        )

        if total + len(block) > MAX_CONTEXT_CHARS:
            continue

        selected.append((rel_path, content))
        total += len(block)

        if len(selected) >= max_files:
            break

    return selected

def format_context(files):
    return "\n".join(
        f"===== FILE: {path} =====\n{content}\n"
        for path, content in files
    )


def get_client():
    key = os.environ.get("OPENROUTER_API_KEY")

    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
    )


def call_model(model, system, user):
    client = get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_completion_tokens=MAX_OUTPUT_TOKENS,
        temperature=0.2,
        extra_body={
            "usage": {
                "include": True
            }
        },
        extra_headers={
            "X-Title": "NEXA Autonomous Development Lab"
        },
    )

    return (
        response.choices[0].message.content,
        response.usage,
    )


def dry_run():
    terms = [
        "implementation",
        "integration",
        "defect",
        "risk",
        "validation",
        "nexa_ea",
        "trade_dna",
    ]

    files = retrieve(terms)
    context = format_context(files)

    mission_text = """
NEXA ENGINEERING MISSION

Design the highest-value next engineering step for the existing
NEXA autonomous MT5 trading system.

Preserve the existing validated architecture.

Do not:
- recreate NEXA from scratch
- fabricate evidence
- fabricate trading performance
- weaken hard risk controls
- claim tests passed unless evidence exists
- modify the live MT5 account

The final proposal must identify:
1. Existing relevant implementation
2. Deficiency or engineering opportunity
3. Exact proposed change
4. Files affected
5. Tests required
6. Acceptance criteria
7. Rollback strategy
8. Evidence still missing
"""

    astra_system = """
You are GPT-6 Astra, Principal Architect and Builder for NEXA.

Use only the supplied repository evidence.
Preserve validated work.
Do not invent implementation or evidence.

Produce a concrete engineering proposal.
"""

    astra_user = mission_text + "\n\nREPOSITORY EVIDENCE:\n" + context

    opus_system = """
You are Claude Opus 5.5, Independent Adversarial Co-Architect.

Do not rubber-stamp Astra.

Attack the proposal against the supplied evidence.

Check:
- MQL5 correctness
- architecture
- data leakage
- risk controls
- execution assumptions
- reproducibility
- validation
- missing evidence
"""

    opus_user = (
        mission_text
        + "\n\nREPOSITORY EVIDENCE:\n"
        + context
        + "\n\nASTRA PROPOSAL:\n"
        + "[ASTRA OUTPUT — generated after call 1]"
    )

    print("=" * 72)
    print("NEXA TRUE API PREFLIGHT")
    print("=" * 72)
    print(f"Files selected                 : {len(files)}")
    print(f"Repository context chars       : {len(context):,}")
    print(f"Astra user chars               : {len(astra_user):,}")
    print(f"Approx Astra input tokens      : {len(astra_system + astra_user) // 4:,}")
    print(f"Approx Opus input tokens       : {len(opus_system + opus_user) // 4:,}")
    print(f"Output ceiling/call            : {MAX_OUTPUT_TOKENS}")
    print(f"Planned model calls             : 3")
    print()
    print("NO OPENROUTER REQUEST MADE")
    print("TRUE PREFLIGHT COMPLETE")


def mission():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = DEBATES / timestamp
    out.mkdir(parents=True, exist_ok=True)

    terms = [
        "NEXA_BUILD_MANIFEST",
        "NEXA_COMPLETE_RESEARCH_MASTER",
        "NEXA_IMPLEMENTATION_PLAN",
        "NEXA_EA",
        "TradeDNA",
        "validation",
        "defect",
        "risk",
    ]

    files = retrieve(terms)
    context = format_context(files)

    if len(context) > MAX_CONTEXT_CHARS:
        raise RuntimeError("ABORT: context ceiling exceeded")

    mission_text = load_text(BASE_DIR / "prompts" / "astra_gap_audit.md")

    astra_system = """
You are GPT-6 Astra, Principal Architect and Builder for NEXA Autonomous Trading AI.

Perform a forensic gap audit using ONLY the supplied repository evidence.
Do not build or modify files.
Do not invent evidence.
Do not propose functionality that already exists.
Identify the single highest-value next task.
"""

    astra_user = mission_text + "\n\nREPOSITORY EVIDENCE:\n" + context

    print("=" * 72)
    print("NEXA GAP AUDIT — ASTRA")
    print("=" * 72)
    print(f"Files selected           : {len(files)}")
    print(f"Context chars            : {len(context):,}")
    print(f"Astra input chars        : {len(astra_user):,}")
    print("API calls planned        : 2")
    print()

    astra = call_model("openai/gpt-6-astra", astra_system, astra_user)

    if not astra:
        raise RuntimeError("Astra returned empty output")

    (out / "01_astra_gap_audit.md").write_text(astra)

    opus_system = """
You are Claude Opus 5.5, Independent Adversarial Co-Architect.

Audit Astra's gap analysis against the supplied repository evidence.

Do not rubber-stamp it.
Find:
- already-existing functionality Astra missed
- unsupported assumptions
- incorrect dependency ordering
- data leakage risks
- execution/model mismatch
- risk-control regressions
- missing validation evidence

Then state whether Astra's proposed NEXT TASK is actually justified.
If not, identify the evidence-supported correction.

Do not build or modify files.
"""

    opus_user = (
        "REPOSITORY EVIDENCE:\n"
        + context
        + "\n\nASTRA GAP AUDIT:\n"
        + astra
    )

    opus = call_model("anthropic/claude-opus-5.5", opus_system, opus_user)

    if not opus:
        (out / "02_opus_audit.md").write_text(
            "OPUS RETURNED EMPTY OUTPUT.\n"
        )
        print("Astra audit saved.")
        print("Opus returned empty output; no further action taken.")
        print(f"Debate directory: {out}")
        return

    (out / "02_opus_audit.md").write_text(opus)

    print("Astra audit saved.")
    print("Opus adversarial audit saved.")
    print(f"Debate directory: {out}")
    print()
    print("NO FILES MODIFIED.")
    print("NO MT5 CHANGES.")
    print("NO THIRD MODEL CALL.")


if __name__ == "__main__":
    mission()
