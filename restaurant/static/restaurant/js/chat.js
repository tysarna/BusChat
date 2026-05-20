(() => {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const messagesEl = document.getElementById('chat-messages');
  const typingIndicator = document.getElementById('typing-indicator');

  if (!form) return;

  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  // Submit on Enter, newline on Shift+Enter
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) form.dispatchEvent(new Event('submit'));
    }
  });

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setLoading(on) {
    sendBtn.disabled = on;
    input.disabled = on;
    typingIndicator.classList.toggle('hidden', !on);
    typingIndicator.classList.toggle('flex', on);
    if (on) scrollToBottom();
  }

  function appendUserBubble(text) {
    const div = document.createElement('div');
    div.className = 'flex justify-end mb-2';
    div.innerHTML = `
      <div class="max-w-[85%] md:max-w-[70%] rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed bg-terracotta-light text-gray-800">
        ${escapeHtml(text).replace(/\n/g, '<br>')}
      </div>`;
    messagesEl.insertBefore(div, typingIndicator);
    scrollToBottom();
    return div;
  }

  function appendAssistantBubble() {
    const div = document.createElement('div');
    div.className = 'flex justify-start mb-2';
    div.innerHTML = `
      <div class="max-w-[85%] md:max-w-[70%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed bg-olive-light text-gray-800">
        <div class="text-xs font-bold text-olive mb-1">Zara</div>
        <span class="response-text streaming-bubble"></span>
      </div>`;
    messagesEl.insertBefore(div, typingIndicator);
    scrollToBottom();
    return div.querySelector('.response-text');
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function renderContent(text) {
    // Convert newlines to <br>, preserve basic formatting
    return escapeHtml(text).replace(/\n/g, '<br>');
  }

  function getCsrf() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    // Hide welcome banner on first message
    const banner = document.getElementById('welcome-banner');
    if (banner) banner.remove();

    // Show user message immediately
    appendUserBubble(message);
    input.value = '';
    input.style.height = 'auto';
    setLoading(true);

    // Create assistant bubble
    const responseSpan = appendAssistantBubble();
    setLoading(false); // hide typing dots once bubble appears
    typingIndicator.classList.add('hidden');

    let fullText = '';
    let tokenCount = null;

    try {
      const response = await fetch('/chat/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCsrf(),
        },
        body: new URLSearchParams({ message }),
      });

      if (!response.ok) throw new Error('Request failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6);

          if (data.startsWith('[DONE')) {
            // Extract token count if present: [DONE:123]
            const match = data.match(/\[DONE:(\d+)\]/);
            if (match) tokenCount = parseInt(match[1]);
            responseSpan.classList.remove('streaming-bubble');
            break;
          }

          try {
            const chunk = JSON.parse(data);
            fullText += chunk;
            responseSpan.innerHTML = renderContent(fullText);
            scrollToBottom();
          } catch (_) {
            // non-JSON chunk, ignore
          }
        }
      }
    } catch (err) {
      responseSpan.classList.remove('streaming-bubble');
      responseSpan.innerHTML = 'Sorry, something went wrong. Please try again.';
    }

    // Persist the assistant response
    if (fullText) {
      fetch('/chat/save-response/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        body: JSON.stringify({ content: fullText, tokens: tokenCount }),
      });
    }

    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
    scrollToBottom();
  });

  // Suggestion chip handler
  window.submitChip = (text) => {
    input.value = text;
    input.dispatchEvent(new Event('input'));
    form.dispatchEvent(new Event('submit'));
  };

  // Scroll to bottom on load
  scrollToBottom();
})();
