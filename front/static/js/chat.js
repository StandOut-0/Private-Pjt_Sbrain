document.addEventListener('DOMContentLoaded', function () {
  const panel = document.getElementById('sb-chat-panel');
  const form = document.getElementById('sb-chat-form');
  if (!panel || !form) return;

  const body = document.getElementById('sb-chat-body');
  const input = document.getElementById('sb-chat-input');
  const openBtn = document.getElementById('sb-chat-open');
  const closeBtn = document.getElementById('sb-chat-close');
  const expandBtn = document.getElementById('sb-chat-expand');
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

  function toggle(open) {
    panel.classList.toggle('open', open);
    openBtn.style.display = open ? 'none' : '';
    if (open) input.focus();
  }

  openBtn.addEventListener('click', () => toggle(true));
  closeBtn.addEventListener('click', () => toggle(false));

  if (expandBtn) {
    expandBtn.addEventListener('click', () => {
      panel.classList.toggle('expanded');
    });
  }

  // Initialize chat tabs (for static tabs in HTML)
  function initChatTabs() {
    const allTabBtns = document.querySelectorAll('.sb-chat-tab-btn');
    const tabContent = document.getElementById('tab-content');

    const tabData = {
      'guide': '[프로젝트 구현 가이드]<br>1. 주요 상품 / 서비스:<br>2. 주요 고객층:<br>3. 만들고 싶은 서비스:<br>4. 필요한 주요 기능:<br>5. 참고 서비스 / 디자인:<br>※ 모르는 항목은 비워두셔도 됩니다.</div>',
      'logo': '<div>로고 디자인 가이드<br>브랜드의 정체성을 나타내는 로고를 디자인합니다.</div>',
      'onepage': '<div>원페이지 디자인 가이드<br>핵심 정보를 한 페이지에 효과적으로 전달합니다.</div>',
      'survey': '<div>설문조사페이지 디자인 가이드<br>사용자 의견을 수집하는 설문폼을 디자인합니다.</div>'
    };

    allTabBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        allTabBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const tabKey = this.dataset.tab;
        if (tabContent && tabData[tabKey]) {
          tabContent.innerHTML = tabData[tabKey];
        }
      });
    });
  }

  initChatTabs();

  // Initialize response tabs
  function initResponseTabs() {
    const responseTabs = document.querySelectorAll('.sb-chat-response-tab');
    const responsePanels = document.querySelectorAll('.sb-chat-response-panel');

    responseTabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const tabName = this.dataset.tab;

        // Update tab active state
        responseTabs.forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        // Update panel visibility
        responsePanels.forEach(panel => {
          panel.classList.remove('active');
          if (panel.dataset.panel === tabName) {
            panel.classList.add('active');
          }
        });
      });
    });
  }

  initResponseTabs();

  // Initialize chat room switching
  function initChatRooms() {
    const chatRooms = document.querySelectorAll('.sb-chat-room');
    const newChatBtn = document.getElementById('sb-new-chat');

    chatRooms.forEach(room => {
      room.addEventListener('click', function() {
        chatRooms.forEach(r => r.classList.remove('active'));
        this.classList.add('active');

        // Badge 숫자 초기화 (실제 구현에서는 해당 채팅방의 메시지를 로드)
        const badge = this.querySelector('.sb-chat-room-badge');
        if (badge) {
          badge.style.display = 'none';
        }
      });
    });

    if (newChatBtn) {
      newChatBtn.addEventListener('click', function() {
        // 새 대화 생성 로직 (실제 구현 필요)
        chatRooms.forEach(r => r.classList.remove('active'));
        // 첫 번째 채팅방을 활성화
        if (chatRooms.length > 0) {
          chatRooms[0].classList.add('active');
        }
      });
    }
  }

  initChatRooms();

  function append(text, role) {
    const message = document.createElement('div');
    message.className = 'sb-msg sb-msg-' + role;

    // Check if message contains tab content (mock implementation)
    if (role === 'ai' && text.includes('[프로젝트 구현 가이드]')) {
      const tabsHtml = `<div class="sb-chat-tabs"><button class="sb-chat-tab-btn active" data-tab="tab1">프로젝트 구현 가이드</button>
          <button class="sb-chat-tab-btn" data-tab="tab2">로고만들기</button>
          <button class="sb-chat-tab-btn" data-tab="tab3">원페이지만들기</button>
          <button class="sb-chat-tab-btn" data-tab="tab4">설문조사페이지만들기</button>
        </div>
        <div class="sb-chat-tab-content active" id="tab1">
          <pre>${text}</pre>
        </div>
        <div class="sb-chat-tab-content" id="tab2">
          <p>로고 디자인 가이드가 여기에 표시됩니다.</p>
        </div>
        <div class="sb-chat-tab-content" id="tab3">
          <p>원페이지 디자인 가이드가 여기에 표시됩니다.</p>
        </div>
        <div class="sb-chat-tab-content" id="tab4">
          <p>설문조사페이지 디자인 가이드가 여기에 표시됩니다.</p>
        </div>
      `;
      message.innerHTML = tabsHtml;

      // Add tab click handlers
      const tabBtns = message.querySelectorAll('.sb-chat-tab-btn');
      tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
          tabBtns.forEach(b => b.classList.remove('active'));
          this.classList.add('active');

          const tabId = this.dataset.tab;
          message.querySelectorAll('.sb-chat-tab-content').forEach(content => {
            content.classList.remove('active');
          });
          message.querySelector('#' + tabId).classList.add('active');
        });
      });
    } else {
      message.textContent = text;
    }

    body.appendChild(message);
    body.scrollTop = body.scrollHeight;
  }

  function showTyping() {
    const typing = document.createElement('div');
    typing.className = 'sb-msg sb-msg-ai sb-msg-typing';
    typing.innerHTML = '<img src="' + form.dataset.loadingSrc + '" alt=""><span>Supervisor Agent 가 작업 중입니다...</span>';
    body.appendChild(typing);
    body.scrollTop = body.scrollHeight;
    return typing;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    append(text, 'user');
    input.value = '';
    const typing = showTyping();

    fetch(form.dataset.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ message: text }),
    })
      .then((response) => response.json())
      .then((data) => append(data.reply, 'ai'))
      .catch(() => append('일시적인 오류가 발생했습니다. 다시 시도해주세요.', 'ai'))
      .finally(() => typing.remove());
  });
});
