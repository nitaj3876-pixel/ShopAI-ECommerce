function renderChatbot() {
  if (document.getElementById("chatbot-toggle")) return;

  const toggle = document.createElement("button");
  toggle.id = "chatbot-toggle";
  toggle.innerHTML = "💬";
  toggle.onclick = () => {
    const win = document.getElementById("chatbot-window");
    win.classList.toggle("open");
  };
  document.body.appendChild(toggle);

  const win = document.createElement("div");
  win.id = "chatbot-window";
  win.innerHTML = `
    <div id="chatbot-header">🤖 ShopAI Assistant</div>
    <div id="chatbot-messages"></div>
    <div id="chatbot-input-row">
      <input type="text" id="chatbot-input" placeholder="Ask me anything...">
      <button onclick="sendChatMessage()">➤</button>
    </div>`;
  document.body.appendChild(win);

  document.getElementById("chatbot-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage();
  });

  addChatBubble("Hi! 👋 I'm your ShopAI assistant. Ask me to find a product, or ask about orders, returns, shipping or payments.", "bot");
}

function addChatBubble(text, who, productsHtml = "") {
  const messages = document.getElementById("chatbot-messages");
  const row = document.createElement("div");
  row.className = "chat-row";
  row.innerHTML = `<div class="chat-bubble ${who}">${text}${productsHtml}</div>`;
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById("chatbot-input");
  const message = input.value.trim();
  if (!message) return;
  addChatBubble(message, "user");
  input.value = "";

  try {
    const res = await Api.chat(message);
    let productsHtml = "";
    if (res.products && res.products.length) {
      productsHtml = `<div class="mt-2 d-flex flex-column gap-2">` + res.products.slice(0, 4).map(p => `
        <a href="product_details.html?id=${p.id}" class="d-flex align-items-center gap-2 text-decoration-none text-dark border rounded p-1">
          <img src="${firstImage(p.image_urls)}" style="width:36px;height:36px;object-fit:cover;border-radius:6px">
          <div>
            <div class="small fw-semibold">${p.name}</div>
            <div class="small text-muted">${formatCurrency(p.price)}</div>
          </div>
        </a>`).join("") + `</div>`;
    }
    addChatBubble(res.reply, "bot", productsHtml);
  } catch (err) {
    addChatBubble("Sorry, I ran into an issue reaching the server. Please try again.", "bot");
  }
}

document.addEventListener("DOMContentLoaded", renderChatbot);
