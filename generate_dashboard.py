#!/usr/bin/env python3
"""Generate a local Hermes operations dashboard HTML.

Reads Hermes cron/log/state files and writes a self-contained index.html.
"""
from __future__ import annotations

import html
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

HOME = Path('/Users/na')
PROJECT = HOME / 'HermesProjects' / 'hermes-ops-dashboard'
HERMES_HOME = HOME / '.hermes'
VAULT = HOME / 'obsidian' / 'nothumanbeing_vault'
RECORDINGS = HOME / 'Library' / 'CloudStorage' / 'SynologyDrive-RecordingsInbox'
JOBS_PATH = HERMES_HOME / 'cron' / 'jobs.json'
ERRORS = HERMES_HOME / 'logs' / 'errors.log'
CALL_STATE = HOME / 'HermesProjects' / 'recording_processing' / 'auto_state.json'
MEETING_STATE = HOME / 'HermesProjects' / 'meeting_recording_processing' / 'auto_state.json'
PENDING_CALL = HOME / 'HermesProjects' / 'recording_processing' / 'pending_gtasks.json'
PENDING_MEETING = HOME / 'HermesProjects' / 'meeting_recording_processing' / 'pending_meeting_gtasks.json'
CACHE_SCANNER = HERMES_HOME / 'scripts' / 'recording_local_cache_cleanup.py'


def run(cmd: list[str], timeout: int = 30) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout).strip()
    except Exception as e:
        return f'ERR: {type(e).__name__}: {e}'


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def count_recent_md(folder: Path, days: int = 7) -> int:
    if not folder.exists():
        return 0
    cutoff = datetime.now().timestamp() - days * 86400
    return sum(1 for p in folder.glob('*.md') if p.is_file() and p.stat().st_mtime >= cutoff)


def recent_errors(days: int = 7, limit: int = 10) -> list[str]:
    if not ERRORS.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    hits: list[str] = []
    for line in ERRORS.read_text(encoding='utf-8', errors='ignore').splitlines()[-1500:]:
        if not any(k in line for k in ['ERROR', 'Broken pipe', 'RuntimeError', 'InternalServerError', 'timeout', 'stale']):
            continue
        try:
            ts = datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S')
            if ts < cutoff:
                continue
        except Exception:
            pass
        hits.append(line[:240])
    return hits[-limit:]


def parse_cache_summary() -> dict[str, Any]:
    if not CACHE_SCANNER.exists():
        return {'available': False}
    out = run([str(CACHE_SCANNER), '--limit', '300', '--json'], timeout=180)
    try:
        d = json.loads(out)
        d['available'] = True
        # Public dashboard must not expose recording filenames/transcript paths.
        d.pop('items', None)
        return d
    except Exception:
        return {'available': False, 'raw': out[:500]}


def status_class(status: str | None) -> str:
    if status == 'ok':
        return 'ok'
    if status in (None, ''):
        return 'idle'
    return 'bad'


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def short_text(s: Any, limit: int = 96) -> str:
    text = ' '.join(str(s or '').split())
    return text if len(text) <= limit else text[: limit - 1] + '…'


def summarize_tasks(items: Any, source: str) -> dict[str, Any]:
    """Return only non-content task metadata for the public dashboard.

    Do not expose meeting/call transcript snippets, titles, source note names,
    evidence, or IDs on GitHub Pages.
    """
    if not isinstance(items, list):
        items = []
    status_counts: dict[str, int] = {}
    due_hint_counts: dict[str, int] = {}
    newest = ''
    for item in items:
        if not isinstance(item, dict):
            continue
        status = short_text(item.get('status') or 'pending', 32)
        due_hint = short_text(item.get('due_hint') or '기한 없음', 24)
        status_counts[status] = status_counts.get(status, 0) + 1
        due_hint_counts[due_hint] = due_hint_counts.get(due_hint, 0) + 1
        created = str(item.get('created_at') or '')
        if created > newest:
            newest = created
    return {
        'source': source,
        'count': len(items),
        'status_counts': status_counts,
        'due_hint_counts': due_hint_counts,
        'newest_created_at': newest or 'unknown',
    }


def public_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {'last_run_at': 'unknown', 'seen_count': 0, 'failed_count': 0}
    return {
        'last_run_at': state.get('last_run_at') or 'unknown',
        'seen_count': len(state.get('seen_keys') or state.get('seen_names') or []),
        'failed_count': len(state.get('failed_keys') or []),
        'transient_failure_count': len(state.get('transient_failures') or {}),
    }


def public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        'name': job.get('name'),
        'job_id': job.get('job_id') or job.get('id'),
        'enabled': job.get('enabled'),
        'last_status': job.get('last_status'),
        'last_error': job.get('last_error'),
        'next_run_at': job.get('next_run_at'),
    }


def find_job(jobs: list[dict[str, Any]], *needles: str) -> dict[str, Any]:
    lowered = [n.lower() for n in needles]
    for job in jobs:
        blob = json.dumps(job, ensure_ascii=False).lower()
        if all(n in blob for n in lowered):
            return job
    return {}


def collect() -> dict[str, Any]:
    jobs_root = load_json(JOBS_PATH, {'jobs': []})
    jobs = jobs_root.get('jobs', []) if isinstance(jobs_root, dict) else []
    active = [j for j in jobs if j.get('enabled')]
    failed = [j for j in active if j.get('last_status') not in (None, 'ok')]
    pending_call = load_json(PENDING_CALL, [])
    pending_meeting = load_json(PENDING_MEETING, [])
    task_summaries = [summarize_tasks(pending_call, '통화'), summarize_tasks(pending_meeting, '회의')]
    people_job = find_job(jobs, '피플팀', '브리핑') or find_job(jobs, 'daily insight')
    cache = parse_cache_summary()
    hermes_version_lines = run([str(HERMES_HOME / 'hermes-agent' / 'venv' / 'bin' / 'hermes'), '--version'], timeout=90).splitlines()
    call_state = public_state(load_json(CALL_STATE, {}))
    meeting_state = public_state(load_json(MEETING_STATE, {}))
    return {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'jobs': [public_job(j) for j in jobs],
        'active_jobs': len(active),
        'failed_jobs': len(failed),
        'errors': recent_errors(),
        'call_recent_notes': count_recent_md(VAULT / '30_통화녹음'),
        'meeting_recent_notes': count_recent_md(VAULT / '31_회의록'),
        'call_state': call_state,
        'meeting_state': meeting_state,
        'pending_call_tasks': len(pending_call),
        'pending_meeting_tasks': len(pending_meeting),
        'task_summaries': task_summaries,
        'people_briefing': {
            'name': people_job.get('name') or '평일 08시 피플팀 뉴스 브리핑',
            'enabled': people_job.get('enabled'),
            'last_status': people_job.get('last_status') or 'not yet',
            'last_run_at': people_job.get('last_run_at') or 'unknown',
            'last_error': people_job.get('last_error') or '',
            'next_run_at': people_job.get('next_run_at') or '-',
            'job_id': people_job.get('job_id') or people_job.get('id') or '',
        },
        'disk_line': run(['df', '-h', str(HOME)]).splitlines()[-1],
        'recordings_du': run(['du', '-sh', str(RECORDINGS)], timeout=90).split('\t')[0],
        'cache': cache,
        'hermes_version': hermes_version_lines[0] if hermes_version_lines else 'unknown',
        'hermes_update': ' / '.join([x for x in hermes_version_lines[1:] if 'Update available' in x or 'Project:' not in x][:3]),
    }


def render(data: dict[str, Any]) -> str:
    jobs = data['jobs']
    failed_jobs = [j for j in jobs if j.get('enabled') and j.get('last_status') not in (None, 'ok')]
    cache = data.get('cache', {})
    cache_bytes = int(cache.get('selected_bytes') or 0)
    cache_mb = cache_bytes / 1024 / 1024
    health = '주의 필요' if data['failed_jobs'] or data['errors'] else '정상'
    health_class = 'bad' if data['failed_jobs'] else 'ok'

    job_rows = []
    for j in jobs:
        enabled = j.get('enabled')
        st = j.get('last_status')
        cls = 'paused' if not enabled else status_class(st)
        job_rows.append(f"""
        <tr class='{cls}'>
          <td><span class='dot'></span>{esc(j.get('name'))}</td>
          <td><code>{esc(j.get('job_id') or j.get('id'))}</code></td>
          <td>{esc('on' if enabled else 'paused')}</td>
          <td>{esc(st or 'not yet')}</td>
          <td>{esc(j.get('next_run_at') or '-')}</td>
        </tr>""")

    errors_html = '\n'.join(f"<li><code>{esc(e)}</code></li>" for e in data['errors']) or '<li>최근 주요 에러 없음</li>'
    task_rows = []
    for t in data.get('task_summaries', []):
        status_text = ', '.join(f"{esc(k)} {v}" for k, v in t.get('status_counts', {}).items()) or '-'
        due_text = ', '.join(f"{esc(k)} {v}" for k, v in t.get('due_hint_counts', {}).items()) or '-'
        task_rows.append(f"""
        <tr>
          <td><span class='pill'>{esc(t['source'])}</span></td>
          <td><b>{esc(t['count'])}</b>개</td>
          <td>{status_text}</td>
          <td>{due_text}</td>
          <td><code>{esc(t.get('newest_created_at'))}</code></td>
        </tr>""")
    tasks_html = ''.join(task_rows) or "<tr><td colspan='5'>현재 Google Tasks 승인 후보 없음</td></tr>"
    people = data.get('people_briefing', {})
    people_status = people.get('last_status') or 'not yet'
    people_cls = status_class(people_status)
    failed_html = '\n'.join(
        f"<li><b>{esc(j.get('name'))}</b> <code>{esc(j.get('job_id') or j.get('id'))}</code> — {esc(j.get('last_status'))}: {esc(j.get('last_error') or '')}</li>"
        for j in failed_jobs
    ) or '<li>실패/주의 cron 없음</li>'

    html_doc = f"""<!doctype html>
<html lang='ko'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Hermes Ops Dashboard</title>
<style>
:root {{
  --bg: #0d1117;
  --panel: #151b23;
  --panel2: #0f1620;
  --text: #e6edf3;
  --muted: #8b949e;
  --line: #30363d;
  --blue: #58a6ff;
  --green: #3fb950;
  --red: #f85149;
  --yellow: #d29922;
  --purple: #bc8cff;
  --radius: 18px;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  min-height: 100vh;
  background: radial-gradient(circle at top left, rgba(88,166,255,.16), transparent 32%), var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', Segoe UI, sans-serif;
}}
main {{ max-width: 1180px; margin: 0 auto; padding: 32px 18px 56px; }}
header {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-end; margin-bottom:24px; }}
h1 {{ margin:0; font-size: clamp(28px, 4vw, 48px); letter-spacing:-.04em; }}
.sub {{ color: var(--muted); margin-top:8px; }}
.badge {{ border:1px solid var(--line); background:rgba(255,255,255,.04); padding:10px 14px; border-radius:999px; white-space:nowrap; }}
.badge.ok {{ color: var(--green); border-color: rgba(63,185,80,.38); }}
.badge.bad {{ color: var(--yellow); border-color: rgba(210,153,34,.45); }}
.grid {{ display:grid; grid-template-columns: repeat(12, 1fr); gap:14px; }}
.card {{
  grid-column: span 3;
  background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.02));
  border:1px solid var(--line);
  border-radius: var(--radius);
  padding:18px;
  box-shadow: 0 16px 45px rgba(0,0,0,.22);
}}
.card.wide {{ grid-column: span 6; }}
.card.full {{ grid-column: 1 / -1; }}
.label {{ color: var(--muted); font-size:13px; margin-bottom:12px; }}
.value {{ font-size:30px; font-weight:750; letter-spacing:-.03em; }}
.value.small {{ font-size:19px; line-height:1.35; }}
.kpi {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
.pill {{ font-size:12px; padding:5px 8px; border-radius:999px; border:1px solid var(--line); color:var(--muted); }}
.pill.ok {{ color: var(--green); border-color: rgba(63,185,80,.35); }}
.pill.bad {{ color: var(--red); border-color: rgba(248,81,73,.35); }}
.pill.warn {{ color: var(--yellow); border-color: rgba(210,153,34,.35); }}
section {{ margin-top:14px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
table.compact {{ font-size:12px; margin-top:12px; }}
th, td {{ padding:12px 10px; border-bottom:1px solid rgba(48,54,61,.75); text-align:left; vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; }}
tr.bad .dot {{ background: var(--red); }}
tr.ok .dot {{ background: var(--green); }}
tr.idle .dot {{ background: var(--yellow); }}
tr.paused {{ opacity:.55; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--muted); margin-right:8px; }}
code {{ color:#c9d1d9; background:rgba(110,118,129,.16); padding:2px 5px; border-radius:6px; }}
ul {{ margin:0; padding-left:20px; }}
li {{ margin:8px 0; color:#c9d1d9; }}
.footer {{ margin-top:22px; color:var(--muted); font-size:12px; }}
@media (max-width: 860px) {{
  header {{ display:block; }}
  .badge {{ display:inline-block; margin-top:14px; }}
  .card, .card.wide {{ grid-column: 1 / -1; }}
  table {{ font-size:12px; }}
  th:nth-child(5), td:nth-child(5) {{ display:none; }}
}}
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Hermes Ops Dashboard</h1>
      <div class='sub'>Mac mini 기반 AI 운영 현황 · generated {esc(data['generated_at'])}</div>
    </div>
    <div class='badge {health_class}'>상태: {health}</div>
  </header>

  <div class='grid'>
    <div class='card'><div class='label'>활성 cron</div><div class='kpi'><div class='value'>{data['active_jobs']}</div><span class='pill'>jobs</span></div></div>
    <div class='card'><div class='label'>실패/주의 cron</div><div class='kpi'><div class='value'>{data['failed_jobs']}</div><span class='pill {'bad' if data['failed_jobs'] else 'ok'}'>{'check' if data['failed_jobs'] else 'ok'}</span></div></div>
    <div class='card'><div class='label'>최근 7일 녹음 노트</div><div class='value'>{data['call_recent_notes']} <span style='color:var(--muted);font-size:18px'>통화</span></div><div class='sub'>{data['meeting_recent_notes']} 회의록</div></div>
    <div class='card'><div class='label'>Tasks 후보</div><div class='value'>{data['pending_call_tasks'] + data['pending_meeting_tasks']}</div><div class='sub'>통화 {data['pending_call_tasks']} · 회의 {data['pending_meeting_tasks']}</div></div>

    <div class='card wide'><div class='label'>Hermes</div><div class='value small'>{esc(data['hermes_version'])}</div><div class='sub'>{esc(data.get('hermes_update') or '업데이트 추가 메시지 없음')}</div></div>
    <div class='card wide'><div class='label'>Disk / Synology</div><div class='value small'>{esc(data['recordings_du'])} 녹음 캐시</div><div class='sub'>{esc(data['disk_line'])}</div></div>

    <div class='card wide'><div class='label'>녹음 처리 상태</div>
      <ul>
        <li>통화 마지막 실행: <code>{esc(data['call_state'].get('last_run_at', 'unknown'))}</code></li>
        <li>회의 마지막 실행: <code>{esc(data['meeting_state'].get('last_run_at', 'unknown'))}</code></li>
        <li>로컬 캐시 후보: <b>{esc(cache.get('finder_evictable_candidates', 'n/a'))}</b>개 · 약 <b>{cache_mb:.1f}MB</b></li>
      </ul>
    </div>
    <div class='card wide'><div class='label'>주의 항목</div><ul>{failed_html}</ul></div>

    <div class='card wide'><div class='label'>피플팀 브리핑 발송 상태</div>
      <div class='kpi'><div class='value small'>{esc(people.get('name'))}</div><span class='pill {people_cls}'>{esc(people_status)}</span></div>
      <ul>
        <li>마지막 실행: <code>{esc(people.get('last_run_at'))}</code></li>
        <li>다음 실행: <code>{esc(people.get('next_run_at'))}</code></li>
        <li>Job ID: <code>{esc(people.get('job_id'))}</code></li>
        <li>{'최근 오류: ' + esc(people.get('last_error')) if people.get('last_error') else '최근 오류 없음'}</li>
      </ul>
    </div>

    <div class='card wide'><div class='label'>Google Tasks 후보 요약</div>
      <div class='sub'>공개 페이지에는 회의/통화 원문, 제목, 인용문, 파일명은 올리지 않고 숫자/상태만 표시</div>
      <table class='compact'>
        <thead><tr><th>출처</th><th>후보 수</th><th>상태</th><th>기한 힌트</th><th>최근 생성</th></tr></thead>
        <tbody>{tasks_html}</tbody>
      </table>
    </div>

    <div class='card full'>
      <div class='label'>Cron Jobs</div>
      <table>
        <thead><tr><th>이름</th><th>ID</th><th>상태</th><th>마지막 결과</th><th>다음 실행</th></tr></thead>
        <tbody>{''.join(job_rows)}</tbody>
      </table>
    </div>

    <div class='card full'>
      <div class='label'>최근 에러 로그</div>
      <ul>{errors_html}</ul>
    </div>
  </div>
  <div class='footer'>Source: ~/.hermes/cron/jobs.json, errors.log, recording processing state, Obsidian notes. 원본 삭제 명령은 포함하지 않음.</div>
</main>
</body>
</html>"""
    return html_doc


def main() -> int:
    PROJECT.mkdir(parents=True, exist_ok=True)
    data = collect()
    (PROJECT / 'dashboard-data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (PROJECT / 'index.html').write_text(render(data), encoding='utf-8')
    print(PROJECT / 'index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
