import requests
import schedule
import time
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Bot
from telegram.error import TelegramError
import tradingeconomics as te  # pip install tradingeconomics

# ==================== إعداداتك ====================
BOT_TOKEN = '8553390029:AAEQD823nUDAykMCpPscymAw-zXHK3-kLI8'  # من BotFather
CHANNEL_ID = '@falconpips'  # اسم القناة
TE_LOGIN = 'guest'  # Trading Economics demo
TE_PASSWORD = 'guest'

bot = Bot(token=BOT_TOKEN)
utc = pytz.UTC

# لوحة تحكم الجلسات الاحترافية
sessions = {
    'Sydney': {'open': '22:00', 'close': '07:00', 'emoji': '🇦🇺', 'volatility': 'منخفضة'},
    'Tokyo': {'open': '00:00', 'close': '09:00', 'emoji': '🇯🇵', 'volatility': 'متوسطة'},
    'London': {'open': '08:00', 'close': '17:00', 'emoji': '🇬🇧', 'volatility': 'عالية'},
    'NewYork': {'open': '13:00', 'close': '22:00', 'emoji': '🇺🇸', 'volatility': 'عالية جداً'}
}

# أخبار مهمة للذهب (USD-focused)
gold_events_keywords = {
    'نفيج (NFP)': ['Non-Farm', 'Employment', 'Unemployment', 'Payrolls'],
    'تضخم (CPI)': ['CPI', 'Inflation', 'Consumer Price'],
    'فيدرالي (FOMC)': ['FOMC', 'Fed', 'Interest Rate', 'Federal Funds'],
    'زراعي': ['Farm', 'Agriculture', 'Crop'],
    'سيولة': ['Liquidity', 'M2', 'Money Supply']
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def send_pro_message(text):
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
        logger.info("✅ رسالة مرسلة بنجاح")
    except TelegramError as e:
        logger.error(f"❌ خطأ Telegram: {e}")

te.login(TE_LOGIN, TE_PASSWORD)

def notify_sessions():
    """إشعارات جلسات مع تداخل احترافي"""
    now_str = datetime.now(utc).strftime('%H:%M')
    active_sessions = []
    
    for name, data in sessions.items():
        open_time = data['open']
        if open_time <= now_str or (now_str < data['close'][:2] + ':00' if len(data['close']) > 3 else False):
            active_sessions.append(f"{data['emoji']} {name}")
    
    if len(active_sessions) >= 2:
        overlap_msg = f"🔥 <b>تداخل جلسات قوي!</b>\n{', '.join(active_sessions)}\nالسيولة {sessions['London']['volatility']} - وقت الدخول على الذهب! 💰📈\n#FalconPips #جلسات"
        send_pro_message(overlap_msg)
    elif active_sessions:
        session = active_sessions[0]
        msg = f"{sessions[session.split()[1]]['emoji']} <b>🚀 جلسة {session.split()[1]} مفتوحة!</b>\nالتقلبات: {sessions[session.split()[1]]['volatility']}\nراقب XAU/USD 🪙\n#ذهب #FalconPips"
        send_pro_message(msg)

def get_usd_events():
    """جلب أحداث USD المهمة من Trading Economics"""
    try:
        # جلب كالندر اليوم + غداً
        calendar = te.getCalendarData(days_ahead=2, country='United States')
        return calendar
    except Exception as e:
        logger.error(f"خطأ API: {e}")
        return []

def analyze_gold_impact(event_title):
    """تحليل تأثير على الذهب"""
    title_lower = event_title.lower()
    for impact_type, keywords in gold_events_keywords.items():
        for kw in keywords:
            if kw.lower() in title_lower:
                return f"<b>{impact_type}</b> - سلبي للذهب إذا قوي الدولار 📉"
    return "حدث عام - راقب الدولار 🧐"

def check_news_30min():
    """فحص الأخبار قبل 30 دقيقة"""
    events = get_usd_events()
    now = datetime.now(utc)
    
    for event in events:
        try:
            event_time = datetime.strptime(event.get('Date', ''), '%Y-%m-%dT%H:%M:%S')  # تعديل حسب الـ format
            event_time = utc.localize(event_time) if event_time.tzinfo is None else event_time
            
            time_diff = (event_time - now).total_seconds() / 60
            
            if 25 <= time_diff <= 35:  # 25-35 دقيقة قبل
                impact = analyze_gold_impact(event.get('Event', ''))
                msg = f"""⚠️ <b>🚨 تنبيه VIP: خبر عالي التأثير قبل 30 دقيقة!</b>

📊 <b>{event.get('Event', 'غير معروف')}</b>
⏰ التوقيت: {event_time.strftime('%H:%M UTC')}
🌍 الدولة: {event.get('Country', 'USA')}
📉 <b>التأثير على الذهب:</b> {impact}

💡 نصيحة Falcon: أغلق الصفقات أو قلل الرافعة!
#ذهب #XAUUSD #NFP #CPI #FalconPips"""
                send_pro_message(msg)
        except Exception as e:
            continue

# ==================== الجدولة الاحترافية ====================
schedule.every().minute.do(notify_sessions)
schedule.every(3).minutes.do(check_news_30min)  # كل 3 دقائق فحص

# رسالة البداية الـ VIP
def startup_msg():
    send_pro_message("""
🤖 <b>🚀 Falcon Pips Pro Bot مفعل!</b>

✅ إشعارات جلسات 24/7 مع تداخل
✅ تنبيهات أخبار USD قبل 30 دقيقة
✅ تحليل تأثير على الذهب XAU/USD
✅ مصدر: Trading Economics Premium

💎 VIP Mode: Active | #FalconPips
    """)

startup_msg()

# حلقة التشغيل الدائمة مع إعادة تشغيل
while True:
    try:
        schedule.run_pending()
        time.sleep(60)  # دقيقة كاملة
    except Exception as e:
        logger.error(f"خطأ عام: {e}")

        time.sleep(300)  # 5 دقائق ثم إعادة
