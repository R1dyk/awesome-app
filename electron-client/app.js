const { api } = window;

document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('status');
  const receivedEl = document.getElementById('received-count');
  const sentEl = document.getElementById('sent-count');
  const targetSelect = document.getElementById('target-select');
  const customMsg = document.getElementById('custom-msg');
  const customGif = document.getElementById('custom-gif');
  const devModeChk = document.getElementById('dev-mode');

  api.onUpdateStatus((event, msg) => statusEl.textContent = msg);
  api.onUpdateCounters((event, { sent, received }) => {
    receivedEl.textContent = `Alerts Received: ${received}`;
    sentEl.textContent = `Alerts Sent: ${sent}`;
  });
  api.onUpdateClientList((event, clients) => {
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
    const res = await api.connectToServer({ host: '10.32.73.31', isDev: devModeChk.checked });
    alert(res.message);
    statusEl.textContent = res.message;
    if (res.success) api.requestClientList();
  });

  devModeChk.addEventListener('change', async () => {
    // Re-init connection state when toggling dev mode
    const res = await api.connectToServer({ host: '10.32.73.31', isDev: devModeChk.checked });
    statusEl.textContent = res.message;
  });

  document.getElementById('set-username').addEventListener('click', async () => {
    const newName = prompt('Enter your username:', 'Anonymous');
    const updated = await api.setUsername(newName);
    document.title = `Alert App - ${updated}`;
  });

  document.getElementById('refresh-clients').addEventListener('click', () => api.requestClientList());

  targetSelect.addEventListener('change', (e) => api.setTarget(e.target.value || null));

  document.getElementById('send-custom').addEventListener('click', () => {
    api.sendCustom({ msg: customMsg.value, gif: customGif.value });
    customMsg.value = ''; customGif.value = '';
  });

  document.querySelectorAll('.alert-btn').forEach(btn => {
    btn.addEventListener('click', () => api.sendAlert(btn.dataset.type));
  });
});