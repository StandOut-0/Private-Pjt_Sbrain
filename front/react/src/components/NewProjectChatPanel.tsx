import { useState, type FormEvent, type RefObject } from 'react';
import { X } from 'lucide-react';

const guides: Record<string, string> = {
  guide: '[프로젝트 구현 가이드]\n1. 주요 상품 / 서비스:\n2. 주요 고객층:\n3. 만들고 싶은 서비스:\n4. 필요한 주요 기능:\n5. 참고 서비스 / 디자인:\n※ 모르는 항목은 비워두셔도 됩니다.',
  logo: '[로고 만들기 가이드]\n브랜드 이름과 전달하고 싶은 분위기, 선호하는 색상과 참고 이미지를 알려주세요.',
  onepage: '[원페이지 만들기 가이드]\n페이지의 목적, 주요 고객, 꼭 보여줄 내용과 원하는 디자인을 적어주세요.',
  survey: '[설문조사 페이지 만들기 가이드]\n설문 목적과 대상, 질문 항목, 응답 방식과 완료 후 안내 내용을 적어주세요.',
};

const tabs = [
  ['guide', '프로젝트 구현 가이드'],
  ['logo', '로고만들기'],
  ['onepage', '원페이지만들기'],
  ['survey', '설문조사페이지만들기'],
] as const;

export function NewProjectChatPanel({ onClose, onSubmit, inputRef }: {
  onClose: () => void;
  onSubmit: (prompt: string) => void;
  inputRef: RefObject<HTMLInputElement | null>;
}) {
  const [tab, setTab] = useState<keyof typeof guides>('guide');
  const [draft, setDraft] = useState('');
  const [expanded, setExpanded] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = draft.trim();
    if (prompt) onSubmit(prompt);
  }

  return <section className={`sb-chat-panel open${expanded ? ' expanded' : ''}`} role="dialog" aria-label="새 프로젝트 챗봇">
    <div className="sb-chat-head"><span>Second Brain</span><div className="d-flex gap-2">
      <button className="btn btn-sm sb-icon-btn" type="button" title="크게 보기" aria-label="크게 보기" onClick={() => setExpanded(value => !value)}><i className="bi bi-arrows-fullscreen"/></button>
      <button className="btn btn-sm sb-icon-btn" type="button" onClick={onClose} aria-label="챗봇 닫기"><X size={17}/></button>
    </div></div>
    <div className="sb-chat-body"><div className="sb-chat-sidebar">
      <div className="sb-chat-sidebar-header"><span className="fw-semibold">채팅방</span><button className="btn btn-sm btn-primary" type="button"><i className="bi bi-plus-lg"/> 새 대화</button></div>
      <div className="sb-chat-rooms">
        {[
          ['planning', 'Planning Agent', '기획 및 요구사항 분석...', '3', 'bi-clipboard-data'],
          ['design', 'Design Agent', 'UI/UX 디자인 작업...', '1', 'bi-palette'],
          ['engineering', 'Engineering Agent', 'Frontend/Backend 개발...', '', 'bi-code-slash'],
        ].map(([key, name, preview, badge, icon], index) => <div className={`sb-chat-room${index === 0 ? ' active' : ''}`} data-room={key} key={key}>
          <div className="sb-chat-room-icon"><i className={`bi ${icon}`}/></div><div className="sb-chat-room-info"><div className="sb-chat-room-name">{name}</div><div className="sb-chat-room-preview">{preview}</div></div>{badge && <div className="sb-chat-room-badge">{badge}</div>}
        </div>)}
      </div>
    </div>
    <div className="sb-chat-main">
      <div className="sb-chat-animation"><div className="sb-chat-gif-container"><img src="/static/img/loading.gif" alt="AI 준비 중" className="sb-chat-gif"/></div><div className="sb-chat-welcome-text"><div className="sb-chat-greeting">안녕하세요! 👋</div><div className="sb-chat-status">준비 중입니다...</div><div className="sb-chat-loading-text">프로젝트 내용을 살펴보고 있어요.</div></div></div>
      <div className="sb-msg sb-msg-ai">프로젝트를 빠르게 구현하고 싶다면 아래 가이드를 확인하고, 만들고 싶은 내용을 입력해 주세요.</div>
      <div className="sb-msg sb-msg-ai"><div className="sb-chat-tabs" data-react-chat-tabs>{tabs.map(([key, label]) => <button className={`sb-chat-tab-btn${tab === key ? ' active' : ''}`} data-tab={key} onClick={event => { event.preventDefault(); setTab(key); }} type="button" key={key}>{label}</button>)}</div><div className="sb-chat-tab-content"><div className="sb-chat-guide-title">{guides[tab].split('\n')[0]}</div><pre className="sb-chat-guide-text">{guides[tab]}</pre></div></div>
    </div></div>
    <form className="sb-chat-foot" onSubmit={submit}><input id="sb-project-chat-input" ref={inputRef} className="form-control form-control-sm" value={draft} onChange={event => setDraft(event.target.value)} placeholder="만들고 싶은 프로젝트를 설명해주세요." aria-label="새 프로젝트 설명"/><button className="btn btn-outline-secondary btn-sm" type="button" title="음성 입력"><i className="bi bi-mic"/></button><button className="btn btn-primary btn-sm" type="submit" aria-label="초안을 만들기"><i className="bi bi-send"/></button></form>
  </section>;
}
