(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('sb-user-guide-modal');
    const link = document.getElementById('sb-user-guide-link');
    const pending = document.getElementById('sb-user-guide-pending');
    const status = document.getElementById('sb-user-guide-status');
    const badge = document.getElementById('sb-user-guide-badge');
    if (!modal || !link || !pending || !status || !badge) return;

    modal.addEventListener('show.bs.modal', async function () {
      link.hidden = true;
      link.removeAttribute('href');
      pending.hidden = false;
      badge.textContent = '준비 중';
      status.textContent = '사용자 가이드 PDF를 준비하고 있습니다. 등록 후 여기에서 열 수 있습니다.';
      try {
        const response = await fetch(link.dataset.guideUrl, {
          method: 'HEAD',
          cache: 'no-store',
          signal: AbortSignal.timeout(5000)
        });
        const contentType = response.headers.get('Content-Type') || '';
        if (!response.ok || !contentType.toLowerCase().includes('application/pdf')) return;
        link.href = link.dataset.viewerUrl;
        link.hidden = false;
        pending.hidden = true;
        badge.textContent = '샘플 PDF';
        status.textContent = '샘플 가이드를 새 탭의 PDF 뷰어에서 확인할 수 있습니다.';
      } catch (error) {
        // Missing files and network failures keep the preparation message visible.
      }
    });
  });
})();
