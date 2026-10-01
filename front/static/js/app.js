(function () {
  const STORAGE_KEY = 'sb-settings';

  function loadSettings() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch (error) {
      return {};
    }
  }

  function saveSettings(settings) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }

  const settings = loadSettings();

  function applyTheme(dark) {
    document.documentElement.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
  }

  applyTheme(settings.dark === true);

  window.sbToast = function (message, variant) {
    const container = document.getElementById('sb-toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-bg-' + (variant || 'primary') + ' border-0';
    toast.innerHTML =
      '<div class="d-flex"><div class="toast-body">' +
      message +
      '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    container.appendChild(toast);
    const instance = new bootstrap.Toast(toast, { delay: 3000 });
    instance.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
  };

  document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sb-sidebar');
    const sidebarToggle = document.getElementById('sb-sidebar-toggle');
    const sidebarCollapsed = localStorage.getItem('sb-sidebar-collapsed') === 'true';
    if (sidebar && sidebarToggle) {
      const sidebarLinks = sidebar.querySelectorAll('a.sb-nav-item, a.sb-nav-sub');
      const updateSidebarTooltips = function (collapsed) {
        sidebarLinks.forEach(function (link) {
          if (!link.dataset.menuLabel) link.dataset.menuLabel = link.textContent.replace(/\s+/g, ' ').trim();
          if (collapsed) link.title = link.dataset.menuLabel;
          else link.removeAttribute('title');
        });
      };
      if (sidebarCollapsed) document.body.classList.add('sb-sidebar-collapsed');
      updateSidebarTooltips(sidebarCollapsed);
      sidebarToggle.setAttribute('aria-expanded', String(!sidebarCollapsed));
      sidebarToggle.addEventListener('click', function () {
        const collapsed = document.body.classList.toggle('sb-sidebar-collapsed');
        localStorage.setItem('sb-sidebar-collapsed', String(collapsed));
        updateSidebarTooltips(collapsed);
        sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
        sidebarToggle.setAttribute('aria-label', collapsed ? '사이드바 펼치기' : '사이드바 접기');
        sidebarToggle.title = collapsed ? '사이드바 펼치기' : '사이드바 접기';
      });
    }
    const chatFab = document.getElementById('sb-chat-open');
    if (chatFab) {
      let dragging = false;
      let moved = false;
      let offsetX = 0;
      let offsetY = 0;
      chatFab.addEventListener('pointerdown', function (event) {
        dragging = true;
        moved = false;
        const rect = chatFab.getBoundingClientRect();
        offsetX = event.clientX - rect.left;
        offsetY = event.clientY - rect.top;
        chatFab.setPointerCapture(event.pointerId);
        chatFab.classList.add('is-dragging');
      });
      chatFab.addEventListener('pointermove', function (event) {
        if (!dragging) return;
        moved = true;
        chatFab.style.left = Math.max(8, Math.min(window.innerWidth - chatFab.offsetWidth - 8, event.clientX - offsetX)) + 'px';
        chatFab.style.top = Math.max(8, Math.min(window.innerHeight - chatFab.offsetHeight - 8, event.clientY - offsetY)) + 'px';
        chatFab.style.right = 'auto';
        chatFab.style.bottom = 'auto';
      });
      chatFab.addEventListener('pointerup', function (event) {
        dragging = false;
        chatFab.classList.remove('is-dragging');
        if (moved) { event.preventDefault(); chatFab.dataset.dragged = 'true'; setTimeout(() => { delete chatFab.dataset.dragged; }, 250); }
      });
      chatFab.addEventListener('click', function (event) { if (chatFab.dataset.dragged === 'true') event.preventDefault(); });
    }
    const darkToggle = document.getElementById('sb-dark-mode');
    if (darkToggle) {
      darkToggle.checked = settings.dark === true;
      darkToggle.addEventListener('change', function () {
        settings.dark = darkToggle.checked;
        saveSettings(settings);
        applyTheme(darkToggle.checked);
      });
    }

    document.querySelectorAll('.sb-image-quality').forEach(function (input) {
      if (settings.imageQuality === input.value) input.checked = true;
      input.addEventListener('change', function () {
        settings.imageQuality = input.value;
        saveSettings(settings);
      });
    });

    document.querySelectorAll('.sb-notify').forEach(function (input) {
      const key = 'notify:' + input.id;
      if (typeof settings[key] === 'boolean') input.checked = settings[key];
      input.addEventListener('change', function () {
        settings[key] = input.checked;
        saveSettings(settings);
      });
    });

    const loading = document.getElementById('sb-loading');
    const loadingText = document.getElementById('sb-loading-text');
    window.sbLoading = function (show, text) {
      if (!loading) return;
      if (text && loadingText) loadingText.textContent = text;
      loading.hidden = !show;
    };

    document.querySelectorAll('[data-sb-loading]').forEach(function (form) {
      form.addEventListener('submit', function () {
        window.sbLoading(true, form.dataset.sbLoading);
      });
    });

    const bell = document.getElementById('sb-notification-btn');
    if (bell) {
      bell.addEventListener('click', function () {
        window.sbToast('Planning Agent 작업이 완료되었습니다.', 'primary');
      });
    }

    // Relative time formatting
    function formatRelativeTime(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHour = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHour / 24);

      if (diffSec < 60) return '방금 전';
      if (diffMin < 60) return diffMin + '분 전';
      if (diffHour < 24) return diffHour + '시간 전';
      if (diffDay === 1) return '어제';
      if (diffDay < 7) return diffDay + '일 전';
      return dateString;
    }

    // Apply relative time to elements with data-sb-relative-time
    document.querySelectorAll('[data-sb-relative-time]').forEach(function (el) {
      const originalTime = el.textContent;
      const relativeTime = formatRelativeTime(originalTime);
      if (relativeTime && relativeTime !== originalTime) {
        el.textContent = relativeTime;
        el.title = originalTime;
      }
    });

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Error Header Test Button
    const errorTestBtn = document.getElementById('sb-error-test-btn');
    const errorAlert = document.getElementById('sb-global-error-alert');
    const errorMessage = document.getElementById('sb-error-message');
    const errorAction = document.getElementById('sb-error-action');

    if (errorTestBtn && errorAlert) {
      errorTestBtn.addEventListener('click', function() {
        showErrorAlert('Project 01의 Agent 실행에 실패했습니다.', '/projects/detail/1');
      });

      if (errorAction) {
        errorAction.addEventListener('click', function() {
          const targetUrl = errorAction.dataset.targetUrl;
          if (targetUrl) {
            window.location.href = targetUrl;
          } else {
            window.sbToast('관련 프로젝트로 이동합니다.', 'info');
            hideErrorAlert();
          }
        });
      }
    }

    // Error Alert 표시 함수
    function showErrorAlert(message, targetUrl) {
      if (errorMessage) {
        errorMessage.textContent = message;
      }
      if (errorAction && targetUrl) {
        errorAction.dataset.targetUrl = targetUrl;
      }
      if (errorAlert) {
        errorAlert.style.display = 'block';
        document.body.classList.add('has-error');
      }
    }

    // Error Alert 숨기기 함수
    function hideErrorAlert() {
      if (errorAlert) {
        errorAlert.style.display = 'none';
        document.body.classList.remove('has-error');
      }
    }

    // 전역 함수로 노출
    window.showErrorAlert = showErrorAlert;
    window.hideErrorAlert = hideErrorAlert;

    // 테스트: 치명적인 오류 시뮬레이션 (개발용)
    // 실제 사용 시에는 API 응답이나 에러 핸들러에서 호출
    setTimeout(function() {
      // 테스트를 위해 5초 후 자동으로 오류 표시 (실제 사용 시 제거)
      // showErrorAlert('치명적인 오류가 발생했습니다. 시스템을 확인해주세요.');
    }, 5000);
  });
})();
