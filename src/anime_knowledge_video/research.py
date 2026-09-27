"""Curated source packs. Unknown topics require supplied and reviewed claims."""

import json
from pathlib import Path

from .contracts import GateError
from .io import ROOT, write_json, write_text


def load_pack(topic_id: str, custom_pack: str | None = None) -> dict:
    path = Path(custom_pack) if custom_pack else ROOT / "examples" / f"{topic_id}.json"
    if not path.is_file():
        raise GateError("No source pack for this topic. Supply --research-pack with cited claims; automatic research provider is not configured.")
    pack = json.loads(path.read_text(encoding="utf-8"))
    claims = pack.get("claims", [])
    if not claims:
        raise GateError("source pack has no claims")
    for claim in claims:
        for field in ("claim", "type", "source", "source_url", "confidence", "caveat", "visual_implication"):
            if not claim.get(field):
                raise GateError(f"claim missing {field}")
        if not claim["source_url"].startswith("https://"):
            raise GateError("claim source must use an HTTPS URL")
    return pack


def save_research(pack: dict, project: Path) -> None:
    folder = project / "research"
    write_json(folder / "claims.json", pack["claims"])
    sources = [f"- [{c['source']}]({c['source_url']}) — {c['claim']}" for c in pack["claims"]]
    write_text(folder / "sources.md", "# Sources\n\n" + "\n".join(sources))
    status = "CURATED EXAMPLE — verify links and claims again before public factual release"
    write_text(folder / "factcheck_report.md", f"# Fact check\n\nStatus: {status}\n\nThis pack is not an automated live-source verification.\n")

