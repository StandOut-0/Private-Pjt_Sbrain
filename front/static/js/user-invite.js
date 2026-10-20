(function () {
  const modal = document.getElementById('sb-invite-modal');
  if (!modal) return;
  const email = modal.querySelector('#sb-invite-email');
  const link = modal.querySelector('#sb-invite-link');
  const guide = modal.querySelector('#sb-invite-guide');
  const preview = modal.querySelector('#sb-invite-preview');
  const status = modal.querySelector('#sb-invite-status');
  const title = 'Second Brain 사용 초대';
  [link, guide].forEach(input => { input.value = new URL(input.dataset.path, location.origin).href; });
  preview.value = 'Second Brain에 초대합니다.\n\n서비스 접속: ' + link.value + '\n사용자 가이드 (샘플 PDF): ' + guide.value + '\n\n계정 및 접근 권한은 관리자에게 문의해주세요.';
  modal.querySelector('#sb-invite-local-note').hidden = !(['localhost', '127.0.0.1', '[::1]'].includes(location.hostname));

  async function copy(input) {
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(input.value);
      status.textContent = '복사했습니다.';
    } catch (error) {
      input.focus();
      input.select();
      status.textContent = '자동 복사를 사용할 수 없습니다. 선택된 내용을 직접 복사해주세요.';
    }
  }
  modal.querySelectorAll('[data-invite-copy]').forEach(button => {
    button.addEventListener('click', () => copy(document.getElementById(button.dataset.inviteCopy)));
  });
  modal.querySelector('#sb-invite-email-send').addEventListener('click', () => {
    if (!email.reportValidity()) return;
    location.href = 'mailto:' + encodeURIComponent(email.value.trim()) + '?subject=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(preview.value);
    status.textContent = '이메일 앱에서 내용을 확인한 뒤 직접 전송해주세요.';
  });
  modal.querySelector('#sb-invite-share').addEventListener('click', async () => {
    if (!navigator.share) { await copy(preview); return; }
    try {
      await navigator.share({title, text: preview.value});
      status.textContent = '공유 창을 닫았습니다.';
    } catch (error) {
      if (error.name !== 'AbortError') await copy(preview);
    }
  });
  modal.addEventListener('hidden.bs.modal', () => { email.value = ''; status.textContent = ''; });
})();
