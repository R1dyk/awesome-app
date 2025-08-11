
const { contextBridge, ipcRenderer } = require('electron');

// Attach window control button listeners after DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
  const minButton = document.getElementById('min-button');
  const maxButton = document.getElementById('max-button');
  const restoreButton = document.getElementById('restore-button');
  const closeButton = document.getElementById('close-button');

  if (minButton) minButton.addEventListener('click', () => ipcRenderer.send('window-minimize'));
  if (maxButton) maxButton.addEventListener('click', () => ipcRenderer.send('window-maximize'));
  if (restoreButton) restoreButton.addEventListener('click', () => ipcRenderer.send('window-maximize'));
  if (closeButton) closeButton.addEventListener('click', () => ipcRenderer.send('window-close'));
});

// Listen for window state changes from main process
ipcRenderer.on('window-maximized', () => {
  document.body.classList.add('maximized');
});
ipcRenderer.on('window-unmaximized', () => {
  document.body.classList.remove('maximized');
});

contextBridge.exposeInMainWorld('api', {
  // Existing API
  connectToServer: (data) => ipcRenderer.invoke('connect-to-server', data),
  setUsername: (name) => ipcRenderer.invoke('set-username', name),
  sendAlert: (type) => ipcRenderer.invoke('send-alert', type),
  sendCustom: (data) => ipcRenderer.invoke('send-custom', data),
  setTarget: (id) => ipcRenderer.invoke('set-target', id),
  requestClientList: () => ipcRenderer.invoke('request-client-list'),
  onUpdateStatus: (cb) => ipcRenderer.on('update-status', cb),
  onUpdateCounters: (cb) => ipcRenderer.on('update-counters', cb),
  onUpdateClientList: (cb) => ipcRenderer.on('update-client-list', cb),
  showAlert: (cb) => ipcRenderer.on('show-alert', cb),
  removeAll: (channel) => ipcRenderer.removeAllListeners(channel),
  // Login/Dev/IPC helpers
  loginAttempt: (data) => ipcRenderer.invoke('login-attempt', data),
  loginSuccess: () => ipcRenderer.send('login-success'),
  send: (channel, ...args) => ipcRenderer.send(channel, ...args)
});