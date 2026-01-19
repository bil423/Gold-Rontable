import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# --- إعدادات الحساب ---
ACCOUNT_SIZE = 5000.0
RISK_USD = 25.0 

st.set_page_config(page_title="Gold London Sniper", page_icon="🔱", layout="wide")

# --- 1. الذاكرة الدائمة خلال الجلسة ---
if 'all_signals' not in st.session_state:
    st.session_state.all_signals = []
if 'entry_price' not in st.session_state:
    st.session_state.entry_price = 0.0

def add_to_archive(sig_type, price, rate):
    now = datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime("%H:%M:%S")
    # منع التكرار لضمان نظافة الجدول
    if not st.session_state.all_signals or st.session_state.all_signals[0]['الوقت'][:-3] != now[:-3]:
        st.session_state.all_signals.insert(0, {"الوقت": now, "النوع": sig_type, "السعر": f"${price:,.2f}", "القوة": f"{rate}%"})
        st.toast(f"🚨 تم تسجيل إشارة {sig_type}", icon="✅")

# --- 2. جلب البيانات وحل مشكلة IndexError ---
@st.cache_data(ttl=60)
def fetch_safe_data():
    try:
        data = yf.download("GC=F", period="5d", interval="1h", progress=False)
        if data is not None and len(data) > 10:
            return data
        return None
    except:
        return None

# --- 3. محرك التحليل (لندن الصباحية) ---
def run_analysis(df):
    try:
        current_p = float(df['Close'].iloc[-1])
        # فيبوناتشي
        h, l = float(df['High'].max()), float(df['Low'].min())
        diff = h - l
        fibs = {"61.8% (الذهبي)": h - 0.618 * diff, "50%": h - 0.5 * diff}
        
        # مؤشرات الزخم والاتجاه
        ma = df['Close'].rolling(20).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
        
        # حساب الجودة
        score = 50
        if current_p > ma: score += 10
        if 65 > rsi > 35: score += 15
        
        signal = "صبر 🔄"
        if current_p > ma and rsi > 62: signal = "Premium BUY 🚀"
        elif current_p < ma and rsi < 38: signal = "Premium SELL 📉"
        
        return signal, current_p, fibs, min(score, 99)
    except:
        return None, 0.0, {}, 0

# --- 4. التحقق من وقت لندن (توقيت الجزائر) ---
def is_london_time():
    now_dz = datetime.datetime.now(pytz.timezone('Africa/Algiers')).time()
    # جلسة لندن الصباحية: 08:00 إلى 12:00
    return datetime.time(8, 0) <= now_dz <= datetime.time(12, 0)

# --- 5. بناء واجهة المستخدم ---
data = fetch_safe_data()

if data is not None:
    price_now = float(data['Close'].iloc[-1])
    # عرض السعر المباشر في الأعلى (تصميم بارز)
    st.markdown(f"""
        <div style="background-color:#1e1e1e; padding:20px; border-radius:15px; border: 2px solid #FFD700; text-align:center;">
            <h1 style="color:#FFD700; margin:0;">💰 سعر الذهب الآن: {price_now:,.2f}$</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.title("🔱 رادار قناص لندن (5000$)")
    
    if is_london_time():
        status, price, fib_levels, rate = run_analysis(data)
        
        # نظام حماية BE
        if st.session_state.entry_price > 0:
            diff = price - st.session_state.entry_price
            if abs(diff) > 4.5:
                st.success("🔒 الهدف الأول محقق! انقل الوقف لنقطة الدخول (BE) الآن.")
            elif (diff < -2.5 and "BUY" in status) or (diff > 2.5 and "SELL" in status):
                st.error("🛑 تحذير انعكاس! حماية الحساب أولوية.")

        if "Premium" in status:
            st.success(f"🎯 إشارة لندن نشطة: {status} (الجودة: {rate}%)")
            add_to_archive(status, price, rate)
            st.session_state.entry_price = price
            st.info(f"📏 اللوت: {RISK_USD/(4*10):.2f} | 🛑 الوقف: {price-4 if 'BUY' in status else price+4:.2f}")
        else:
            st.warning("🔎 لندن الصباحية: بانتظار توافق السيولة لإشارة Premium...")
    else:
        st.error("⏳ الروبوت في وضع الخمول. جلسة لندن الصباحية (08:00 - 12:00) هي وقت العمل المسموح به.")

    st.divider()
    
    # أرشيف الإشارات
    st.subheader("📜 أرشيف جميع إشارات الجلسة")
    if st.session_state.all_signals:
        st.table(pd.DataFrame(st.session_state.all_signals))
    else:
        st.info("لا توجد إشارات مسجلة في الأرشيف حالياً.")
else:
    st.info("🔄 جاري تحديث البيانات من الخادم... يرجى الانتظار.")

# القائمة الجانبية
st.sidebar.write(f"⏰ توقيت الجزائر: {datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime('%H:%M:%S')}")
if st.sidebar.button("🗑️ مسح الأرشيف وتصفير الدخول"):
    st.session_state.all_signals = []
    st.session_state.entry_price = 0.0
    st.rerun()
