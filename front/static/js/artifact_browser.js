document.addEventListener('DOMContentLoaded', function () {
  const tree = document.querySelector('[data-sb-tree]');
  if (!tree) return;

  const viewer = document.querySelector('[data-sb-viewer]');
  const title = document.querySelector('[data-sb-viewer-title]');
  const meta = document.querySelector('[data-sb-viewer-meta]');
  let selected = null;

  tree.querySelectorAll('.sb-tree-file').forEach(function (button) {
    button.addEventListener('click', function () {
      tree.querySelectorAll('.sb-tree-file').forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      selected = button.dataset.fileName;

      title.textContent = selected;
      meta.textContent = button.dataset.fileAgent + ' Agent · ' + button.dataset.fileSize + ' · ' + button.dataset.fileUpdated;
      viewer.innerHTML =
        '<i class="bi bi-file-earmark-check fs-1"></i><div>DOCUMENT VIEWER</div><div class="small">' +
        selected +
        '</div><div class="small text-secondary">미리보기는 Backend 연동 후 제공됩니다.</div>';
    });
  });

  document.querySelectorAll('[data-sb-action]').forEach(function (button) {
    button.addEventListener('click', function () {
      const action = button.dataset.sbAction;
      if (action === 'zip') {
        window.sbToast('프로젝트 결과물을 ZIP으로 준비합니다.', 'primary');
        return;
      }
      if (!selected) {
        window.sbToast('먼저 결과물을 선택해주세요.', 'secondary');
        return;
      }
      window.sbToast(selected + (action === 'share' ? ' 공유 링크를 복사했습니다.' : ' 다운로드를 시작합니다.'), 'primary');
    });
  });
});
