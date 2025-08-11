  // Back to Login button (if present)
  const backToLoginBtn = document.getElementById('back-to-login-btn');
  if (backToLoginBtn && window.api && window.api.send) {
    backToLoginBtn.addEventListener('click', () => {
      window.api.send('back-to-login');
    });
  }
document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('status');
  const receivedEl = document.getElementById('received-count');
  const sentEl = document.getElementById('sent-count');
  const targetSelect = document.getElementById('target-select');
  const customMsg = document.getElementById('custom-msg');
  const customGif = document.getElementById('custom-gif');
  const devModeChk = document.getElementById('dev-mode');

  window.api.onUpdateStatus((event, msg) => statusEl.textContent = msg);
  window.api.onUpdateCounters((event, { sent, received }) => {
    receivedEl.textContent = `Alerts Received: ${received}`;
    sentEl.textContent = `Alerts Sent: ${sent}`;
  });
  window.api.onUpdateClientList((event, clients) => {
    targetSelect.innerHTML = '<option value="">All Clients</option>';
    clients.forEach(client => {
      const opt = document.createElement('option');
      opt.value = client.id;
      opt.textContent = `${client.username} (ID: ${client.id})`;
      targetSelect.appendChild(opt);
    });
    statusEl.textContent = `Connected clients: ${clients.length}`;
  });

  document.getElementById('connect-btn').addEventListener('click', async () => {
    const res = await window.api.connectToServer({ host: '10.32.73.31', isDev: devModeChk.checked });
    alert(res.message);
    statusEl.textContent = res.message;
    if (res.success) window.api.requestClientList();
  });

  devModeChk.addEventListener('change', async () => {
    // Re-init connection state when toggling dev mode
    const res = await window.api.connectToServer({ host: '10.32.73.31', isDev: devModeChk.checked });
    statusEl.textContent = res.message;
  });

  document.getElementById('set-username').addEventListener('click', async () => {
    const newName = prompt('Enter your username:', 'Anonymous');
    const updated = await window.api.setUsername(newName);
    document.title = `Alert App - ${updated}`;
  });

  document.getElementById('refresh-clients').addEventListener('click', () => window.api.requestClientList());

  targetSelect.addEventListener('change', (e) => window.api.setTarget(e.target.value || null));

  document.getElementById('send-custom').addEventListener('click', () => {
    window.api.sendCustom({ msg: customMsg.value, gif: customGif.value });
    customMsg.value = ''; customGif.value = '';
  });

  document.querySelectorAll('.alert-btn').forEach(btn => {
    btn.addEventListener('click', () => window.api.sendAlert(btn.dataset.type));
  });
});