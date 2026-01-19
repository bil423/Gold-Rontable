import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# --- الإعدادات الثابتة ---
ACCOUNT_SIZE = 5000.0
RISK_USD = 25.0 

st.set_page_config(page_title="London Gold Sniper", page_icon="🔱", layout="wide")

# --- 1. إدارة الذاكرة والأرشيف ---
if 'all_signals' not in st.session_state:
    st.session_state.all_signals = []
if 'entry_price' not in st.session_state:
    st.session_state.entry_price = 0.0

def add_to_log(sig_type, price, rate):
    now = datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime("%H:%M:%S")
    if not st.session_state.all_signals or st.session_state.all_signals[0]['الوقت'][:-3] != now[:-3]:
        st.session_state.all_signals.insert(0, {"الوقت": now, "النوع": sig_type, "السعر": f"${price:,.2f}", "القوة": f"{rate}%"})
        st.toast(f"🚨 إشارة {sig_type} مكتشفة!", icon="🔔")

# --- 2. جلب البيانات بأمان (منع IndexError) ---
@st.cache_data(ttl=60)
def fetch_gold_data():
    try:
        data = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if data.empty or len(data) < 20:
            return None
        return data
    except:
        return None

# --- 3. محرك التحليل (Trend + RSI + Fib) ---
def get_analysis(df):
    try:
        # حساب السعر الحالي بأمان
        current_price = float(df['Close'].iloc[-1])
        
        # فيبوناتشي
        h, l = float(df['High'].max()), float(df['Low'].min())
        diff = h - l
        fibs = {"61.8%": h - 0.618 * diff, "50%": h - 0.5 * diff}
        
        # مؤشرات
        ma = df['Close'].rolling(20).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
        
        # قوة الصفقة
        score = 50
        if current_price > ma: score += 10
        if 70 > rsi > 30: score += 15
        
        signal = "صبر 🔄"
        if current_price > ma and rsi > 62: signal = "Premium BUY 🚀"
        elif current_price < ma and rsi < 38: signal = "Premium SELL 📉"
        
        return signal, current_price, fibs, min(score, 98)
    except:
        return None, 0.0, {}, 0

# --- 4. التحكم في وقت الجلسة ---
def is_london_active():
    # توقيت الجزائر (GMT+1) - لندن الصباحية من 8 صباحاً حتى 12 ظهراً
    now_dz = datetime.datetime.now(pytz.timezone('Africa/Algiers')).time()
    start = datetime.time(8, 0)
    end = datetime.time(12, 0)
    return start <= now_dz <= end

# --- 5. الواجهة البرمجية ---
data = fetch_gold_data()

if data is not None:
    current_p = float(data['Close'].iloc[-1])
    # عرض السعر في الأعلى بشكل بارز جداً
    st.markdown(f"<h1 style='text-align: center; color: #FFD700; background-color: #1e1e1e; padding: 20px; border-radius: 10px;'>💰 سعر الذهب المباشر: {current_p:,.2f}$</h1>", unsafe_allow_html=True)
    
    st.title("🔱 رادار قناص لندن الصباحي")
    
    if is_london_active():
        status, price, fib_levels, success = get_analysis(data)
        
        # ميزة الـ Break-Even
        if st.session_state.entry_price > 0:
            diff = price - st.session_state.entry_price
            if abs(diff) > 4.5:
                st.success("✅ الصفقة في ربح جيد! فعل خاصية الـ Break-Even الآن.")
            elif (diff < -2.5 and "BUY" in status) or (diff > 2.5 and "SELL" in status):
                st.error("🛑 تحذير: السعر يعكس! راقب الصفقة للحماية.")

        # عرض الإشارة
        if "Premium" in status:
            st.success(f"🎯 إشارة نشطة: {status} | الجودة: {success}%")
            add_to_log(status, price, success)
            st.session_state.entry_price = price
            st.info(f"📏 اللوت: {RISK_USD/(4*10):.2f} | 🛑 الوقف: {price-4 if 'BUY' in status else price+4:.2f}")
        else:
            st.warning("🔎 بانتظار إشارة 'Premium' متوافقة مع شروط لندن...")
    else:
        st.error("⏳ الروبوت في وضع الاستراحة. جلسة لندن الصباحية (08:00 - 12:00) هي وقت العمل فقط.")

    st.divider()
    
    # أرشيف الإشارات
    st.subheader("📜 أرشيف إشارات الجلسة")
    if st.session_state.all_signals:
        st.table(pd.DataFrame(st.session_state.all_signals))
    else:
        st.info("لا توجد إشارات مسجلة اليوم حتى الآن.")
else:
    st.info("🔄 جاري الاتصال بخادم البيانات... يرجى الانتظار ثواني.")

# القائمة الجانبية
st.sidebar.header("⚙️ الإعدادات")
st.sidebar.write(f"🌍 توقيت الجزائر: {datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime('%H:%M:%S')}")
if st.sidebar.button("🗑️ مسح السجل وتصفير الدخول"):
    st.session_state.all_signals = []
    st.session_state.entry_price = 0.0
    st.rerun()
