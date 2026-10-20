(function () {
  const form = document.getElementById('sb-google-login-form');
  const modal = document.getElementById('sb-google-consent-modal');
  if (!form || !modal) return;
  const check = document.getElementById('sb-google-consent-check');
  const confirm = document.getElementById('sb-google-consent-confirm');
  let pending = null;
  let approved = false;
  form.addEventListener('submit', event => {
    if (approved) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    pending = event.submitter || form.querySelector('[value="google"]');
    check.checked = false;
    confirm.disabled = true;
    document.getElementById('sb-google-consent-mode').textContent = pending.value === 'google-admin' ? '관리자 로그인 · 이후 Face 인증 화면으로 이동합니다.' : 'Google로 로그인';
    bootstrap.Modal.getOrCreateInstance(modal).show();
  }, true);
  check.addEventListener('change', () => { confirm.disabled = !check.checked; });
  confirm.addEventListener('click', () => {
    if (!check.checked || !pending || approved) return;
    approved = true;
    confirm.disabled = true;
    form.requestSubmit(pending);
  });
  modal.addEventListener('hidden.bs.modal', () => {
    if (approved) return;
    check.checked = false;
    confirm.disabled = true;
    if (pending) pending.focus();
    pending = null;
  });
})();
