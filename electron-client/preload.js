const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
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
  removeAll: (channel) => ipcRenderer.removeAllListeners(channel)
});