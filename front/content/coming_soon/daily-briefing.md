---
title: 개인 Daily Briefing
summary: 뉴스 / 날씨 / 주요 이슈를 수집해 개인 맞춤 브리핑을 생성한다.
status: 아이디어
category: Data
technologies:
- Web Crawling
- External API
- LLM Summarization
related_agents:
- Data
- AI
- Reflection
created_at: '2026-08-11'
updated_at: '2026-08-11'
---

## 목적

사용자가 매일 확인해야 하는 정보를 Data Agent가 수집하고 AI Agent가 요약해 전달한다.
MVP 범위에서는 제외하고 확장 시나리오로 관리한다.

## 예상 구조

```
Supervisor → Data Agent → AI Agent → Reflection Agent → Daily Briefing
```

## 적용 계획

1. 수집 대상 소스 정의 (뉴스 / 날씨)
2. Crawling & External API 연동
3. 요약 및 중요도 판단 프롬프트 설계
4. Reflection 검증 후 Dashboard 카드로 노출
