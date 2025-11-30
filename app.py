from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    client = OpenAI(api_key=api_key)

app = FastAPI(title="KURNAZ Spor Chatbot")

SYSTEM_PROMPT = """
Senin adın KURNAZ. Türkçe konuşan, esprili ama güvenilir bir spor uzmanı asistansın.
Önceliğin spor konuları: futbol, basketbol, tenis, antrenman, kondisyon, sporcu istatistikleri.

Kurallar:
- Bilmediğin şeylerde uydurma, emin değilsen bunu söyle.
- Görüş belirtirken "bana göre" demeyi unutma.
- Kısa ve net cevap ver, detay istenince genişlet.
- Tıbbi konularda kesin tavsiye verme, uzman yönlendirmesi yap.
- Kişilik: samimi, hafif şakacı, bilgili.
"""

class Msg(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KURNAZ - Spor Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 5px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            justify-content: flex-end;
        }
        .message.bot {
            justify-content: flex-start;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        #messageInput:focus {
            border-color: #667eea;
        }
        #sendButton {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #sendButton:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        #sendButton:active {
            transform: translateY(0);
        }
        #sendButton:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            display: none;
            padding: 12px 16px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            max-width: 70px;
        }
        .loading.show {
            display: block;
        }
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ KURNAZ</h1>
            <p>Spor Uzmanı Asistanınız</p>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message bot">
                <div class="message-content">
                    Merhaba! Ben KURNAZ. Spor hakkında sorularınızı sorabilirsiniz. Futbol, basketbol, tenis, antrenman ve daha fazlası hakkında konuşabiliriz!
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Mesajınızı yazın..." autocomplete="off">
            <button id="sendButton" onclick="sendMessage()">Gönder</button>
        </div>
        <div class="loading" id="loading"></div>
    </div>
    <script>
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loading = document.getElementById('loading');

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage('user', message);
            messageInput.value = '';
            sendButton.disabled = true;
            loading.classList.add('show');
            loading.scrollIntoView({ behavior: 'smooth' });

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Sunucu hatası');
                }

                const data = await response.json();
                loading.classList.remove('show');
                addMessage('bot', data.reply);
            } catch (error) {
                loading.classList.remove('show');
                const errorMsg = error.message || 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';
                addMessage('bot', `Hata: ${errorMsg}`);
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        function addMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            messageDiv.appendChild(contentDiv);
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    </script>
</body>
</html>
    """

@app.post("/chat")
async def chat(req: Msg):
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API anahtarı ayarlanmamış. Lütfen OPENAI_API_KEY environment variable'ını ayarlayın."
        )
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message}
        ]
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.2
        )

        answer = resp.choices[0].message.content

        return {"bot": "KURNAZ", "reply": answer}
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise HTTPException(status_code=500, detail="OpenAI API anahtarı geçersiz. Lütfen OPENAI_API_KEY'i kontrol edin.")
        raise HTTPException(status_code=500, detail=f"OpenAI API hatası: {error_msg}")

