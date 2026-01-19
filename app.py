import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الحساب
ACCOUNT_SIZE = 5000.0
RISK_PER_TRADE_USD = 25.0

st.set_page_config(page_title="Funded Sniper Safe-Guard", page_icon="🛡️", layout="wide")

# --- 1. نظام الذاكرة والتنبيهات ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_signal_price' not in st.session_state:
    st.session_state.last_signal_price = 0.0

def send_alert(msg, icon="🔔"):
    st.toast(msg, icon=icon)
    st.components.v1.html("""<audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg"></audio>""", height=0)

# --- 2. محرك التحليل المتقدم ---
def analyze_advanced(df):
    if df is None or len(df) < 50: return None, 0.0, {}, 0
    try:
        # حساب الفيبوناتشي
        high_p, low_p = float(df['High'].max()), float(df['Low'].min())
        diff = high_p - low_p
        fibs = {"61.8%": high_p - 0.618 * diff, "50%": high_p - 0.5 * diff, "38.2%": high_p - 0.382 * diff}
        
        # المؤشرات
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp = float(df['Close'].iloc[-1])
        lma = float(df['MA20'].iloc[-1])
        lrsi = float(df['RSI'].iloc[-1])
        
        # قوة الاتجاه ونسبة النجاح
        success_rate = 50
        if lp > lma: success_rate += 15
        if lrsi > 60 or lrsi < 40: success_rate += 15
        if any(abs(lp - v) < 2.0 for v in fibs.values()): success_rate += 20
        
        signal = "صبر 🔄"
        if lp > lma and lrsi > 62: signal = "Premium BUY 🚀"
        elif lp < lma and lrsi < 38: signal = "Premium SELL 📉"
        
        return signal, lp, fibs, min(success_rate, 98)
    except Exception as e:
        return None, 0.0, {}, 0

@st.cache_data(ttl=60)
def fetch_data(inv, per):
    try:
        d = yf.download("GC=F", period=per, interval=inv, progress=False)
        return d if not d.empty else None
    except: return None

# --- 3. الواجهة الرئيسية ---
st.title("🛡️ رادار التمويل: نظام حماية الحساب (BE)")

d1h, d15m = fetch_data("1h", "5d"), fetch_data("15m", "2d")
t1h, price, fibs, rate = analyze_advanced(d1h)
t15m, _, _, _ = analyze_advanced(d15m)

if price > 0:
    # --- منطق تنبيه الـ BE والانعكاس ---
    if st.session_state.last_signal_price > 0:
        entry = st.session_state.last_signal_price
        # إذا ربحت الصفقة 4 دولار، نطلب تحريك الوقف لنقطة الدخول (BE)
        if ("BUY" in t1h and price > entry + 4.0) or ("SELL" in t1h and price < entry - 4.0):
            st.success("✅ الهدف الأول تحقق! انقل وقف الخسارة إلى نقطة الدخول (Break-Even) الآن.")
            send_alert("وقت تأمين الصفقة (BE)!", icon="🔒")
        
        # إذا عكس السعر 2.5 دولار ضدك
        elif ("BUY" in t1h and price < entry - 2.5) or ("SELL" in t1h and price > entry + 2.5):
            st.error("⚠️ تحذير: السعر يعكس بقوة! فكر في الخروج لتقليل الخسارة.")
            send_alert("انعكاس خطر! حماية الحساب", icon="🛑")

    # عرض البيانات
    col1, col2, col3 = st.columns(3)
    col1.metric("السعر الحالي", f"${price:,.2f}")
    col2.metric("جودة الإشارة", f"{rate}%")
    col3.metric("مخاطرة اليوم", "$25")

    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success(f"🎯 إشارة نشطة: {t1h} (القوة: {rate}%)")
        st.session_state.last_signal_price = price
        lot = 25.0 / (4.0 * 10)
        st.info(f"📏 اللوت: {lot:.2f} | ✅ الهدف: {price+7.5 if 'BUY' in t1h else price-7.5:.2f} | 🛑 الوقف: {price-4 if 'BUY' in t1h else price+4:.2f}")
    else:
        st.warning("🔎 بانتظار توافق الفريمات (Premium Setup)...")

st.divider()

# حل مشكلة الجدول (Fixing the Column Error)
st.subheader("📏 مستويات فيبوناتشي الحالية")
if fibs:
    # عرض المستويات في جدول بدلاً من أعمدة لتجنب الأخطاء التقنية
    fib_df = pd.DataFrame(list(fibs.items()), columns=['المستوى', 'السعر'])
    st.dataframe(fib_df, use_container_width=True)
else:
    st.info("جاري حساب المستويات...")

st.sidebar.write(f"🌍 توقيت الجزائر: {datetime.datetime.now(pytz.timezone('Africa/Algiers')).strftime('%H:%M:%S')}")
