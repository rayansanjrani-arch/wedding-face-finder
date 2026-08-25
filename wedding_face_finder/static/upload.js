(function() {
  'use strict';

  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');
  const previewGrid = document.getElementById('previewGrid');
  const progressWrap = document.getElementById('uploadProgress');
  const progressText = document.getElementById('progressText');
  const progressPercent = document.getElementById('progressPercent');
  const progressFill = document.getElementById('progressFill');
  const continueBtn = document.getElementById('continueBtn');
  const cameraBtn = document.getElementById('cameraBtn');
  const cameraContainer = document.getElementById('cameraContainer');
  const cameraVideo = document.getElementById('cameraVideo');
  const shutterBtn = document.getElementById('shutterBtn');
  const cameraCanvas = document.getElementById('cameraCanvas');

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const filesQueue = [];
  let uploadedCount = 0;
  let totalCount = 0;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
    uploadZone.addEventListener(evt, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(evt => {
    uploadZone.addEventListener(evt, () => uploadZone.classList.add('dragover'), false);
  });

  ['dragleave', 'drop'].forEach(evt => {
    uploadZone.addEventListener(evt, () => uploadZone.classList.remove('dragover'), false);
  });

  uploadZone.addEventListener('drop', handleDrop, false);
  fileInput.addEventListener('change', handleFiles, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    handleFiles({ target: { files: dt.files } });
  }

  function handleFiles(e) {
    const files = Array.from(e.target.files).filter(f => f.type.startsWith('image/'));
    if (!files.length) return;

    files.forEach(file => {
      if (file.size > 1024 * 1024) {
        compressImage(file, 1920, 0.85).then(blob => {
          filesQueue.push({ original: file, blob: blob, name: file.name });
          addPreview(blob, file.name);
        });
      } else {
        filesQueue.push({ original: file, blob: file, name: file.name });
        addPreview(file, file.name);
      }
    });

    previewGrid.style.display = 'grid';
    continueBtn.disabled = false;
  }

  function compressImage(file, maxWidth, quality) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const scale = Math.min(1, maxWidth / img.width);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(resolve, 'image/jpeg', quality);
      };
      img.src = URL.createObjectURL(file);
    });
  }

  function addPreview(blobOrFile, name) {
    const url = URL.createObjectURL(blobOrFile);
    const div = document.createElement('div');
    div.className = 'preview-item';
    div.innerHTML = `
      <img src="${url}" alt="${escapeHtml(name)}">
      <div class="preview-item-status" id="status-${escapeHtml(name)}">Pending</div>
    `;
    previewGrid.appendChild(div);
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  continueBtn.addEventListener('click', async () => {
    if (!filesQueue.length) return;
    continueBtn.disabled = true;
    progressWrap.style.display = 'block';
    totalCount = filesQueue.length;
    uploadedCount = 0;

    for (const item of filesQueue) {
      const formData = new FormData();
      formData.append('photos', item.blob, item.name);

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          body: formData
        });
        if (res.ok) {
          uploadedCount++;
          updateProgress();
          markStatus(item.name, 'done');
        } else {
          markStatus(item.name, 'error');
        }
      } catch (err) {
        markStatus(item.name, 'error');
      }
    }

    if (uploadedCount > 0) {
      window.location.href = '/search';
    } else {
      continueBtn.disabled = false;
    }
  });

  function updateProgress() {
    const pct = Math.round((uploadedCount / totalCount) * 100);
    progressText.textContent = `Uploading ${uploadedCount} of ${totalCount}...`;
    progressPercent.textContent = `${pct}%`;
    progressFill.style.width = `${pct}%`;
  }

  function markStatus(name, state) {
    const el = document.getElementById(`status-${name}`);
    if (!el) return;
    el.textContent = state === 'done' ? 'Done' : 'Failed';
    el.className = `preview-item-status ${state}`;
  }

  let stream = null;
  cameraBtn.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      cameraVideo.srcObject = stream;
      cameraContainer.style.display = 'block';
      cameraBtn.style.display = 'none';
    } catch (err) {
      alert('Could not access camera. Please ensure permissions are granted.');
    }
  });

  shutterBtn.addEventListener('click', () => {
    const ctx = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    ctx.drawImage(cameraVideo, 0, 0);
    
    cameraCanvas.toBlob(async (blob) => {
      if (stream) stream.getTracks().forEach(t => t.stop());
      cameraContainer.style.display = 'none';
      const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
      filesQueue.push({ original: file, blob: file, name: file.name });
      addPreview(file, file.name);
      previewGrid.style.display = 'grid';
      continueBtn.disabled = false;
      continueBtn.click();
    }, 'image/jpeg', 0.9);
  });

})();