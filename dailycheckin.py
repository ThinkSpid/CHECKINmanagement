import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "SimSun"]
from datetime import datetime, time

# 页面设置
st.set_page_config(page_title="考勤分析助手", layout="wide")
st.markdown("""
<style>
body {
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
}
</style>
""", unsafe_allow_html=True)
st.title("📅 考勤记录分析与目标预测工具")

# 辅助函数：计算时间差
def calculate_time_difference(t):
    # 使用考勤记录中的日期而非当前日期
    target = datetime.combine(t.date(), time(8, 0))
    delta = int((target - t).total_seconds() / 60)
    return delta

# 上传文件
uploaded_file = st.file_uploader("请上传你的考勤记录 Excel 文件 (.xlsx)", type=["xlsx"])

if uploaded_file:
    # 读取Excel数据
    df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=None)
    
    # 设置列名并清理数据
    columns = ['编号', '姓名', '部门', '日期', '考勤状态', '数据来源', '处理类型', '体温', '体温异常']
    df.columns = columns
    
    # 删除空行
    df.dropna(subset=['日期'], inplace=True)

    # 解析日期列
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df[df['日期'].notnull()].copy()

    # 提取打卡时间
    df['打卡时间'] = df['日期'].dt.time
    df['打卡时间戳'] = df['日期']
    df['时间差分钟'] = df['打卡时间戳'].apply(lambda x: calculate_time_difference(x))

    # 过滤掉周日
    df['星期几'] = df['日期'].dt.day_name()
    df = df[df['星期几'] != 'Sunday']

    st.success("✅ 文件已成功加载并解析！")

    # 显示原始数据
    with st.expander("📊 查看原始数据"):
        st.dataframe(df[['日期', '打卡时间', '星期几', '时间差分钟']])

    # 可视化部分
    st.subheader("📈 每日到岗时间分析")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['日期'], df['时间差分钟'], marker='o', linestyle='-', color='b')
    ax.axhline(0, color='r', linestyle='--', label='准时 (8:00)')
    ax.set_xlabel("日期")
    ax.set_ylabel("时间差 (分钟)")
    ax.set_title("每日打卡时间相对于8:00的偏差")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # 平均值统计
    avg_score = df['时间差分钟'].mean()
    st.metric(label="当前平均得分（相对于8:00）", value=f"{avg_score:.2f} 分钟")

    # 预测功能
    st.subheader("🎯 目标设定与预测")
    desired_avg = st.slider("你想在月底达到的平均提前时间（分钟）（正数为提前，负数为迟到）", min_value=-60, max_value=60, value=0)

    days_left = (df['日期'].max().replace(day=df['日期'].max().days_in_month) - df['日期'].max()).days
    if days_left <= 0:
        st.warning("⚠️ 当前数据中没有剩余天数用于预测，请确保数据覆盖整个月。")
    else:
        required_score_per_day = (desired_avg * (len(df) + days_left) - df['时间差分钟'].sum()) / days_left
        st.markdown(f"""
<style>
.stApp { font-family: sans-serif; }
.stMarkdown { line-height: 1.6; }
</style>
""", unsafe_allow_html=True)
        st.markdown(f"""
### 计算明细
- 当前已记录天数: {len(df)}
- 当前总时间差: {df['时间差分钟'].sum():.2f} 分钟
- 剩余工作日: {days_left}
- 目标总时间差: {desired_avg * (len(df) + days_left):.2f} 分钟
- 剩余需达成时间差: {desired_avg * (len(df) + days_left) - df['时间差分钟'].sum():.2f} 分钟

为了达到月末平均 `{desired_avg:.2f}` 分钟，接下来每天需要平均打分为：**{required_score_per_day:.2f} 分钟**
""")

        arrival_time = datetime.combine(datetime.today(), time(8, 0)) - pd.Timedelta(minutes=required_score_per_day)
        st.markdown(f"👉 即你应该每天大约在 **{arrival_time.strftime('%H:%M')}** 打卡")

        if required_score_per_day > 0:
            st.info(f"✅ 你比8点早到了 {abs(required_score_per_day):.2f} 分钟")
        elif required_score_per_day < 0:
            st.warning(f"⏰ 你需比8点提前 {-required_score_per_day:.2f} 分钟")
        else:
            st.success("✅ 你需要刚好在8点打卡以达成目标")

else:
    st.info("📂 请上传一个 Excel 格式的考勤表以开始分析")