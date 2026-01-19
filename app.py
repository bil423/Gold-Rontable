import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الحساب والمخاطرة
ACCOUNT_SIZE = 5000.0
RISK_USD = 25.0 

st.set_page_config(page_title="London Sniper Elite", page_icon="🇬🇧", layout="wide")

# --- 1. نظام حفظ الإشارات الدائم (Archive) ---
if 'all_signals' not in st.session_state:
    st.session_state.all_signals = []
if 'entry_price' not in st.session_state:
    st.session_state.entry_price = 0.0

def archive_signal(sig_type, sig_price, sig_rate):
    now = datetime.datetime.now(pytz.timezone('Africa/Algiers'))
    time_str = now.strftime("%H:%M:%S")
    # منع التكرار في نفس الدقيقة
    if not st.session_state.all_signals or st.session_state.all_signals[0]['الوقت'][:-3] != time_str[:-3]:
        entry = {
            "الوقت": time_str,
            "النوع": sig_type,
            "السعر": f"${sig_price:,.2f}",
            "القوة": f"{sig_rate}%"
        }
        st.session_state.all_signals.insert(0, entry)
        st.toast(f"🚨 تم رصد إشارة {sig_type} جديدة!", icon="🔔")

# --- 2. محرك التحليل المتطور (فيبوناتشي + قوة الاتجاه) ---
def analyze_london_session(df):
    if df is None or len(df) < 50: return None, 0.0, {}, 0
    
    high_p, low_p = float(df['High'].max()), float(df['Low'].min())
    diff = high_p - low_p
    fibs = {"61.8%": high_p - 0.618 * diff, "50%": high_p - 0.5 * diff, "38.2%": high_p - 0.382 * diff}
    
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    price = float(df['Close'].iloc[-1])
    ma = float(df['MA20'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    
    # حساب نسبة النجاح
    score = 45
    if price > ma: score += 15
    if 65 > rsi > 35: score += 10
    if any(abs(price - v) < 1.2 for v in fibs.values()): score += 25
    
    signal = "صبر 🔄"
    if price > ma and rsi > 62: signal = "Premium BUY 🚀"
    elif price < ma and rsi < 38: signal = "Premium SELL 📉"
    
    return signal, price, fibs, min(score, 99)

@st.cache_data(ttl=60)
def load_data():
    return yf.download("GC=F", period="5d", interval="1h", progress=False)

# --- 3. إدارة وقت جلسة لندن الصباحية ---
def is_london_session():
    now_utc = datetime.datetime.now(pytz.utc).time()
    # افتتاح لندن الصباحي (08:00 - 12:00 UTC) تقريباً
    start = datetime.time(8, 0)
    end = datetime.time(12, 0)
    return start <= now_utc <= end

# --- 4. واجهة المستخدم ---
st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>💰 سعر الذهب الآن: {load_data()['Close'].iloc[-1]:,.2f}$</h1>", unsafe_allow_html=True)
st.title("🛡️ رادار حساب التمويل (جلسة لندن فقط)")

if is_london_session():
    data = load_data()
    signal, price, fibs, rate = analyze_london_session(data)
    
    # منطق الـ BE والحماية
    if st.session_state.entry_price > 0:
        entry = st.session_state.entry_price
        if (price > entry + 4.0) or (price < entry - 4.0):
            st.success("✅ الربح ممتاز! فعل خاصية BE الآن لحماية الحساب.")
            st.toast("وقت تأمين الربح!", icon="🔒")

    # عرض الإشارة الحالية
    if "Premium" in signal:
        st.success(f"🎯 إشارة لندن الحالية: {signal} (القوة: {rate}%)")
        archive_signal(signal, price, rate)
        st.session_state.entry_price = price
        lot = RISK_USD / (4.0 * 10)
        st.info(f"📏 اللوت: {lot:.2f} | 🛑 الوقف: {price-4 if 'BUY' in signal else price+4:.2f}")
    else:
        st.warning("🔎 لندن الصباحية: الروبوت يراقب السيولة.. لا توجد إشارة Premium متوافقة.")
else:
    st.error("🛑 جلسة لندن الصباحية مغلقة حالياً. الروبوت في وضع الخمول لحماية حسابك من تذبذب خارج الجلسة.")

st.divider()

# --- 5. لوحة أرشيف الإشارات (Dashboard) ---
st.subheader("📜 سجل جميع إشارات الجلسة (Archive)")
if st.session_state.all_signals:
    st.table(pd.DataFrame(st.session_state.all_signals))
else:
    st.info("لم يتم تسجيل إشارات خلال الجلسة الحالية.")

# زر المسح وتوقيت الجزائر في الجانب
st.sidebar.write(f"🌍 توقيت الجزائر: {datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime('%H:%M:%S')}")
if st.sidebar.button("🗑️ مسح الأرشيف"):
    st.session_state.all_signals = []
    st.session_state.entry_price = 0.0
    st.rerun()
