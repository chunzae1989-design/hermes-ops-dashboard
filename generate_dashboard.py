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
PORTFOLIO_JSON = HOME / 'HermesProjects' / 'finance-manager' / 'portfolio.json'
CRON_OUTPUT = HERMES_HOME / 'cron' / 'output'
HISTORY_JSON = PROJECT / 'ops-history.json'
MULTIAGENT_OPS = HOME / 'HermesProjects' / 'hermes-multiagent-ops'
AGY_CLI = HOME / '.local' / 'bin' / 'agy'


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


def pct(n: float, d: float) -> float:
    return round((n / d * 100.0), 1) if d else 0.0


def format_krw(v: Any) -> str:
    try:
        n = float(v or 0)
    except Exception:
        return '0원'
    if n >= 100_000_000:
        return f'{n / 100_000_000:.1f}억 원'
    if n >= 10_000:
        return f'{n / 10_000:.0f}만 원'
    return f'{n:.0f}원'


def count_recent_files(folder: Path, days: int = 7) -> int:
    if not folder.exists():
        return 0
    cutoff = datetime.now().timestamp() - days * 86400
    return sum(1 for p in folder.glob('*') if p.is_file() and p.stat().st_mtime >= cutoff)


def compact_time(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime('%m/%d %H:%M')
    except Exception:
        return ts[:16] if ts else '-'


def signed_delta(now: Any, prev: Any, suffix: str = '') -> tuple[str, str]:
    if now is None or prev is None:
        return '-', 'flat'
    try:
        delta = float(now) - float(prev)
    except Exception:
        return '-', 'flat'
    if abs(delta) < 0.05:
        return f'±0{suffix}', 'flat'
    cls = 'up' if delta > 0 else 'down'
    sign = '+' if delta > 0 else ''
    value = f'{delta:.1f}'.rstrip('0').rstrip('.')
    return f'{sign}{value}{suffix}', cls


def update_history(data: dict[str, Any], limit: int = 30) -> dict[str, Any]:
    """Persist compact, public-safe dashboard metrics for trend display."""
    bm = data.get('benchmarks', {})
    ai = bm.get('ai_ops', {})
    conv = bm.get('task_conversion', {})
    roi = bm.get('roi', {})
    point = {
        'ts': data.get('generated_at') or datetime.now().isoformat(timespec='seconds'),
        'score': ai.get('score', 0),
        'cron_success_rate_pct': ai.get('cron_success_rate_pct', 0),
        'attention_jobs': ai.get('attention_jobs', 0),
        'recent_error_lines': ai.get('recent_error_lines', 0),
        'cron_runs_7d': ai.get('cron_runs_7d', 0),
        'task_candidates': conv.get('task_candidates', 0),
        'roi_hours_7d': roi.get('estimated_hours_saved_7d', 0),
    }
    history = load_json(HISTORY_JSON, [])
    if not isinstance(history, list):
        history = []
    history = [h for h in history if isinstance(h, dict)]
    if not history or any(point.get(k) != history[-1].get(k) for k in point if k != 'ts'):
        history.append(point)
    else:
        history[-1]['ts'] = point['ts']
    history = history[-limit:]
    HISTORY_JSON.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')

    prev = history[-2] if len(history) >= 2 else None
    return {
        'history': history,
        'latest': history[-1] if history else point,
        'previous': prev,
        'score_delta': signed_delta(point.get('score'), prev.get('score') if prev else None),
        'success_delta': signed_delta(point.get('cron_success_rate_pct'), prev.get('cron_success_rate_pct') if prev else None, '%p'),
        'attention_delta': signed_delta(point.get('attention_jobs'), prev.get('attention_jobs') if prev else None),
        'error_delta': signed_delta(point.get('recent_error_lines'), prev.get('recent_error_lines') if prev else None),
    }


def collect_multi_agent_status(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    """Return public-safe status for the 헤르미온느 + specialist workers setup."""
    agents_md = MULTIAGENT_OPS / 'AGENTS.md'
    prompt_md = MULTIAGENT_OPS / 'research_worker_prompt.md'
    audit_md = MULTIAGENT_OPS / 'token_audit_2026-06-04.md'
    diji_dir = MULTIAGENT_OPS / 'agents' / 'diji'
    diji_role = diji_dir / 'AGENTS.md'
    diji_prompt = diji_dir / 'diji_prompt_template.md'
    diji_style = diji_dir / 'style_bible.md'
    diji_growth = diji_dir / 'design_growth_loop.md'
    text = agents_md.read_text(encoding='utf-8', errors='ignore') if agents_md.exists() else ''
    people_job = find_job(jobs, '피플팀', '브리핑') or find_job(jobs, 'daily insight')
    research_routes = sum(1 for marker in ['External-source research', 'Market/tool/vendor comparison', 'Drafting a first-pass summary'] if marker in text)
    design_routes = sum(1 for marker in ['PPT/deck planning', 'Photo/image critique', 'Visual design for dashboards', 'Selecting visual systems'] if marker in text)
    priority_jobs = [
        {'job_id': '7d884cf4f2dd', 'name': '피플팀 뉴스 브리핑', 'priority': 1},
        {'job_id': '5eb8a9449c5f', 'name': '회의녹음 회의록 정리', 'priority': 2},
        {'job_id': '6b91a9914c2e', 'name': 'Hermes 스킬 코너', 'priority': 3},
    ]
    return {
        'enabled': agents_md.exists() and prompt_md.exists(),
        'chief_agent': '헤르미온느',
        'workers': [
            {
                'name': '아기',
                'type': 'research',
                'cli': 'agy',
                'available': AGY_CLI.exists(),
                'role_manual': agents_md.name if agents_md.exists() else 'missing',
                'prompt_template': prompt_md.name if prompt_md.exists() else 'missing',
                'routes_defined': research_routes,
                'rule': '리서치 1차 수집/초안',
            },
            {
                'name': '디지',
                'type': 'design',
                'cli': 'Hermes delegated design context',
                'available': diji_role.exists() and diji_prompt.exists() and diji_style.exists(),
                'role_manual': 'agents/diji/AGENTS.md' if diji_role.exists() else 'missing',
                'prompt_template': 'agents/diji/diji_prompt_template.md' if diji_prompt.exists() else 'missing',
                'style_bible': 'agents/diji/style_bible.md' if diji_style.exists() else 'missing',
                'growth_loop': 'agents/diji/design_growth_loop.md' if diji_growth.exists() else 'missing',
                'routes_defined': design_routes,
                'rule': 'PPT·사진·디자인 방향성·시각 QA',
            },
        ],
        'worker_name': '아기',  # kept for backward-compatible dashboard-data consumers
        'worker_cli': 'agy',
        'agy_available': AGY_CLI.exists(),
        'design_agent_name': '디지',
        'design_agent_available': diji_role.exists() and diji_prompt.exists() and diji_style.exists(),
        'role_manual': agents_md.name if agents_md.exists() else 'missing',
        'prompt_template': prompt_md.name if prompt_md.exists() else 'missing',
        'token_audit': audit_md.name if audit_md.exists() else 'missing',
        'research_routes_defined': research_routes,
        'design_routes_defined': design_routes,
        'refactor_priority_jobs': priority_jobs,
        'highest_token_job_id': people_job.get('job_id') or people_job.get('id') or '7d884cf4f2dd',
        'highest_token_job_status': people_job.get('last_status') or 'not yet',
        'operating_rule': '리서치는 아기, 디자인은 디지, 검증·side effect·최종 전달은 헤르미온느',
    }


def collect_portfolio_benchmark() -> dict[str, Any]:
    p = load_json(PORTFOLIO_JSON, {})
    holdings = p.get('holdings', []) if isinstance(p, dict) else []
    rows = []
    total = 0.0
    cash = 0.0
    profit_known = 0.0
    for h in holdings:
        if not isinstance(h, dict):
            continue
        value = float(h.get('value_krw') or 0)
        total += value
        if h.get('ticker') == 'CASH':
            cash += value
        profit = h.get('profit_krw')
        if isinstance(profit, (int, float)):
            profit_known += float(profit)
        rows.append({'name': h.get('name') or h.get('ticker'), 'ticker': h.get('ticker'), 'value_krw': value})
    top = max(rows, key=lambda x: x['value_krw'], default={'name': '-', 'ticker': '-', 'value_krw': 0})
    return {
        'total_value_krw': round(total),
        'cash_weight_pct': pct(cash, total),
        'known_profit_krw': round(profit_known),
        'top_holding': f"{top.get('name')} ({top.get('ticker')})",
        'top_weight_pct': pct(float(top.get('value_krw') or 0), total),
        'benchmarks': ['NASDAQ', 'S&P500', 'SOXX', 'KOSPI', 'USD/KRW'],
        'last_briefing_outputs_7d': count_recent_files(CRON_OUTPUT / '4ea6aab46e6d', 7),
    }


def collect_benchmarks(jobs: list[dict[str, Any]], active: list[dict[str, Any]], failed: list[dict[str, Any]], errors: list[str], pending_call: Any, pending_meeting: Any, call_notes: int, meeting_notes: int, people_job: dict[str, Any], call_state: dict[str, Any], meeting_state: dict[str, Any]) -> dict[str, Any]:
    ok_active = [j for j in active if j.get('last_status') == 'ok']
    total_candidates = (len(pending_call) if isinstance(pending_call, list) else 0) + (len(pending_meeting) if isinstance(pending_meeting, list) else 0)
    total_notes = call_notes + meeting_notes
    recording_runs_7d = count_recent_files(CRON_OUTPUT / 'c1ac367cdb01', 7) + count_recent_files(CRON_OUTPUT / '5eb8a9449c5f', 7)
    cron_runs_7d = sum(count_recent_files(CRON_OUTPUT / str(j.get('id') or j.get('job_id')), 7) for j in jobs)
    auto_items = call_notes + meeting_notes + total_candidates + cron_runs_7d
    minutes_saved = round(call_notes * 8 + meeting_notes * 20 + total_candidates * 1.5 + cron_runs_7d * 3)
    ops_score = max(0, round(100 - (len(failed) / max(len(active), 1) * 45) - min(len(errors), 10) * 2))
    return {
        'ai_ops': {
            'score': ops_score,
            'active_jobs': len(active),
            'ok_active_jobs': len(ok_active),
            'cron_success_rate_pct': pct(len(ok_active), len(active)),
            'attention_jobs': len(failed),
            'recent_error_lines': len(errors),
            'cron_runs_7d': cron_runs_7d,
        },
        'task_conversion': {
            'recording_notes_7d': total_notes,
            'task_candidates': total_candidates,
            'candidate_rate_pct': pct(total_candidates, total_notes),
            'call_pipeline_seen': call_state.get('seen_count', 0),
            'meeting_pipeline_seen': meeting_state.get('seen_count', 0),
        },
        'daily_insight': {
            'job_status': people_job.get('last_status') or 'not yet',
            'last_run_at': people_job.get('last_run_at') or 'unknown',
            'next_run_at': people_job.get('next_run_at') or '-',
            'last_error_present': bool(people_job.get('last_error')),
            'delivery_reliability': '주의' if people_job.get('last_status') not in (None, 'ok') else '정상',
        },
        'portfolio': collect_portfolio_benchmark(),
        'roi': {
            'auto_items_7d': auto_items,
            'estimated_minutes_saved_7d': minutes_saved,
            'estimated_hours_saved_7d': round(minutes_saved / 60, 1),
            'recording_runs_7d': recording_runs_7d,
            'model': '통화노트 8분·회의록 20분·후보 1.5분·cron 3분 절감 가정',
        },
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
    call_notes = count_recent_md(VAULT / '30_통화녹음')
    meeting_notes = count_recent_md(VAULT / '31_회의록')
    errors = recent_errors()
    benchmarks = collect_benchmarks(jobs, active, failed, errors, pending_call, pending_meeting, call_notes, meeting_notes, people_job, call_state, meeting_state)
    multi_agent = collect_multi_agent_status(jobs)
    return {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'jobs': [public_job(j) for j in jobs],
        'active_jobs': len(active),
        'failed_jobs': len(failed),
        'errors': errors,
        'benchmarks': benchmarks,
        'multi_agent': multi_agent,
        'call_recent_notes': call_notes,
        'meeting_recent_notes': meeting_notes,
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
    """Render a public-safe Hermes teal command-center dashboard.

    The layout intentionally follows DESIGN.md rather than the earlier
    GitHub-dark card grid: fixed icon rail, mission panel, editorial hero,
    dense telemetry ribbon, dispatch board, terminal/log motifs.
    """
    jobs = data['jobs']
    failed_jobs = [j for j in jobs if j.get('enabled') and j.get('last_status') not in (None, 'ok')]
    cache = data.get('cache', {})
    cache_bytes = int(cache.get('selected_bytes') or 0)
    cache_mb = cache_bytes / 1024 / 1024
    health = '주의 필요' if data['failed_jobs'] or data['errors'] else '정상'
    health_class = 'bad' if (data['failed_jobs'] or data['errors']) else 'ok'

    bm = data.get('benchmarks', {})
    ai = bm.get('ai_ops', {})
    conv = bm.get('task_conversion', {})
    di = bm.get('daily_insight', {})
    pf = bm.get('portfolio', {})
    roi = bm.get('roi', {})
    ma = data.get('multi_agent', {})
    people = data.get('people_briefing', {})
    people_status = people.get('last_status') or 'not yet'
    people_cls = status_class(people_status)
    trend = data.get('trend', {})
    history = trend.get('history', [])[-8:]
    score_delta_text, score_delta_cls = trend.get('score_delta', ('-', 'flat'))
    success_delta_text, success_delta_cls = trend.get('success_delta', ('-', 'flat'))
    attention_delta_text, attention_delta_raw_cls = trend.get('attention_delta', ('-', 'flat'))
    error_delta_text, error_delta_raw_cls = trend.get('error_delta', ('-', 'flat'))
    attention_delta_cls = 'up' if attention_delta_raw_cls == 'down' else 'down' if attention_delta_raw_cls == 'up' else 'flat'
    error_delta_cls = 'up' if error_delta_raw_cls == 'down' else 'down' if error_delta_raw_cls == 'up' else 'flat'

    score_bars = ''.join(
        f"<i title='{esc(compact_time(h.get('ts', '')))} · {esc(h.get('score', 0))}점' style='height:{max(8, min(100, float(h.get('score') or 0)))}%'></i>"
        for h in trend.get('history', [])[-12:]
    ) or "<i style='height:50%'></i>"

    def job_category(job: dict[str, Any]) -> str:
        blob = f"{job.get('name', '')} {job.get('job_id', '')}".lower()
        if any(x in blob for x in ['피플', 'insight', '브리핑', '스킬']):
            return 'Insights'
        if any(x in blob for x in ['녹음', '회의', '통화']):
            return 'Recordings'
        if any(x in blob for x in ['포트폴리오', 'finance', '국내장']):
            return 'Finance'
        if any(x in blob for x in ['update', 'dashboard', '주간 운영']):
            return 'Maintenance'
        return 'Ops'

    def safe_job_name(job: dict[str, Any]) -> str:
        # Cron labels are operational labels, but keep them compact and category-like.
        return short_text(job.get('name') or job_category(job), 44)

    job_rows = []
    for idx, j in enumerate(jobs, 1):
        enabled = j.get('enabled')
        st = j.get('last_status')
        cls = 'paused' if not enabled else status_class(st)
        job_rows.append(f"""
        <tr class='{cls}'>
          <td><span class='led'></span><span class='row-index'>{idx:02d}</span></td>
          <td><b>{esc(job_category(j))}</b><small>{esc(safe_job_name(j))}</small></td>
          <td><code>{esc(j.get('job_id') or j.get('id'))}</code></td>
          <td>{esc('on' if enabled else 'paused')}</td>
          <td><span class='state-chip {cls}'>{esc(st or 'not yet')}</span></td>
          <td><code>{esc(j.get('next_run_at') or '-')}</code></td>
        </tr>""")

    def error_bucket(line: str) -> str:
        lowered = line.lower()
        if 'context summary' in lowered or 'compressor' in lowered:
            return 'context_compressor_timeout'
        if 'internalservererror' in lowered or 'api call failed' in lowered:
            return 'provider_api_retry'
        if 'telegram' in lowered or 'get_updates' in lowered:
            return 'gateway_polling_warning'
        if 'broken pipe' in lowered:
            return 'broken_pipe'
        if 'timeout' in lowered:
            return 'timeout'
        return 'runtime_warning'

    error_counts: dict[str, int] = {}
    for e in data.get('errors', []):
        bucket = error_bucket(str(e))
        error_counts[bucket] = error_counts.get(bucket, 0) + 1
    error_summary_html = ''.join(
        f"<li><span>{esc(k)}</span><b>{v}</b></li>" for k, v in sorted(error_counts.items())
    ) or '<li><span>no_recent_major_errors</span><b>0</b></li>'

    task_rows = []
    for t in data.get('task_summaries', []):
        status_text = ', '.join(f"{esc(k)} {v}" for k, v in t.get('status_counts', {}).items()) or '-'
        due_text = ', '.join(f"{esc(k)} {v}" for k, v in t.get('due_hint_counts', {}).items()) or '-'
        task_rows.append(f"""
        <tr>
          <td><span class='state-chip neutral'>{esc(t['source'])}</span></td>
          <td><b>{esc(t['count'])}</b>개</td>
          <td>{status_text}</td>
          <td>{due_text}</td>
          <td><code>{esc(t.get('newest_created_at'))}</code></td>
        </tr>""")
    tasks_html = ''.join(task_rows) or "<tr><td colspan='5'>현재 Google Tasks 승인 후보 없음</td></tr>"

    multi_workers_html = ''.join(
        f"""
        <div class='agent-node {'ready' if w.get('available') else 'warn'}'>
          <span class='node-label'>{esc(w.get('type'))}</span>
          <b>{esc(w.get('name'))}</b>
          <small>{esc(w.get('rule'))}</small>
          <code>routes={esc(w.get('routes_defined', 0))}</code>
        </div>"""
        for w in ma.get('workers', [])
    ) or '<div class="agent-node warn"><b>worker 없음</b></div>'

    failed_html = ''.join(
        f"<li><span>{esc(job_category(j))}</span><b>{esc(short_text(j.get('last_status') or 'check', 24))}</b></li>"
        for j in failed_jobs
    )

    html_doc = f"""<!doctype html>
<html lang='ko'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Hermes Ops Dashboard</title>
<style>
:root {{
  --bg:#041C1C; --cream:#FFE6CB; --warm:#FFBD38; --green:#34D399; --cyan:#6EE7F9; --red:#FB7185; --purple:#C4B5FD;
  --terminal:#020808; --card:#102928; --card2:#203734; --rail:#0A2222; --border:#35514D;
  --muted:rgba(255,230,203,.62); --subtle:rgba(255,230,203,.42); --line:rgba(255,230,203,.16); --line2:rgba(255,230,203,.30);
  --font-sans:system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic','Segoe UI',sans-serif;
  --font-mono:ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,monospace;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;min-height:100vh;color:var(--cream);font-family:var(--font-sans);background:radial-gradient(circle at 0% 0%,rgba(255,189,56,.18),transparent 34%),radial-gradient(circle at 86% 12%,rgba(52,211,153,.13),transparent 30%),radial-gradient(circle at 50% 115%,rgba(110,231,249,.09),transparent 38%),var(--bg);}}
body:before{{content:'';position:fixed;inset:0;pointer-events:none;opacity:.16;mix-blend-mode:screen;background:linear-gradient(rgba(255,230,203,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(255,230,203,.055) 1px,transparent 1px);background-size:52px 52px;mask-image:radial-gradient(circle at top,#000 0%,transparent 74%);z-index:0}}
body:after{{content:'';position:fixed;inset:0;pointer-events:none;opacity:.10;background:repeating-conic-gradient(currentColor 0% 25%,transparent 0% 50%) 0 0/3px 3px;color:var(--cream);z-index:1}}
.shell{{position:relative;z-index:2;display:grid;grid-template-columns:88px 292px minmax(0,1fr);min-height:100vh}}
.rail{{position:sticky;top:0;height:100vh;background:linear-gradient(180deg,rgba(10,34,34,.92),rgba(4,28,28,.74));border-right:1px solid var(--line);padding:16px 12px;display:flex;flex-direction:column;align-items:center;gap:16px}}
.mark{{width:48px;height:48px;border-radius:16px;background:radial-gradient(circle at 35% 18%,#fff7ed,var(--cream) 52%,var(--warm));color:var(--bg);display:grid;place-items:center;font-weight:950;box-shadow:0 0 44px rgba(255,230,203,.24)}}
.rail-nav{{display:grid;gap:10px;margin-top:18px;width:100%}}
.rail-nav a{{height:48px;border:1px solid transparent;border-radius:16px;display:grid;place-items:center;color:var(--muted);text-decoration:none;font-family:var(--font-mono);font-weight:800}}
.rail-nav a:hover,.rail-nav a.active{{background:rgba(255,230,203,.08);border-color:var(--line);color:var(--cream)}}
.rail-status{{margin-top:auto;width:38px;height:38px;border-radius:50%;border:1px solid {'rgba(255,189,56,.55)' if health_class == 'bad' else 'rgba(52,211,153,.55)'};background:{'rgba(255,189,56,.10)' if health_class == 'bad' else 'rgba(52,211,153,.10)'};box-shadow:0 0 30px {'rgba(255,189,56,.22)' if health_class == 'bad' else 'rgba(52,211,153,.22)'};}}
.mission{{position:sticky;top:0;height:100vh;padding:16px;border-right:1px solid var(--line);background:rgba(4,28,28,.55);backdrop-filter:blur(22px)}}
.mission-card{{height:calc(100vh - 32px);border:1px solid var(--line);border-radius:24px;background:linear-gradient(180deg,rgba(255,230,203,.08),rgba(255,230,203,.025));padding:22px;display:flex;flex-direction:column;gap:18px;box-shadow:0 24px 80px rgba(0,0,0,.22)}}
.brand-title{{font-size:34px;line-height:.9;letter-spacing:-.07em;font-weight:950}}
.brand-kicker,.label{{font-family:var(--font-mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--subtle);font-weight:750}}
.mission-note{{border:1px solid var(--line);border-radius:18px;background:rgba(255,230,203,.05);padding:14px;color:var(--muted);line-height:1.5;font-size:13px}}
.meta-stack{{display:grid;gap:10px;margin-top:auto}}
.meta-row{{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid var(--line);padding-bottom:8px;color:var(--muted);font-size:13px}}
.meta-row b{{color:var(--cream);font-family:var(--font-mono);font-size:12px;text-align:right}}
main{{min-width:0;padding:22px;max-width:1480px;width:100%;margin:0 auto}}
.topline{{display:flex;justify-content:space-between;gap:16px;color:var(--subtle);font-size:12px;font-family:var(--font-mono);margin-bottom:14px}}
.hero{{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:34px;min-height:330px;padding:34px;background:linear-gradient(135deg,rgba(255,230,203,.12),rgba(255,230,203,.035) 45%,rgba(52,211,153,.08)),var(--card);box-shadow:0 24px 80px rgba(0,0,0,.28)}}
.hero:after{{content:'';position:absolute;right:-90px;top:-100px;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle,rgba(255,189,56,.28),transparent 64%)}}
.hero-grid{{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:28px;align-items:end;height:100%}}
h1{{margin:0;font-size:clamp(62px,10vw,132px);line-height:.82;letter-spacing:-.085em;font-weight:950;font-stretch:condensed}}
.hero-sub{{margin-top:18px;color:var(--muted);font-size:16px;line-height:1.55;max-width:760px}}
.command{{font-family:var(--font-mono);font-size:12px;color:var(--green);background:var(--terminal);border:1px solid var(--line);border-radius:14px;padding:12px;margin-top:18px;display:inline-block}}
.status-dial{{border:1px solid var(--line2);border-radius:28px;background:rgba(2,8,8,.54);padding:22px;min-height:210px;display:flex;flex-direction:column;justify-content:space-between}}
.dial-value{{font-size:76px;line-height:.82;letter-spacing:-.08em;font-weight:950}}
.state-chip{{font-family:var(--font-mono);font-size:11px;letter-spacing:.08em;border:1px solid var(--line);border-radius:999px;padding:5px 8px;color:var(--muted);display:inline-flex;align-items:center;gap:6px;width:max-content;background:rgba(255,230,203,.04)}}
.state-chip.ok,.state-chip.ready{{color:var(--green);border-color:rgba(52,211,153,.38);background:rgba(52,211,153,.08)}}
.state-chip.bad,.state-chip.warn{{color:var(--warm);border-color:rgba(255,189,56,.42);background:rgba(255,189,56,.08)}}
.state-chip.paused{{opacity:.55}} .state-chip.neutral{{color:var(--cream)}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin-top:14px}}
.tile,.panel{{position:relative;overflow:hidden;border:1px solid var(--line);background:linear-gradient(180deg,rgba(255,230,203,.075),rgba(255,230,203,.025));border-radius:22px;padding:16px;box-shadow:0 12px 36px rgba(0,0,0,.18)}}
.tile:before,.panel:before{{content:'';position:absolute;inset:0 0 auto;height:1px;background:linear-gradient(90deg,transparent,rgba(255,230,203,.34),transparent)}}
.tile{{grid-column:span 2;min-height:126px;display:flex;flex-direction:column;justify-content:space-between}}
.tile.wide{{grid-column:span 4}}
.panel.score{{grid-column:span 7}} .panel.dispatch{{grid-column:span 5}} .panel.pipeline{{grid-column:span 6}} .panel.tasks{{grid-column:span 6}} .panel.cron{{grid-column:1/-1}} .panel.logs{{grid-column:span 5}} .panel.people{{grid-column:span 7}}
.value{{font-size:38px;line-height:.9;letter-spacing:-.065em;font-weight:900}}
.value small{{font-size:14px;letter-spacing:0;color:var(--muted);font-weight:650;margin-left:4px}}
.context{{color:var(--subtle);font-size:12px;line-height:1.45;margin-top:8px}}
.delta-row{{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}}
.delta-row span{{font-family:var(--font-mono);font-size:11px;border:1px solid var(--line);border-radius:999px;padding:5px 8px;color:var(--subtle)}}
.delta-row .up{{color:var(--green);border-color:rgba(52,211,153,.34)}} .delta-row .down{{color:var(--red);border-color:rgba(251,113,133,.34)}}
.score-layout{{display:grid;grid-template-columns:minmax(0,1fr) 190px;gap:20px;align-items:end}}
.spark{{height:96px;display:flex;align-items:end;gap:6px;border:1px solid var(--line);border-radius:18px;background:rgba(2,8,8,.48);padding:12px}}
.spark i{{flex:1;min-width:6px;border-radius:999px 999px 4px 4px;background:linear-gradient(180deg,var(--cream),var(--green));box-shadow:0 0 20px rgba(255,230,203,.18)}}
.agent-flow{{display:grid;grid-template-columns:1fr;gap:12px;align-items:stretch;margin-top:16px}}
.chief,.agent-node{{border:1px solid var(--line);border-radius:18px;background:rgba(2,8,8,.34);padding:14px;min-height:auto}}
.chief b,.agent-node b{{display:block;font-size:22px;letter-spacing:-.04em}} .chief small,.agent-node small{{display:block;color:var(--muted);margin-top:8px;line-height:1.45}}
.node-label{{font-family:var(--font-mono);font-size:10px;letter-spacing:.16em;color:var(--subtle);text-transform:uppercase}}
.route{{color:var(--warm);font-family:var(--font-mono);font-weight:900;transform:rotate(90deg);width:max-content;margin:0 auto}}
.agent-nodes{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
.metric-list{{display:grid;gap:10px;margin-top:14px}}
.metric-list li{{list-style:none;display:flex;justify-content:space-between;align-items:flex-start;gap:14px;border-bottom:1px solid var(--line);padding-bottom:8px;color:var(--muted)}}
.metric-list b{{color:var(--cream);font-family:var(--font-mono);text-align:right;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}} th,td{{padding:11px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;overflow-wrap:anywhere}} th{{color:var(--subtle);font-family:var(--font-mono);font-size:11px;text-transform:uppercase;letter-spacing:.12em}} td small{{display:block;color:var(--subtle);margin-top:4px}} code{{font-family:var(--font-mono);font-size:11px;color:var(--cream);background:rgba(255,230,203,.08);border:1px solid rgba(255,230,203,.08);padding:3px 6px;border-radius:8px}}
.led{{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--subtle);margin-right:9px;box-shadow:0 0 12px currentColor}} tr.ok .led{{background:var(--green)}} tr.bad .led{{background:var(--red)}} tr.idle .led{{background:var(--warm)}} tr.paused{{opacity:.52}} .row-index{{font-family:var(--font-mono);color:var(--subtle);font-size:11px}}
.log-terminal{{background:var(--terminal);border:1px solid var(--line);border-radius:18px;padding:14px;margin-top:12px;font-family:var(--font-mono)}}
.log-terminal ul{{margin:0;padding:0;display:grid;gap:8px}} .log-terminal li{{list-style:none;display:flex;justify-content:space-between;gap:12px;color:var(--green)}}
.footer{{margin:22px 0 4px;color:var(--subtle);font-family:var(--font-mono);font-size:11px}}
@media(max-width:1280px){{.agent-nodes{{grid-template-columns:1fr}}}}
@media(max-width:1120px){{.shell{{display:block}}.rail,.mission{{position:relative;height:auto}}.rail{{flex-direction:row;justify-content:space-between}}.rail-nav{{display:flex;margin:0;width:auto}}.mission-card{{height:auto}}.hero-grid,.score-layout,.agent-flow{{grid-template-columns:1fr}}.tile,.tile.wide,.panel.score,.panel.dispatch,.panel.pipeline,.panel.tasks,.panel.logs,.panel.people{{grid-column:1/-1}}h1{{font-size:clamp(58px,18vw,112px)}}main{{padding:16px}}}}
@media(max-width:720px){{.rail-nav a{{width:42px;height:42px}}.hero{{padding:22px;min-height:auto}}.grid{{gap:10px}}th:nth-child(6),td:nth-child(6){{display:none}}table{{font-size:12px}}}}
</style>
</head>
<body>
<div class='shell'>
  <aside class='rail' aria-label='icon navigation'>
    <div class='mark'>H</div>
    <nav class='rail-nav'>
      <a class='active' href='#overview' title='Overview'>⌘</a>
      <a href='#agents' title='Agents'>A</a>
      <a href='#recordings' title='Recordings'>●</a>
      <a href='#cron' title='Cron'>↻</a>
      <a href='#logs' title='Logs'>▣</a>
    </nav>
    <div class='rail-status' title='state {esc(health)}'></div>
  </aside>

  <aside class='mission'>
    <div class='mission-card'>
      <div>
        <div class='brand-kicker'>Public Control Plane</div>
        <div class='brand-title'>Hermes<br>Ops</div>
      </div>
      <div class='mission-note'><b>Public-safe mirror</b><br>GitHub Pages에는 회의/통화 원문·파일명·인용문 없이 운영 지표만 표시.</div>
      <div class='mission-note'><b>Design mode</b><br>Teal command center · rail + mission panel + cockpit modules.</div>
      <div class='meta-stack'>
        <div class='meta-row'><span>generated</span><b>{esc(data['generated_at'])}</b></div>
        <div class='meta-row'><span>version</span><b>{esc(data['hermes_version'].replace('Hermes Agent ', ''))}</b></div>
        <div class='meta-row'><span>active cron</span><b>{esc(data['active_jobs'])}</b></div>
        <div class='meta-row'><span>public_safe</span><b>true</b></div>
      </div>
    </div>
  </aside>

  <main>
    <div class='topline'><span>source=aggregated_metrics · private_content=redacted</span><span>{esc(data.get('hermes_update') or 'Up to date')}</span></div>
    <section class='hero' id='overview'>
      <div class='hero-grid'>
        <div>
          <div class='label'>Hermes Agent Operations</div>
          <h1>OPS /<br>HERMES</h1>
          <div class='hero-sub'>Mac mini 기반 AI 운영 관제판. Cron, 녹음 파이프라인, 멀티에이전트, Daily Insight, Finance 지표를 공개-safe 형태로 미러링.</div>
          <div class='command'>public_safe=true · source=aggregated_metrics · private_content=redacted</div>
        </div>
        <div class='status-dial'>
          <span class='state-chip {health_class}'>{esc(health)}</span>
          <div class='dial-value'>{esc(ai.get('score', 0))}</div>
          <div class='context'>AI Ops Score · cron 성공률 {esc(ai.get('cron_success_rate_pct', 0))}% · 오류 신호 {esc(ai.get('recent_error_lines', 0))}</div>
        </div>
      </div>
    </section>

    <section class='grid' aria-label='telemetry ribbon'>
      <div class='tile'><div class='label'>Active Automation</div><div class='value'>{data['active_jobs']}</div><div class='context'>cron jobs online</div></div>
      <div class='tile'><div class='label'>Attention</div><div class='value'>{data['failed_jobs']}</div><div class='context'>failed/watch jobs</div></div>
      <div class='tile'><div class='label'>Record Notes</div><div class='value'>{data['call_recent_notes']}<small>통화</small></div><div class='context'>{data['meeting_recent_notes']} meeting notes</div></div>
      <div class='tile'><div class='label'>Task Candidates</div><div class='value'>{data['pending_call_tasks'] + data['pending_meeting_tasks']}</div><div class='context'>approval queue only</div></div>
      <div class='tile'><div class='label'>ROI / 7D</div><div class='value'>{esc(roi.get('estimated_hours_saved_7d', 0))}<small>h</small></div><div class='context'>{esc(roi.get('auto_items_7d', 0))} auto signals</div></div>
      <div class='tile'><div class='label'>Daily Insight</div><div class='value' style='font-size:28px'>{esc(di.get('delivery_reliability', '-'))}</div><div class='context'>next {esc(short_text(di.get('next_run_at', '-'), 24))}</div></div>

      <div class='panel score'>
        <div class='label'>Benchmark Cockpit</div>
        <div class='score-layout'>
          <div>
            <div class='value'>{esc(ai.get('score', 0))}<small> AI Ops Score</small></div>
            <div class='delta-row'><span class='{score_delta_cls}'>score {esc(score_delta_text)}</span><span class='{success_delta_cls}'>success {esc(success_delta_text)}</span><span class='{attention_delta_cls}'>attention {esc(attention_delta_text)}</span><span class='{error_delta_cls}'>errors {esc(error_delta_text)}</span></div>
            <div class='context'>Task 전환율 {esc(conv.get('candidate_rate_pct', 0))}% · 포트폴리오 top {esc(pf.get('top_holding', '-'))} · ROI {esc(roi.get('estimated_hours_saved_7d', 0))}h/7d</div>
          </div>
          <div><div class='spark'>{score_bars}</div><div class='context'>최근 {len(history)}회 score bars</div></div>
        </div>
      </div>

      <div class='panel dispatch' id='agents'>
        <div class='label'>Agent Dispatch Board</div>
        <div class='agent-flow'>
          <div class='chief'><span class='node-label'>chief</span><b>{esc(ma.get('chief_agent', '헤르미온느'))}</b><small>{esc(ma.get('operating_rule', '검증·side effect·최종 전달 담당'))}</small></div>
          <div class='route'>→</div>
          <div class='agent-nodes'>{multi_workers_html}</div>
        </div>
      </div>

      <div class='panel pipeline' id='recordings'>
        <div class='label'>Public-safe Recording Pipeline</div>
        <ul class='metric-list'>
          <li><span>call_last_run</span><b>{esc(data['call_state'].get('last_run_at', 'unknown'))}</b></li>
          <li><span>meeting_last_run</span><b>{esc(data['meeting_state'].get('last_run_at', 'unknown'))}</b></li>
          <li><span>cache_candidates</span><b>{esc(cache.get('finder_evictable_candidates', 'n/a'))} · {cache_mb:.1f}MB</b></li>
          <li><span>private_content</span><b>redacted</b></li>
        </ul>
      </div>

      <div class='panel tasks'>
        <div class='label'>Google Tasks Candidate Matrix</div>
        <table>
          <thead><tr><th>source</th><th>count</th><th>status</th><th>due hint</th><th>newest</th></tr></thead>
          <tbody>{tasks_html}</tbody>
        </table>
      </div>

      <div class='panel people'>
        <div class='label'>Daily Insight / People Team</div>
        <div class='value' style='font-size:30px'>{esc(people.get('name'))}</div>
        <div class='delta-row'><span class='{people_cls}'>{esc(people_status)}</span><span>next {esc(short_text(people.get('next_run_at'), 28))}</span><span>job {esc(people.get('job_id'))}</span></div>
        <div class='context'>최근 오류: {esc('없음' if not people.get('last_error') else '있음 — 상세는 비공개 운영 로그에서 확인')}</div>
      </div>

      <div class='panel logs' id='logs'>
        <div class='label'>Sanitized Log Stream</div>
        <div class='log-terminal'><ul>{error_summary_html}</ul></div>
        <ul class='metric-list'><li><span>attention_jobs</span><b>{len(failed_jobs)}</b></li>{failed_html}</ul>
      </div>

      <div class='panel cron' id='cron'>
        <div class='label'>Cron Operations Board</div>
        <table>
          <thead><tr><th></th><th>category / job</th><th>id</th><th>mode</th><th>last</th><th>next run</th></tr></thead>
          <tbody>{''.join(job_rows)}</tbody>
        </table>
      </div>
    </section>
    <div class='footer'>Source: public-safe aggregates from Hermes cron/state/log summaries. Raw call/meeting contents, filenames, evidence snippets, secrets, and local private paths are intentionally omitted.</div>
  </main>
</div>
</body>
</html>"""
    return html_doc

def main() -> int:
    PROJECT.mkdir(parents=True, exist_ok=True)
    data = collect()
    data['trend'] = update_history(data)
    (PROJECT / 'dashboard-data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (PROJECT / 'index.html').write_text(render(data), encoding='utf-8')
    print(PROJECT / 'index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
