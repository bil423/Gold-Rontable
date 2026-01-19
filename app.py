import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب التمويل (5000$)
ACCOUNT_SIZE = 5000.0
RISK_PER_TRADE_USD = 25.0 # مخاطرة 0.5% ثابتة

st.set_page_config(page_title="Funded Sniper Dashboard", page_icon="🔔", layout="wide")

# --- 1. نظام الذاكرة والسجل (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = []

def add_signal_to_log(signal_type, price):
    now = datetime.datetime.now(pytz.timezone('Africa/Algiers'))
    time_str = now.strftime("%H:%M:%S")
    
    # منع تكرار نفس الإشارة في نفس الدقيقة لضمان نظافة السجل
    if not st.session_state.history or st.session_state.history[0]['الوقت'][:-3] != time_str[:-3]:
        new_entry = {
            "الوقت": time_str,
            "نوع الإشارة": signal_type,
            "السعر": f"${price:,.2f}"
        }
        st.session_state.history.insert(0, new_entry) # إضافة الأحدث في الأعلى
        # --- إضافة التنبيه المرئي (Toast) ---
        st.toast(f"🔔 إشارة {signal_type} جديدة عند {price:,.2f}", icon='🔥')

# --- 2. محرك التحليل الفني ---
def analyze_market(df):
    if df is None or len(df) < 30: return None, None
    try:
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        # شروط Premium (جودة عالية)
        if lp > lma and lrsi > 62: return "Premium BUY 🚀", lp
        if lp < lma and lrsi < 38: return "Premium SELL 📉", lp
        return "صبر 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def fetch_data(inv, per):
    try:
        d = yf.download("GC=F", period=per, interval=inv, progress=False)
        return d if not d.empty else None
    except: return None

# --- 3. الواجهة الرئيسية الرئيسية ---
st.title("🛡️ رادار التمويل: لوحة قيادة الإشارات")

d1h, d15m = fetch_data("1h", "5d"), fetch_data("15m", "2d")
t1h, price = analyze_market(d1h)
t15m, _ = analyze_market(d15m)

if price:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    
    # منطق الإشارة المباشرة والتنبيه
    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success(f"🎯 إشارة نشطة: {t1h}")
        add_signal_to_log(t1h, price) # استدعاء نظام الحفظ والتنبيه
        
        sl_pts = 4.0
        lot_size = RISK_PER_TRADE_USD / (sl_pts * 10)
        st.info(f"📏 لوت التداول: {lot_size:.2f} | 🛑 وقف الخسارة: {price-4 if 'BUY' in t1h else price+4:.2f}")
    else:
        st.warning("🔎 يراقب السوق.. لم تكتمل شروط 'Premium' (الجودة العالية) بعد.")

st.divider()

# --- 4. لوحة أرشيف الإشارات (Dashboard) ---
st.subheader("📜 سجل إشارات الجلسة (Archive)")
if st.session_state.history:
    # عرض السجل في جدول أنيق
    st.table(pd.DataFrame(st.session_state.history))
    if st.button("🗑️ مسح سجل الإشارات"):
        st.session_state.history = []
        st.rerun()
else:
    st.write("لم يتم رصد إشارات متوافقة اليوم حتى الآن. الروبوت يرفض الدخول في التذبذب.")

# معلومات جانبية
st.sidebar.write(f"🌍 توقيت الجزائر: {datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime('%H:%M:%S')}")
st.sidebar.write(f"🔒 حماية الحساب: $25 مخاطرة/صفقة")
