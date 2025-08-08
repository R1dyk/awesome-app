const { api } = window;

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('popup-container');
  const messageEl = document.getElementById('message');
  const canvas = document.getElementById('bg-canvas');
  const ctx = canvas.getContext('2d');
  const okBtn = document.getElementById('ok-btn');

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
    messageEl.textContent = info.message;
    resizeCanvas();
    currentImg = null;
    if (info.gif_url) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = info.gif_url;
      img.onload = () => {
        currentImg = img;
        drawCoverImage(img);
      };
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    const lower = (info.message || '').toLowerCase();
    if (lower.includes('freezing') || lower.includes('cold')) {
      animateSnow(canvas, ctx);
    }
  });

  okBtn.addEventListener('click', () => window.close());

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
      // Do not clear image; draw only snow
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