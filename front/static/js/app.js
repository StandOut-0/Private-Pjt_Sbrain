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

    const bell = document.getElementById('sb-notification-btn');
    if (bell) {
      bell.addEventListener('click', function () {
        window.sbToast('Planning Agent 작업이 완료되었습니다.', 'primary');
      });
    }
  });
})();
