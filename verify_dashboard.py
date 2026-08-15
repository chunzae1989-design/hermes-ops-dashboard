#!/usr/bin/env python3
"""Verify the generated Hermes Ops public dashboard contract."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
DATA = ROOT / "dashboard-data.json"
REQUIRED_IDS = {"overview", "agents", "recordings", "cron", "logs"}


def main() -> int:
    document = INDEX.read_text(encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    job_ids = [str(job.get("job_id") or job.get("id") or "") for job in jobs]
    row_count = len(re.findall(r"<tr class='(?:paused|ok|bad|idle)'>", document))
    rendered_ids = set(re.findall(r"id='([^']+)'", document))

    checks = {
        "theme": "data-theme='exception-first'" in document,
        "theme_css": "id=\"poc-variant\"" in document and "id=\"exception-first-production\"" in document,
        "runtime": "id=\"exception-first-runtime\"" in document,
        "selected_hero": "ACT /<br>NOW" in document,
        "legacy_style_removed": "--bg:#041C1C" not in document,
        "local_paths_removed": "/Users/na/" not in document,
        "poc_controls_absent": "poc-switcher" not in document,
        "job_row_count": row_count == len(jobs),
        "job_ids_present": all(html.escape(job_id, quote=True) in document for job_id in job_ids if job_id),
        "required_sections": REQUIRED_IDS <= rendered_ids,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"DASHBOARD_VERIFY_FAILED failed={failed} checks={checks}")
    print(
        "DASHBOARD_VERIFY_OK "
        f"jobs={len(jobs)} rows={row_count} required_ids={len(REQUIRED_IDS)} "
        "local_paths=0 theme=exception-first"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
