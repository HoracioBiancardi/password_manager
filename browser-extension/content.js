// Content script to perform auto-fill and auto-detect on web page input elements

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fill_credentials') {
    const filled = performFill(request.user, request.pass);
    sendResponse({ success: filled });
  } else if (request.action === 'detect_credentials') {
    const detected = detectCredentials();
    sendResponse(detected);
  }
  return true; // Keep message channel open for async response
});

function performFill(username, password) {
  const passwordInputs = document.querySelectorAll('input[type="password"]');
  if (!passwordInputs.length) {
    return false;
  }

  const triggerEvents = (element) => {
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  };

  passwordInputs.forEach(input => {
    input.value = password;
    triggerEvents(input);
  });

  const allInputs = Array.from(document.querySelectorAll('input'));
  const firstPasswordIndex = allInputs.findIndex(input => input.type === 'password');

  if (firstPasswordIndex !== -1) {
    let usernameInput = null;
    for (let i = firstPasswordIndex - 1; i >= 0; i--) {
      const input = allInputs[i];
      const type = input.type.toLowerCase();
      if ((type === 'text' || type === 'email' || type === 'tel' || !input.hasAttribute('type')) && 
          input.offsetWidth > 0 && input.offsetHeight > 0) {
        usernameInput = input;
        break;
      }
    }

    if (!usernameInput) {
      usernameInput = document.querySelector('input[type="email"], input[type="text"]');
    }

    if (usernameInput) {
      usernameInput.value = username;
      triggerEvents(usernameInput);
    }
  }

  return true;
}

function detectCredentials() {
  const passwordInputs = document.querySelectorAll('input[type="password"]');
  let passVal = '';
  let userVal = '';

  // Encontra o primeiro campo de senha que contenha valor, ou o primeiro do DOM
  const pwInput = Array.from(passwordInputs).find(input => input.value.trim()) || passwordInputs[0];

  if (pwInput) {
    passVal = pwInput.value;

    const allInputs = Array.from(document.querySelectorAll('input'));
    const pwIndex = allInputs.indexOf(pwInput);

    if (pwIndex !== -1) {
      let usernameInput = null;
      // Procura para trás a partir do campo de senha
      for (let i = pwIndex - 1; i >= 0; i--) {
        const input = allInputs[i];
        const type = input.type.toLowerCase();
        if ((type === 'text' || type === 'email' || type === 'tel' || !input.hasAttribute('type')) && 
            input.offsetWidth > 0 && input.offsetHeight > 0) {
          usernameInput = input;
          break;
        }
      }

      // Se não achar para trás, procura qualquer campo de e-mail ou texto preenchido na página
      if (!usernameInput) {
        usernameInput = Array.from(document.querySelectorAll('input[type="email"], input[type="text"]')).find(input => input.value.trim()) ||
                        document.querySelector('input[type="email"], input[type="text"]');
      }

      if (usernameInput) {
        userVal = usernameInput.value;
      }
    }
  }

  return { user: userVal, pass: passVal };
}
