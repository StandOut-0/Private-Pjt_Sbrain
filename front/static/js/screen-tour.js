(function () {
  const storageKey = 'sb-screen-tour-v2';
  function itinerary() {
    const admin = !!document.querySelector('.sb-sidebar-menus a[href="/manage/tasks/"]');
    const project = [...document.querySelectorAll('.sb-sidebar-menus a, .sb-project-card')].find(link => /^\/projects\/\d+\/$/.test(link.getAttribute('href') || ''));
    const routes = admin ? [
      ['/manage/tasks/', '.sb-content', 'Tasks', '관리자 화면에서 작업 목록과 진행 상태를 확인합니다.'],
      ['/manage/agents/', '.sb-content', 'Agents', '에이전트 목록에서 역할과 실행 정보를 확인합니다.']
    ] : [
      ['/', '.sb-content', '대시보드', '프로젝트 진행 상황과 최근 작업, 에이전트 실행 및 결과물을 한눈에 확인하는 화면입니다.'],
      ['/projects/list/', '.sb-project-card, .sb-content', '프로젝트 목록', '프로젝트 카드에서 진행 상태를 확인하고 상세 화면으로 이동할 수 있습니다.']
    ];
    if (!admin && project) routes.push([project.getAttribute('href'), '.sb-artifact-browser', '프로젝트 결과물', '생성된 파일을 탐색하고 미리볼 수 있습니다.']);
    routes.push(['/coming-soon/', '#feature-preview', 'Coming Soon', '준비 중인 기능과 앞으로의 계획을 살펴보세요.']);
    routes.push(['/user-guide/', '.sb-guide-document', '사용자 가이드', 'PDF 가이드를 읽거나 다운로드할 수 있습니다.']);
    return routes.map(([url,selector,title,description]) => ({url,selector,title,description}));
  }
  function save(state) {
    try { sessionStorage.setItem(storageKey, JSON.stringify(state)); return true; }
    catch (error) { return false; }
  }
  function pending() {
    try {
      const state = JSON.parse(sessionStorage.getItem(storageKey));
      if (!state || !Array.isArray(state.steps) || !Number.isInteger(state.index) || state.index < 0 || state.index >= state.steps.length) return null;
      if (!state.steps.every(step => /^\/(?:$|projects\/(?:list|\d+)\/|manage\/(?:tasks|agents)\/|coming-soon\/|user-guide\/)$/.test(step.url) && typeof step.selector === 'string')) return null;
      return state;
    } catch (error) { return null; }
  }
  let tour = null;
  const visible = el => el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
  function finish() {
    try { sessionStorage.removeItem(storageKey); } catch (error) { /* Storage may be unavailable. */ }
    if (!tour) return;
    const previous = tour.previous;
    tour.nodes.forEach(node => node.remove());
    tour = null;
    window.removeEventListener('resize', position);
    window.removeEventListener('scroll', position, true);
    document.removeEventListener('keydown', keys);
    if (previous && previous.isConnected) previous.focus({preventScroll:true});
  }
  function position() {
    if (!tour) return;
    const {steps, index, highlight, dialog} = tour;
    const rect = steps[index].el.getBoundingClientRect();
    Object.assign(highlight.style, {left:Math.max(4,rect.left-4)+'px', top:Math.max(4,rect.top-4)+'px', width:Math.min(rect.width+8,innerWidth-8)+'px', height:Math.min(rect.height+8,innerHeight-8)+'px'});
    const width = dialog.offsetWidth, height = dialog.offsetHeight;
    const below = rect.bottom + 16;
    const top = below + height <= innerHeight-16 ? below : rect.top-height-16 >= 16 ? rect.top-height-16 : innerHeight-height-16;
    dialog.style.left = Math.max(16,Math.min(rect.left,innerWidth-width-16))+'px';
    dialog.style.top = Math.max(16,top)+'px';
  }
  function show(index) {
    tour.index = index;
    const step = tour.steps[index];
    if (step.url && location.pathname !== step.url) {
      if (save({steps:tour.steps,index})) { location.assign(step.url); return; }
      finish();
      if (window.sbToast) window.sbToast('화면 이동 안내를 위해 브라우저의 세션 저장소를 허용해주세요.', 'secondary');
      return;
    }
    if (step.url) {
      step.el = document.querySelector(step.selector);
      if (!visible(step.el)) step.el = document.querySelector('.sb-content');
      // Store only route data; DOM elements do not survive navigation.
      save({steps:tour.steps.map(({url,selector,title,description}) => ({url,selector,title,description})),index});
    }
    tour.dialog.querySelector('h2').textContent = step.title;
    tour.dialog.querySelector('p').textContent = step.description;
    tour.dialog.querySelector('[data-count]').textContent = (index+1)+' / '+tour.steps.length;
    tour.dialog.querySelector('[data-prev]').disabled = index === 0;
    const next = tour.steps[index+1];
    tour.dialog.querySelector('[data-next]').textContent = !next ? '완료' : next.url && next.url !== location.pathname ? '다음 화면으로' : '다음';
    step.el.scrollIntoView({block:'nearest',behavior:'instant'});
    position();
    tour.dialog.querySelector('[data-next]').focus({preventScroll:true});
  }
  function keys(event) {
    if (event.key === 'Escape') { event.preventDefault(); finish(); }
    if (event.key !== 'Tab' || !tour) return;
    const buttons = [...tour.dialog.querySelectorAll('button')].filter(b => !b.disabled);
    const first = buttons[0], last = buttons[buttons.length-1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  function start(resume) {
    finish();
    const steps = resume ? resume.steps : itinerary();
    if (!steps.length) return;
    const shade = document.createElement('div'); shade.className = 'sb-tour-shade';
    const highlight = document.createElement('div'); highlight.className = 'sb-tour-highlight'; highlight.setAttribute('aria-hidden','true');
    const dialog = document.createElement('div'); dialog.className = 'sb-tour-dialog';
    dialog.setAttribute('role','dialog'); dialog.setAttribute('aria-modal','true'); dialog.setAttribute('aria-labelledby','sb-tour-title'); dialog.setAttribute('aria-describedby','sb-tour-description');
    dialog.innerHTML = '<div class="sb-tour-head"><span data-count></span><button class="sb-tour-close" type="button">종료</button></div><div aria-live="polite"><h2 id="sb-tour-title"></h2><p id="sb-tour-description"></p></div><div class="sb-tour-actions"><button class="btn btn-outline-secondary" data-prev type="button">이전</button><button class="btn btn-primary" data-next type="button">다음</button></div>';
    tour = {steps,index:0,highlight,dialog,previous:document.activeElement,nodes:[shade,highlight,dialog]};
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
  document.addEventListener('click',event => { if (event.target.closest('[data-screen-tour]')) start(); });
  document.addEventListener('DOMContentLoaded',() => {
    const state = pending();
    if (!state) return;
    // Resume only on the destination page; unrelated navigation cancels the Tour.
    if (document.querySelector('.sb-topbar') && state.steps[state.index].url === location.pathname) start(state);
    else finish();
  });
})();
