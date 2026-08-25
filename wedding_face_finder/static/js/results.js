(function() {
  'use strict';

  const grid = document.getElementById('resultsGrid');
  const emptyState = document.getElementById('emptyState');
  const matchCount = document.getElementById('matchCount');
  const downloadBar = document.getElementById('downloadBar');
  const selectedCount = document.getElementById('selectedCount');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const cancelDownloadBtn = document.getElementById('cancelDownloadBtn');
  const selectAllBtn = document.getElementById('selectAllBtn');
  const clearSelectionBtn = document.getElementById('clearSelectionBtn');

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  let selectedIds = new Set();

  const mockMatches = [
    { id: 'p1', url: 'https://images.unsplash.com/photo-1519741497674-611481863552?w=400&q=80', confidence: 0.96 },
    { id: 'p2', url: 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=400&q=80', confidence: 0.91 },
    { id: 'p3', url: 'https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=400&q=80', confidence: 0.88 },
    { id: 'p4', url: 'https://images.unsplash.com/photo-1522673607200-164d1b6ce486?w=400&q=80', confidence: 0.85 },
    { id: 'p5', url: 'https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?w=400&q=80', confidence: 0.82 },
    { id: 'p6', url: 'https://images.unsplash.com/photo-1460978812857-470ed1c77af0?w=400&q=80', confidence: 0.78 },
    { id: 'p7', url: 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=400&q=80', confidence: 0.95 },
    { id: 'p8', url: 'https://images.unsplash.com/photo-1519741497674-611481863552?w=400&q=80', confidence: 0.72 },
  ];

  function init() {
    renderMatches(mockMatches);
  }

  function renderMatches(matches) {
    grid.innerHTML = '';
    if (!matches || !matches.length) {
      emptyState.style.display = 'block';
      matchCount.textContent = '0';
      return;
    }
    emptyState.style.display = 'none';
    matchCount.textContent = matches.length;

    matches.forEach(match => {
      const item = document.createElement('div');
      item.className = 'masonry-item';
      item.dataset.id = match.id;
      
      const badgeClass = match.confidence >= 0.9 ? 'confidence-high' : match.confidence >= 0.75 ? 'confidence-med' : 'confidence-low';
      const pct = Math.round(match.confidence * 100);

      item.innerHTML = `
        <img src="${match.url}" alt="Match" loading="lazy">
        <div class="select-check">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <div class="masonry-overlay">
          <span class="masonry-confidence">
            <span class="confidence-badge ${badgeClass}">${pct}% match</span>
          </span>
        </div>
      `;

      item.addEventListener('click', () => toggleSelection(item, match.id));
      grid.appendChild(item);
    });
  }

  function toggleSelection(item, id) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
      item.classList.remove('selected');
    } else {
      selectedIds.add(id);
      item.classList.add('selected');
    }
    updateDownloadBar();
  }

  function updateDownloadBar() {
    const count = selectedIds.size;
    selectedCount.textContent = `${count} selected`;
    downloadBar.classList.toggle('visible', count > 0);
  }

  selectAllBtn.addEventListener('click', () => {
    document.querySelectorAll('.masonry-item').forEach(item => {
      const id = item.dataset.id;
      if (!selectedIds.has(id)) {
        selectedIds.add(id);
        item.classList.add('selected');
      }
    });
    updateDownloadBar();
  });

  clearSelectionBtn.addEventListener('click', () => {
    selectedIds.clear();
    document.querySelectorAll('.masonry-item.selected').forEach(item => item.classList.remove('selected'));
    updateDownloadBar();
  });

  cancelDownloadBtn.addEventListener('click', () => {
    selectedIds.clear();
    document.querySelectorAll('.masonry-item.selected').forEach(item => item.classList.remove('selected'));
    updateDownloadBar();
  });

  downloadZipBtn.addEventListener('click', async () => {
    if (selectedIds.size === 0) return;
    downloadZipBtn.disabled = true;
    downloadZipBtn.innerHTML = `<div class="spinner"></div> Building ZIP...`;

    try {
      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ photo_ids: Array.from(selectedIds) })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'wedding-matches.zip';
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert('Download failed. Please try again.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    } finally {
      downloadZipBtn.disabled = false;
      downloadZipBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" x2="12" y1="15" y2="3"/>
        </svg>
        Download ZIP
      `;
    }
  });

  init();

})();