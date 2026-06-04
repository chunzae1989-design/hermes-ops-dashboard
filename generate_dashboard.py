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
    """Return public-safe status for the Hermes 주무 + specialist workers setup."""
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
        'chief_agent': 'Hermes 주무',
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
        'operating_rule': '리서치는 아기, 디자인은 디지, 검증·side effect·최종 전달은 Hermes 주무',
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
    bm = data.get('benchmarks', {})
    ai = bm.get('ai_ops', {})
    conv = bm.get('task_conversion', {})
    di = bm.get('daily_insight', {})
    pf = bm.get('portfolio', {})
    roi = bm.get('roi', {})
    ma = data.get('multi_agent', {})
    trend = data.get('trend', {})
    history = trend.get('history', [])[-5:]
    score_delta_text, score_delta_cls = trend.get('score_delta', ('-', 'flat'))
    success_delta_text, success_delta_cls = trend.get('success_delta', ('-', 'flat'))
    attention_delta_text, attention_delta_raw_cls = trend.get('attention_delta', ('-', 'flat'))
    error_delta_text, error_delta_raw_cls = trend.get('error_delta', ('-', 'flat'))
    # 주의/오류는 줄어드는 것이 좋은 방향이므로 색상을 반전한다.
    attention_delta_cls = 'up' if attention_delta_raw_cls == 'down' else 'down' if attention_delta_raw_cls == 'up' else 'flat'
    error_delta_cls = 'up' if error_delta_raw_cls == 'down' else 'down' if error_delta_raw_cls == 'up' else 'flat'
    score_points = [float(h.get('score') or 0) for h in trend.get('history', [])[-10:]] or [float(ai.get('score', 0) or 0)]
    score_bars = ''.join(
        f"<i title='{esc(compact_time(h.get('ts', '')))} · {esc(h.get('score', 0))}점' style='height:{max(10, min(100, float(h.get('score') or 0)))}%'></i>"
        for h in trend.get('history', [])[-10:]
    ) or "<i style='height:50%'></i>"
    trend_rows = ''.join(
        f"<tr><td>{esc(compact_time(h.get('ts', '')))}</td><td><b>{esc(h.get('score', 0))}</b></td><td>{esc(h.get('cron_success_rate_pct', 0))}%</td><td>{esc(h.get('attention_jobs', 0))}</td><td>{esc(h.get('recent_error_lines', 0))}</td></tr>"
        for h in reversed(history)
    ) or "<tr><td colspan='5'>추이 데이터 수집 전</td></tr>"
    benchmark_cards = f"""
    <div class='card trend-card wide'><div class='label'>1. AI Ops Score</div>
      <div class='score-layout'>
        <div>
          <div class='kpi'><div class='value'>{esc(ai.get('score', 0))}</div><span class='pill {'ok' if ai.get('score', 0) >= 80 else 'warn'}'>ops</span></div>
          <div class='trend-delta'><span class='{score_delta_cls}'>Score {esc(score_delta_text)}</span><span class='{success_delta_cls}'>성공률 {esc(success_delta_text)}</span><span class='{attention_delta_cls}'>주의 {esc(attention_delta_text)}</span><span class='{error_delta_cls}'>오류 {esc(error_delta_text)}</span></div>
          <div class='sub'>cron 성공률 {esc(ai.get('cron_success_rate_pct', 0))}% · 주의 {esc(ai.get('attention_jobs', 0))}개 · 7일 실행 {esc(ai.get('cron_runs_7d', 0))}회</div>
        </div>
        <div class='spark-wrap'><div class='spark'>{score_bars}</div><div class='sub'>최근 {len(score_points)}회 score 추이</div></div>
      </div>
      <table class='compact trend-table'>
        <thead><tr><th>시각</th><th>Score</th><th>성공률</th><th>주의</th><th>오류</th></tr></thead>
        <tbody>{trend_rows}</tbody>
      </table>
    </div>
    <div class='card'><div class='label'>2. Task 전환율</div><div class='value'>{esc(conv.get('candidate_rate_pct', 0))}%</div><div class='sub'>7일 노트 {esc(conv.get('recording_notes_7d', 0))}개 → 후보 {esc(conv.get('task_candidates', 0))}개</div></div>
    <div class='card'><div class='label'>3. Daily Insight 품질</div><div class='kpi'><div class='value small'>{esc(di.get('delivery_reliability', '-'))}</div><span class='pill {status_class(di.get('job_status'))}'>{esc(di.get('job_status', '-'))}</span></div><div class='sub'>다음 실행 {esc(di.get('next_run_at', '-'))}</div></div>
    <div class='card'><div class='label'>4. 포트폴리오 벤치마크</div><div class='value small'>{esc(pf.get('top_holding', '-'))}</div><div class='sub'>상위 비중 {esc(pf.get('top_weight_pct', 0))}% · 추적: {esc(', '.join(pf.get('benchmarks', [])))}</div></div>
    <div class='card wide'><div class='label'>5. Mac mini 자동화 ROI</div><div class='kpi'><div class='value'>{esc(roi.get('estimated_hours_saved_7d', 0))}h</div><span class='pill'>7d</span></div><div class='sub'>{esc(roi.get('auto_items_7d', 0))}개 자동 처리 신호 · {esc(roi.get('model', ''))}</div></div>
    <div class='card wide'><div class='label'>벤치마킹 상태</div><ul>
      <li>AI Ops: 성공률/주의 cron/오류 로그 기준 점수화</li>
      <li>Task: 공개 페이지에는 후보 내용 없이 전환 숫자만 표시</li>
      <li>Finance: 총액 {esc(format_krw(pf.get('total_value_krw', 0)))} · 현금비중 {esc(pf.get('cash_weight_pct', 0))}% · 최근 브리핑 {esc(pf.get('last_briefing_outputs_7d', 0))}건</li>
    </ul></div>
    """
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
    multi_priority_html = ''.join(
        f"<li>#{esc(j.get('priority'))} <code>{esc(j.get('job_id'))}</code> — {esc(j.get('name'))}</li>"
        for j in ma.get('refactor_priority_jobs', [])
    ) or '<li>리팩터링 후보 없음</li>'
    multi_workers_html = ''.join(
        f"<li><b>{esc(w.get('name'))}</b> <span class='pill {'ok' if w.get('available') else 'warn'}'>{esc(w.get('type'))}</span> — {esc(w.get('rule'))} · routes {esc(w.get('routes_defined', 0))}</li>"
        for w in ma.get('workers', [])
    ) or '<li>등록된 worker 없음</li>'

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
.score-layout {{ display:grid; grid-template-columns: minmax(0, 1fr) 150px; gap:16px; align-items:end; }}
.trend-delta {{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 4px; }}
.trend-delta span {{ font-size:11px; border:1px solid var(--line); border-radius:999px; padding:4px 7px; color:var(--muted); }}
.trend-delta .up {{ color:var(--green); border-color:rgba(63,185,80,.35); background:rgba(63,185,80,.08); }}
.trend-delta .down {{ color:var(--red); border-color:rgba(248,81,73,.35); background:rgba(248,81,73,.08); }}
.trend-delta .flat {{ color:var(--muted); }}
.spark-wrap {{ min-width:130px; }}
.spark {{ height:58px; display:flex; align-items:end; gap:5px; padding:8px; border:1px solid rgba(48,54,61,.75); border-radius:14px; background:rgba(255,255,255,.03); }}
.spark i {{ flex:1; min-width:5px; border-radius:999px 999px 3px 3px; background:linear-gradient(180deg, var(--blue), var(--purple)); box-shadow:0 0 18px rgba(88,166,255,.25); }}
.trend-table th, .trend-table td {{ padding:7px 6px; font-size:12px; }}
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
  .score-layout {{ grid-template-columns: 1fr; }}
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

    {benchmark_cards}

    <div class='card wide'><div class='label'>Hermes</div><div class='value small'>{esc(data['hermes_version'])}</div><div class='sub'>{esc(data.get('hermes_update') or '업데이트 추가 메시지 없음')}</div></div>
    <div class='card wide'><div class='label'>Disk / Synology</div><div class='value small'>{esc(data['recordings_du'])} 녹음 캐시</div><div class='sub'>{esc(data['disk_line'])}</div></div>

    <div class='card full'><div class='label'>Multi-Agent System · 주무 × Specialists</div>
      <div class='kpi'><div class='value small'>{esc(ma.get('chief_agent', 'Hermes 주무'))} → 아기 · 디지</div><span class='pill {'ok' if ma.get('enabled') and ma.get('agy_available') and ma.get('design_agent_available') else 'warn'}'>{'ready' if ma.get('enabled') and ma.get('agy_available') and ma.get('design_agent_available') else 'check'}</span></div>
      <div class='sub'>{esc(ma.get('operating_rule', '리서치는 아기, 디자인은 디지, 검증/최종 전달은 Hermes'))}</div>
      <ul>{multi_workers_html}</ul>
      <ul>
        <li>Manual: <code>{esc(ma.get('role_manual'))}</code> · Research prompt: <code>{esc(ma.get('prompt_template'))}</code> · Audit: <code>{esc(ma.get('token_audit'))}</code></li>
        <li>Design agent: <b>{esc(ma.get('design_agent_name', '디지'))}</b> · available <b>{esc(ma.get('design_agent_available'))}</b> · design routes <b>{esc(ma.get('design_routes_defined', 0))}</b></li>
        <li>최우선 절감 job <code>{esc(ma.get('highest_token_job_id'))}</code> 상태 <b>{esc(ma.get('highest_token_job_status'))}</b></li>
      </ul>
      <div class='sub'>리팩터링 우선순위</div>
      <ul>{multi_priority_html}</ul>
    </div>

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
    data['trend'] = update_history(data)
    (PROJECT / 'dashboard-data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (PROJECT / 'index.html').write_text(render(data), encoding='utf-8')
    print(PROJECT / 'index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
