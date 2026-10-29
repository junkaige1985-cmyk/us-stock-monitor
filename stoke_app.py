import streamlit as st
import yfinance as yf
import pandas as pd

# 页面配置
st.set_page_config(page_title="美股回撤监控与智能闹钟", layout="centered")

st.title("📈 美股回撤监控与智能闹钟")

# 初始化 Session State 用于存储自定义闹钟
if 'alarms' not in st.session_state:
    st.session_state.alarms = [
        {"id": 1, "name": "标普大跌防线", "ticker": "^GSPC", "metric": "回撤幅度 (%)", "target": -5.0},
        {"id": 2, "name": "纳指强劲反弹", "ticker": "^IXIC", "metric": "日涨幅 (%)", "target": 2.0}
    ]

# 创建两个 Tab 标签页，方便手机端切换
tab1, tab2 = st.tabs(["📊 实时测算与警报检查", "⏰ 闹钟规则管理"])

# ==================== TAB 1: 实时测算与警报检查 ====================
with tab1:
    st.markdown("### 🔍 实时美股行情与闹钟触发检测")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker_input = st.text_input("输入要测算的美股代码", value="^GSPC", key="main_ticker")
    with col2:
        period = st.selectbox("历史周期", ["1y", "2y", "5y", "max"], index=0, key="main_period")

    if st.button("开始测算并检查闹钟", type="primary", use_container_width=True):
        try:
            with st.spinner("正在获取最新数据..."):
                stock = yf.Ticker(ticker_input.strip())
                df = stock.history(period=period)
                
                if df.empty:
                    st.error("未找到该代码的数据，请检查拼写。")
                else:
                    current_price = df['Close'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    change_pct = (current_price - prev_close) / prev_close * 100
                    
                    peak_price = df['Close'].max()
                    peak_date = df['Close'].idxmax().strftime('%Y-%m-%d')
                    
                    drawdown_pct = (current_price - peak_price) / peak_price * 100
                    recovery_pct = (peak_price - current_price) / current_price * 100
                    
                    st.markdown("---")
                    st.subheader(f"📊 【{ticker_input.upper()}】当前状态")
                    
                    # 核心指标展示
                    m_col1, m_col2 = st.columns(2)
                    m_col1.metric("当前价格", f"${current_price:.2f}", f"{change_pct:+.2f}% (较昨日)")
                    m_col2.metric("周期最高点", f"${peak_price:.2f}", f"日期: {peak_date}")
                    
                    r_col1, r_col2 = st.columns(2)
                    r_col1.metric("当前回撤幅度", f"{drawdown_pct:.2f}%")
                    r_col2.metric("距前高涨回所需", f"{recovery_pct:.2f}%")
                    
                    st.markdown("### 🚨 闹钟触发检测")
                    # 检查当前输入代码匹配的闹钟
                    triggered_any = False
                    for alarm in st.session_state.alarms:
                        if alarm['ticker'].upper() == ticker_input.strip().upper():
                            m_type = alarm['metric']
                            target = alarm['target']
                            
                            current_val = 0.0
                            if m_type == "回撤幅度 (%)":
                                current_val = drawdown_pct
                                # 回撤通常是负数，若设目标 -5%，当 current_val <= -5 触发
                                is_triggered = current_val <= target
                            elif m_type == "日涨幅 (%)":
                                current_val = change_pct
                                is_triggered = current_val >= target
                            elif m_type == "距前高涨幅 (%)":
                                current_val = recovery_pct
                                is_triggered = current_val <= target # 比如距离小于2%时触发
                            else:
                                is_triggered = False

                            if is_triggered:
                                triggered_any = True
                                st.error(f"🔔 **【闹钟响起】{alarm['name']}**\n\n"
                                         f"代码: `{alarm['ticker']}` | 规则: {m_type} 达到目标 {target}%\n"
                                         f"当前实际数值: **{current_val:.2f}%**")
                    
                    if triggered_any:
                        # 触发时自动播放提示音 (HTML5 音频)
                        st.markdown("""
                            <audio autoplay>
                              <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mp3">
                            </audio>
                        """, unsafe_allow_html=True)
                    else:
                        st.success("✨ 当前代码没有触发任何已设定的闹钟。")
                        
                    st.markdown("### 📉 历史走势")
                    st.line_chart(df['Close'])
                    
        except Exception as e:
                    st.error(f"发生错误: {e}")

# ==================== TAB 2: 闹钟规则管理 ====================
with tab2:
    st.markdown("### ⏰ 自定义闹钟管理")
    st.markdown("在这里你可以添加、查看或删除你的个性化闹钟规则。")
    
    # 显示现有闹钟列表
    if not st.session_state.alarms:
        st.info("当前还没有设定任何闹钟，请在下方添加。")
    else:
        for i, alarm in enumerate(st.session_state.alarms):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**🏷️ 名称**: {alarm['name']}")
                    st.markdown(f"**📌 代码**: `{alarm['ticker']}`")
                with c2:
                    st.markdown(f"**📊 监控指标**: {alarm['metric']}")
                    st.markdown(f"**🎯 触发阈值**: {alarm['target']}%")
                with c3:
                    if st.button("删除", key=f"del_{alarm['id']}", type="secondary"):
                        st.session_state.alarms.pop(i)
                        st.rerun()

    st.markdown("---")
    st.markdown("### ➕ 添加新闹钟")
    with st.form("add_alarm_form"):
        new_name = st.text_input("闹钟名称 (例如: 标普大跌买入提醒)", "我的专属美股提醒")
        new_ticker = st.text_input("美股代码 (例如: ^GSPC 或 AAPL)", "^GSPC")
        new_metric = st.selectbox("监控指标", ["回撤幅度 (%)", "日涨幅 (%)", "距前高涨幅 (%)"])
        new_target = st.number_input("触发目标数值 (如回撤设 -5 表示跌超5%，涨幅设 3 表示涨超3%)", value=-5.0)
        
        submitted = st.form_submit_button("确认添加闹钟")
        if submitted:
            new_id = max([a['id'] for a in st.session_state.alarms], default=0) + 1
            st.session_state.alarms.append({
                "id": new_id,
                "name": new_name,
                "ticker": new_ticker.strip(),
                "metric": new_metric,
                "target": new_target
            })
            st.success(f"成功添加闹钟：{new_name}！")
            st.rerun()