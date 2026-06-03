# Hermes Ops Dashboard

Mac mini 기반 Hermes Agent 운영 현황을 한 페이지로 모아보는 정적 HTML 대시보드입니다.

## 포함 항목

- Hermes cron 활성/실패 상태
- 통화녹음·회의록 처리 상태
- Google Tasks 승인 후보 상세
- 피플팀 뉴스 브리핑 발송 상태
- Hermes 버전/업데이트 상태
- Synology 녹음 로컬 캐시와 디스크 상태
- 최근 Hermes 에러 로그

## 갱신

```bash
python3 generate_dashboard.py
```

출력:

- `index.html`
- `dashboard-data.json`
