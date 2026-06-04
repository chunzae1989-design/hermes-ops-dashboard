# Hermes Ops Dashboard

Mac mini 기반 Hermes Agent 운영 현황을 한 페이지로 모아보는 정적 HTML 대시보드입니다.

## 포함 항목

- AI Ops Score / Task 전환율 / Daily Insight 품질 / 포트폴리오 벤치마크 / Mac mini 자동화 ROI
- Multi-Agent System: Hermes 주무 × 아기(`agy`) 리서치 워커 × 디지 디자인 워커 상태
- 통화녹음·회의록 처리 상태
- Google Tasks 승인 후보 요약(내용 비공개)
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
