(function () {
  const storageKey = 'sb-screen-tour-v6';
  const hashPrefix = '#sb-tour=';
  const payloadNode = document.getElementById('sb-react-data');
  try {
    if (JSON.parse(payloadNode?.textContent || '{}').user?.is_admin) {
      sessionStorage.removeItem(storageKey);
      if (location.hash.startsWith(hashPrefix)) history.replaceState(null, '', location.pathname + location.search);
      return;
    }
  } catch (error) { return; }

  function itinerary() {
    const project = [...document.querySelectorAll('.sb-sidebar-menus a, .sb-project-card')].find(link => /^\/projects\/\d+\/$/.test(link.getAttribute('href') || ''));
    const routes = [
      ['/', '.sb-overview', '대시보드', '환영 영역, 프로젝트 요약, 내 프로젝트와 자주 찾는 메뉴를 한 화면에서 확인합니다.'],
      ['/projects/list/', '.sb-project-card, .sb-project-filter', '프로젝트 목록', '프로젝트 카드와 필터를 사용해 원하는 프로젝트를 찾을 수 있습니다.']
    ];
    routes.push(['/projects/list/', '#sb-project-chat-input', '챗봇으로 새 프로젝트 작성', '챗봇에 만들고 싶은 내용을 설명하면 새 프로젝트 입력 초안으로 옮길 수 있습니다.', false, true]);
    if (project) {
      const projectUrl = project.getAttribute('href');
      routes.push([projectUrl, '.sb-chat-tabs', '챗봇 가이드', '프로젝트 채팅창에서 구현 가이드와 로고·원페이지·설문조사 가이드를 선택할 수 있습니다.', true]);
      routes.push([projectUrl, '#sb-chat-form', '챗봇에 질문하기', '입력창에 요청을 적고 보내기 버튼을 눌러 프로젝트 작업을 시작할 수 있습니다.', true]);
      routes.push([projectUrl, '.sb-artifact-browser', '프로젝트 결과물', 'Agent가 만든 파일을 목록에서 선택하고 미리보기를 확인할 수 있습니다.']);
    }
    routes.push(['/coming-soon/', '.sb-future-grid', 'Coming Soon', '준비 중인 기능 카드를 살펴보고 각 기능의 상세 설명을 열 수 있습니다.']);
    routes.push(['/user-guide/', '.sb-guide-document', '사용자 가이드', 'PDF 가이드를 읽거나 다운로드할 수 있습니다.']);
    return routes.map(([url, selector, title, description, openChat = false, openProjectChat = false]) => ({url, selector, title, description, openChat, openProjectChat}));
  }

  function validState(state) {
    return !!state && Array.isArray(state.steps) && Number.isInteger(state.index) && state.index >= 0 && state.index < state.steps.length &&
      (state.returnTo === undefined || (typeof state.returnTo === 'string' && state.returnTo.startsWith('/') && !state.returnTo.startsWith('//') && !state.returnTo.includes('..'))) &&
      state.steps.every(step => step && typeof step.url === 'string' && typeof step.selector === 'string' && step.url.startsWith('/') && !step.url.startsWith('//') && !step.url.includes('..') && (step.openChat === undefined || typeof step.openChat === 'boolean') && (step.openProjectChat === undefined || typeof step.openProjectChat === 'boolean'));
  }
  function encode(state) {
    const bytes = new TextEncoder().encode(JSON.stringify(state));
    let binary = '';
    bytes.forEach(byte => { binary += String.fromCharCode(byte); });
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  }
  function save(state) {
    try { sessionStorage.setItem(storageKey, JSON.stringify(state)); } catch (error) { /* Hash remains a fallback. */ }
    try { history.replaceState(null, '', location.pathname + location.search + hashPrefix + encode(state)); } catch (error) { /* Navigation may still use the saved session state. */ }
    return true;
  }
  function pending() {
    try {
      const stored = sessionStorage.getItem(storageKey);
      if (stored) {
        const state = JSON.parse(stored);
        if (validState(state)) return state;
      }
      if (!location.hash.startsWith(hashPrefix)) return null;
      const token = location.hash.slice(hashPrefix.length).replace(/-/g, '+').replace(/_/g, '/');
      const binary = atob(token + '='.repeat((4 - token.length % 4) % 4));
      const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
      const state = JSON.parse(new TextDecoder().decode(bytes));
      return validState(state) ? state : null;
    } catch (error) { return null; }
  }

  let tour = null;
  let lastResumeHash = '';
  const visible = element => element && element.getClientRects().length && getComputedStyle(element).visibility !== 'hidden' && getComputedStyle(element).display !== 'none';
  function clearState() {
    try { sessionStorage.removeItem(storageKey); } catch (error) { /* Storage may be disabled. */ }
    if (location.hash.startsWith(hashPrefix)) {
      try { history.replaceState(null, '', location.pathname + location.search); } catch (error) { location.hash = ''; }
    }
  }
  function finish() {
    const returnTo = tour?.returnTo;
    clearState();
    if (!tour) return;
    const previous = tour.previous;
    tour.nodes.forEach(node => node.remove());
    tour = null;
    window.removeEventListener('resize', position);
    window.removeEventListener('scroll', position, true);
    document.removeEventListener('keydown', keys);
    if (returnTo && `${location.pathname}${location.search}` !== returnTo) {
      location.assign(returnTo);
      return;
    }
    if (previous && previous.isConnected) previous.focus({preventScroll:true});
  }
  function position() {
    if (!tour) return;
    const {steps, index, highlight, dialog} = tour;
    const element = steps[index].el;
    if (!visible(element)) return;
    const rect = element.getBoundingClientRect();
    Object.assign(highlight.style, {left:Math.max(4,rect.left-4)+'px',top:Math.max(4,rect.top-4)+'px',width:Math.min(rect.width+8,innerWidth-8)+'px',height:Math.min(rect.height+8,innerHeight-8)+'px'});
    const width = dialog.offsetWidth, height = dialog.offsetHeight, below = rect.bottom + 16;
    const top = below + height <= innerHeight-16 ? below : rect.top-height-16 >= 16 ? rect.top-height-16 : innerHeight-height-16;
    dialog.style.left = Math.max(16,Math.min(rect.left,innerWidth-width-16))+'px';
    dialog.style.top = Math.max(16,top)+'px';
  }
  function show(index, attempts = 0) {
    if (!tour || index < 0 || index >= tour.steps.length) return;
    tour.index = index;
    const step = tour.steps[index];
    if (!step.openChat && !step.openProjectChat) window.dispatchEvent(new Event('sb:minimize-chatbot'));
    if (location.pathname !== step.url) {
      save({steps:tour.steps.map(({url,selector,title,description,openChat,openProjectChat}) => ({url,selector,title,description,openChat,openProjectChat})),index,returnTo:tour.returnTo});
      location.assign(step.url + location.hash);
      return;
    }
    if (step.openChat) {
      const panel = document.querySelector('#sb-chat-panel');
      if (panel && !panel.classList.contains('open')) {
        document.querySelector('#sb-chat-open')?.click();
        if (!panel.classList.contains('open')) {
          panel.classList.add('open');
          const openButton = document.querySelector('#sb-chat-open');
          if (openButton) openButton.style.display = 'none';
          document.querySelector('#sb-chat-input')?.focus({preventScroll:true});
        }
      }
    }
    if (step.openProjectChat) window.dispatchEvent(new Event('sb:focus-project-chat'));
    step.el = document.querySelector(step.selector);
    if (!visible(step.el)) {
      if (attempts < 100) {
        tour.targetTimer = setTimeout(() => { if (tour && tour.index === index) show(index, attempts+1); }, 50);
        return;
      }
      step.el = document.querySelector('.sb-content');
      if (!visible(step.el)) {
        window.sbToast?.('이 화면 안내 대상을 불러오지 못했습니다. 다음 화면으로 계속 이동합니다.', 'warning');
        if (index < tour.steps.length-1) show(index+1); else finish();
        return;
      }
    }
    save({steps:tour.steps.map(({url,selector,title,description,openChat,openProjectChat}) => ({url,selector,title,description,openChat,openProjectChat})),index,returnTo:tour.returnTo});
    tour.dialog.querySelector('h2').textContent = step.title;
    tour.dialog.querySelector('p').textContent = step.description;
    tour.dialog.querySelector('[data-count]').textContent = `${index+1} / ${tour.steps.length}`;
    tour.dialog.querySelector('[data-prev]').disabled = index === 0;
    tour.dialog.querySelector('[data-next]').textContent = index === tour.steps.length-1 ? '완료' : (tour.steps[index+1].url !== location.pathname ? '다음 화면으로' : '다음');
    step.el.scrollIntoView({block:'nearest',behavior:'instant'});
    position();
    tour.dialog.querySelector('[data-next]').focus({preventScroll:true});
  }
  function keys(event) {
    if (!tour) return;
    if (event.key === 'Escape') { event.preventDefault(); finish(); return; }
    if (event.key !== 'Tab') return;
    const buttons = [...tour.dialog.querySelectorAll('button')].filter(button => !button.disabled);
    const first = buttons[0], last = buttons[buttons.length-1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  function start(resume) {
    if (tour) { finish(); return; }
    const steps = resume ? resume.steps : itinerary();
    if (!steps.length) return;
    const returnTo = resume?.returnTo || `${location.pathname}${location.search}`;
    if (!resume && location.pathname !== steps[0].url) {
      save({steps,index:0,returnTo});
      location.assign(steps[0].url + location.hash);
      return;
    }
    const shade = document.createElement('div'); shade.className = 'sb-tour-shade';
    const highlight = document.createElement('div'); highlight.className = 'sb-tour-highlight'; highlight.setAttribute('aria-hidden','true');
    const dialog = document.createElement('div'); dialog.className = 'sb-tour-dialog';
    dialog.setAttribute('role','dialog'); dialog.setAttribute('aria-modal','true'); dialog.setAttribute('aria-labelledby','sb-tour-title'); dialog.setAttribute('aria-describedby','sb-tour-description');
    dialog.innerHTML = '<div class="sb-tour-head"><span data-count></span><button class="sb-tour-close" type="button">종료</button></div><div aria-live="polite"><h2 id="sb-tour-title"></h2><p id="sb-tour-description"></p></div><div class="sb-tour-actions"><button class="btn btn-outline-secondary" data-prev type="button">이전</button><button class="btn btn-primary" data-next type="button">다음</button></div>';
    tour = {steps,index:0,highlight,dialog,previous:document.activeElement,nodes:[shade,highlight,dialog],targetTimer:null,returnTo};
    tour.nodes.forEach(node => document.body.appendChild(node));
    shade.addEventListener('click',finish);
    dialog.querySelector('.sb-tour-close').addEventListener('click',finish);
    dialog.querySelector('[data-prev]').addEventListener('click',() => show(tour.index-1));
    dialog.querySelector('[data-next]').addEventListener('click',() => tour.index === tour.steps.length-1 ? finish() : show(tour.index+1));
    window.addEventListener('resize',position);
    window.addEventListener('scroll',position,true);
    document.addEventListener('keydown',keys);
    show(resume ? resume.index : 0);
  }
  function resumeTour() {
    const state = pending();
    if (!state || tour || location.hash === lastResumeHash || state.steps[state.index].url !== location.pathname) return;
    lastResumeHash = location.hash;
    start(state);
  }
  document.addEventListener('click',event => { if (event.target.closest('[data-screen-tour]')) start(); });
  window.addEventListener('sb:react-mounted',resumeTour);
  window.addEventListener('DOMContentLoaded',resumeTour,{once:true});
  window.addEventListener('load',resumeTour,{once:true});
  setTimeout(resumeTour,0);
})();
