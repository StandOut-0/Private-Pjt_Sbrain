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

  // Drag and drop resizer functionality
  const resizer = document.getElementById('sb-artifact-resizer');
  const artifactTree = document.querySelector('.sb-artifact-tree');
  const artifactViewer = document.querySelector('.sb-artifact-viewer');

  // Keep the file list's scrolling height matched to the preview box.
  if (viewer) {
    const syncTreeHeight = function () {
      const height = viewer.getBoundingClientRect().height;
      if (height > 0) tree.style.setProperty('--sb-tree-max-height', height + 'px');
    };
    syncTreeHeight();
    if (typeof ResizeObserver !== 'undefined') {
      const viewerObserver = new ResizeObserver(syncTreeHeight);
      viewerObserver.observe(viewer);
    } else {
      window.addEventListener('resize', syncTreeHeight);
    }
  }

  if (resizer && artifactTree && artifactViewer) {
    let isResizing = false;

    resizer.addEventListener('mousedown', function(e) {
      isResizing = true;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function(e) {
      if (!isResizing) return;

      const containerRect = artifactTree.parentElement.getBoundingClientRect();
      const newTreeWidth = e.clientX - containerRect.left;
      const containerWidth = containerRect.width;

      // Calculate the three grid columns: tree, resizer, viewer.
      const treePercentage = (newTreeWidth / containerWidth) * 100;

      // Set minimum and maximum limits
      if (treePercentage >= 20 && treePercentage <= 60) {
        const viewerPercentage = 100 - treePercentage;
        artifactTree.parentElement.style.gridTemplateColumns = treePercentage + '% 8px calc(' + viewerPercentage + '% - 8px)';
      }
    });

    document.addEventListener('mouseup', function() {
      if (isResizing) {
        isResizing = false;
        resizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });
  }
});
