document.addEventListener('DOMContentLoaded', function () {
  const panel = document.getElementById('sb-chat-panel');
  const form = document.getElementById('sb-chat-form');
  if (!panel || !form) return;

  const body = document.getElementById('sb-chat-body');
  const input = document.getElementById('sb-chat-input');
  const openBtn = document.getElementById('sb-chat-open');
  const closeBtn = document.getElementById('sb-chat-close');
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

  function toggle(open) {
    panel.classList.toggle('open', open);
    openBtn.style.display = open ? 'none' : '';
    if (open) input.focus();
  }

  openBtn.addEventListener('click', () => toggle(true));
  closeBtn.addEventListener('click', () => toggle(false));

  function append(text, role) {
    const message = document.createElement('div');
    message.className = 'sb-msg sb-msg-' + role;
    message.textContent = text;
    body.appendChild(message);
    body.scrollTop = body.scrollHeight;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    append(text, 'user');
    input.value = '';

    fetch(form.dataset.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ message: text }),
    })
      .then((response) => response.json())
      .then((data) => append(data.reply, 'ai'))
      .catch(() => append('일시적인 오류가 발생했습니다. 다시 시도해주세요.', 'ai'));
  });
});
