---
title: MCP 기반 외부 Tool 확장
summary: Agent가 외부 시스템의 기능을 Tool 형태로 사용할 수 있도록 확장한다.
status: 연구 예정
category: Agent
technologies:
- MCP
- Tool Calling
- API
related_agents:
- Supervisor
- Engineering
- AI
created_at: '2026-08-11'
updated_at: '2026-08-11'
---

## 목적

Agent가 외부 시스템의 기능을 Tool 형태로 사용할 수 있도록 확장한다.

## 예상 구조

```
Supervisor
    ↓
  Agent
    ↓
MCP Client
    ↓
Search / DB / External API
```

## 적용 계획

1. MCP Server 구성
2. Tool 정의
3. Agent Tool Calling 연결
4. 실행 결과 검증
