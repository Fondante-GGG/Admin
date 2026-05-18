document.addEventListener("DOMContentLoaded", function () {
  const widget = document.querySelector(".chat-widget");
  if (!widget) {
    return;
  }

  const endpoint = widget.dataset.chatEndpoint;
  const toggle = widget.querySelector(".chat-widget__toggle");
  const panel = widget.querySelector(".chat-widget__panel");
  const closeButton = widget.querySelector(".chat-widget__close");
  const messages = widget.querySelector(".chat-widget__messages");
  const form = widget.querySelector(".chat-widget__form");
  const textarea = form.querySelector('textarea[name="message"]');
  const nameInput = widget.querySelector('.chat-widget__meta input[name="name"]');
  const phoneInput = widget.querySelector('.chat-widget__meta input[name="phone"]');
  const submitButton = form.querySelector(".chat-widget__send");
  const quickButtons = widget.querySelectorAll("[data-quick-message]");

  function getCookie(name) {
    const cookieValue = document.cookie
      .split(";")
      .map(function (item) {
        return item.trim();
      })
      .find(function (item) {
        return item.startsWith(name + "=");
      });

    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
  }

  function scrollMessages() {
    messages.scrollTop = messages.scrollHeight;
  }

  function openPanel() {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    widget.classList.add("chat-widget--open");
    window.setTimeout(function () {
      textarea.focus();
      scrollMessages();
    }, 60);
  }

  function closePanel() {
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    widget.classList.remove("chat-widget--open");
  }

  function appendBubble(text, type) {
    const bubble = document.createElement("div");
    bubble.className = "chat-widget__bubble chat-widget__bubble--" + type;
    bubble.textContent = text;
    messages.appendChild(bubble);
    scrollMessages();
  }

  async function sendMessage(message) {
    appendBubble(message, "user");
    textarea.value = "";
    submitButton.disabled = true;
    submitButton.textContent = "Отправка...";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({
          message: message,
          name: nameInput.value.trim(),
          phone: phoneInput.value.trim()
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Ошибка отправки");
      }

      appendBubble(
        data.reply || "Ваше сообщение получено. Менеджер увидит его в лидах.",
        "bot"
      );
    } catch (error) {
      appendBubble(
        "Не удалось отправить сообщение. Попробуйте еще раз или оставьте заявку через форму ниже на странице.",
        "bot"
      );
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Отправить";
      textarea.focus();
    }
  }

  toggle.addEventListener("click", function () {
    if (panel.hidden) {
      openPanel();
      return;
    }
    closePanel();
  });

  closeButton.addEventListener("click", closePanel);

  quickButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const message = button.dataset.quickMessage;
      if (!message) {
        return;
      }
      if (panel.hidden) {
        openPanel();
      }
      sendMessage(message);
    });
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const message = textarea.value.trim();
    if (!message) {
      textarea.focus();
      return;
    }
    if (panel.hidden) {
      openPanel();
    }
    sendMessage(message);
  });

  textarea.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
});
