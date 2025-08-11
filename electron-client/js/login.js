// login.js - Handles login page button actions for Awesome App
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const devBtn = document.querySelector('.dev-mode-btn');
  const registerBtn = document.getElementById('register-btn');

  // Login button (form submit)
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    alert('Login is not implemented yet.');
    // await window.api.loginAttempt({ username, password, dev: false });
    // window.api.loginSuccess();
  });

  // Dev Mode: Proceeds to main screen regardless of inputs
  devBtn.addEventListener('click', async () => {
  await window.api.loginAttempt({ username: 'dev', password: '', dev: true });
  window.api.loginSuccess();
  });

  // Register button (dummy)
  registerBtn.addEventListener('click', () => {
    alert('Register is not implemented yet.');
  });
});
