import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 从Secrets获取Airtable配置（需用户在Streamlit社区云或本地secrets.toml中配置）
AIRTABLE_API_KEY = st.secrets.get("airtable_api_key", "")
AIRTABLE_BASE_ID = st.secrets.get("airtable_base_id", "")
AIRTABLE_TABLE_NAME = "tblWyetzvY1weZjDv"


def get_airtable_data():
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        st.error("请配置Airtable API密钥和基ID（通过Streamlit Secrets或环境变量）")
        return pd.DataFrame()
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    
    all_records = []
    offset = None
    
    # Airtable API分页获取所有数据
    while True:
        params = {"offset": offset} if offset else {}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            all_records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        except Exception as e:
            st.error(f"获取Airtable数据失败: {str(e)}")
            return pd.DataFrame()
    
    records = []
    for record in all_records:
        fields = record.get("fields", {})
        date_str = fields.get("日期")  # 假设Airtable中有"日期"字段（格式YYYY-MM-DD）
        if date_str:
            try:
                month = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
            except ValueError:
                month = "日期格式错误"
        else:
            month = "未记录日期"
        
        records.append({
            "月份": month,
            "病例类型": fields.get("业务类型", "未知类型"),  # 根据Airtable实际字段名"业务类型"获取病例类型
            "分值": fields.get("分值", 0)  # 假设Airtable中有"分值"字段（数值类型）
        })
    
    return pd.DataFrame(records)


# 主应用
st.title("📊 病例制作情况与分值分析看板")

# 获取并缓存数据（每小时刷新）
@st.cache_data(ttl=3600)
def cached_airtable_data():
    return get_airtable_data()
df = cached_airtable_data()

if not df.empty:
    # 数据预处理
    monthly_group = df.groupby(["月份", "病例类型"]).agg({
        "分值": ["sum", "count"]  # 计算每月每种类型的总分和病例数
    }).reset_index()
    monthly_group.columns = ["月份", "病例类型", "总分值", "病例数"]
    
    monthly_total = df.groupby("月份").agg({
        "分值": ["sum", "count"]
    }).reset_index()
    monthly_total.columns = ["月份", "月度总分", "病例总数"]
    
    # 侧边栏筛选
    st.sidebar.header("筛选条件")
    selected_months = st.sidebar.multiselect("选择月份", df["月份"].unique(), default=df["月份"].unique())
    filtered_group = monthly_group[monthly_group["月份"].isin(selected_months)]
    filtered_total = monthly_total[monthly_total["月份"].isin(selected_months)]

    # 主内容展示
    st.subheader("📅 月度病例类型分布（堆叠柱状图）")
    st.bar_chart(filtered_group, x="月份", y="总分值", color="病例类型", use_container_width=True)
    
    st.subheader("📈 月度总分趋势")
    st.line_chart(filtered_total, x="月份", y=["月度总分", "病例总数"], use_container_width=True)
    
    st.subheader("📋 详细数据表格")
    st.dataframe(filtered_group, use_container_width=True)
else:
    st.info("请检查Airtable配置或确保表中存在数据")
