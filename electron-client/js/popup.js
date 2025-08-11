document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('popup-container');
  const messageEl = document.getElementById('message');
  const canvas = document.getElementById('bg-canvas');
  const ctx = canvas.getContext('2d');
  const okBtn = document.getElementById('ok-btn');
  const xBtn = document.getElementById('popup-x-btn');
  // Add a background <img> for the gif
  let bgImg = document.getElementById('popup-bg-img');
  if (!bgImg) {
    bgImg = document.createElement('img');
    bgImg.id = 'popup-bg-img';
    bgImg.style.position = 'absolute';
    bgImg.style.top = '0';
    bgImg.style.left = '0';
    bgImg.style.width = '100%';
    bgImg.style.height = '100%';
    bgImg.style.maxWidth = '100%';
    bgImg.style.maxHeight = '100%';
    bgImg.style.objectFit = 'cover';
    bgImg.style.zIndex = '0';
    bgImg.style.pointerEvents = 'none';
    bgImg.style.aspectRatio = 'auto';
    bgImg.style.display = 'block';
    bgImg.style.transition = 'width 0.2s, height 0.2s';
    // Responsive on resize
    window.addEventListener('resize', () => {
      bgImg.style.width = '100%';
      bgImg.style.height = '100%';
    });
    container.prepend(bgImg);
    // Ensure container is position:relative and hides overflow
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    // Also ensure body and html do not scroll
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    // Move canvas above image
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '1';
    // Message and button above all
    messageEl.style.position = 'relative';
    messageEl.style.zIndex = '2';
    okBtn.style.position = 'relative';
    okBtn.style.zIndex = '2';
  }

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', () => {
    resizeCanvas();
    if (currentImg) drawCoverImage(currentImg);
  });

  let currentImg = null;

  api.showAlert((event, info) => {
    container.style.backgroundColor = info.bg || '#333';
  // Render message with line breaks
  messageEl.innerHTML = (info.message || '').replace(/\n/g, '<br>');
    resizeCanvas();
    currentImg = null;
    // Set gif as background image
    if (info.gif_url) {
      bgImg.src = info.gif_url;
      bgImg.style.display = '';
    } else {
      bgImg.src = '';
      bgImg.style.display = 'none';
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const lower = (info.message || '').toLowerCase();
    if (lower.includes('freezing') || lower.includes('cold')) {
      animateSnow(canvas, ctx);
    }
  });

  okBtn.addEventListener('click', () => window.close());

  // Add event listener for X button to close the window
  if (xBtn) {
    xBtn.addEventListener('click', () => window.close());
  }

  function drawCoverImage(img) {
    const cw = canvas.width, ch = canvas.height;
    const ir = img.width / img.height;
    const cr = cw / ch;
    let dw, dh;
    if (cr > ir) { // canvas wider
      dw = cw; dh = cw / ir;
    } else { // canvas taller
      dh = ch; dw = ch * ir;
    }
    const dx = (cw - dw) / 2;
    const dy = (ch - dh) / 2;
    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, dx, dy, dw, dh);
  }

  function animateSnow(canvas, ctx) {
    const snowflakes = [];
    for (let i = 0; i < 60; i++) {
      snowflakes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 3 + 2,
        speed: Math.random() * 2 + 1
      });
    }
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      snowflakes.forEach(flake => {
        ctx.beginPath();
        ctx.arc(flake.x, flake.y, flake.size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.fill();
        flake.y += flake.speed;
        if (flake.y - flake.size > canvas.height) flake.y = -flake.size;
        flake.x += Math.random() - 0.5;
      });
      requestAnimationFrame(draw);
    }
    draw();
  }
});