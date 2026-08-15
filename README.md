# Hermes Ops Dashboard

Mac mini 기반 Hermes Agent 운영 현황을 한 페이지로 모아보는 정적 HTML 대시보드입니다.

현재 운영 디자인은 **Exception First**입니다. 이상 상태와 다음 조치를 먼저 읽고, 세부 운영 지표와 전체 크론 보드는 그 다음에 확인하도록 구성합니다.

## 포함 항목

- AI Ops Score / Task 전환율 / Daily Insight 품질 / 포트폴리오 벤치마크 / Mac mini 자동화 ROI
- Multi-Agent System: 헤르미온느 × 아기(`agy`) 리서치 워커 × 디지 디자인 워커 상태
- 통화녹음·회의록 처리 상태
- Google Tasks 승인 후보 요약(내용 비공개)
- 피플팀 뉴스 브리핑 발송 상태
- Hermes 버전/업데이트 상태
- Synology 녹음 로컬 캐시와 디스크 상태
- 최근 Hermes 에러 로그

## 갱신

```bash
python3 generate_dashboard.py
python3 verify_dashboard.py
```

출력:

- `index.html`
- `dashboard-data.json`

## 디자인 구조

- `generate_dashboard.py` — 데이터 수집과 public-safe 의미 마크업
- `exception_first_theme.py` — 선택된 운영 CSS, 로컬 경로 제거, 패널 우선순위와 반응형 동작
- `DESIGN.md` — Exception First 디자인 토큰과 사용 규칙
- `tokens.dtcg.json`, `tailwind.theme.json` — DESIGN.md에서 생성한 토큰 export

운영 HTML만 수동 수정하지 않습니다. 디자인 변경은 생성기 또는 테마 모듈에 반영해야 다음 크론 갱신 후에도 유지됩니다.
