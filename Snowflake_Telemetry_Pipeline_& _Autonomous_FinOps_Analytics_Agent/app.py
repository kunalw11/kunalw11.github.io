import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px  # Streamlit works brilliantly with Plotly for dynamic charts
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Page Configuration
st.set_page_config(page_title="AI Cloud FinOps Agent", page_icon="📊", layout="wide")

# 1. Configuration & Keys Setup
os.environ["GOOGLE_API_KEY"] = "[API_KEY]"  # Replace with your real key

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "snowflake_key.pem")
with open(desktop_path, "rb") as key_file:
    p_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=default_backend())

private_key_der_bytes = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

SNOWFLAKE_CONFIG = {
    "account": "[account_name]",
    "user": "KUNALW11",
    "private_key": private_key_der_bytes,
    "host": "host_url",
    "port": 443,
    "role": "ACCOUNTADMIN",
    "warehouse": "TUNING_PROJECT_WH",
    "database": "OPTIMIZATION_DB",
    "schema": "ANALYTICAL_LOGS"
}


# 2. Database Fetch Function
@st.cache_data(ttl=60)  # Caches data for 1 minute to keep the UI incredibly fast
def fetch_data_mart():
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM OPTIMIZATION_DB.ANALYTICAL_LOGS.AGGREGATE_PERFORMANCE_MART;")
    columns = [col[0].upper() for col in cursor.description]

    mart_data = []
    for row in cursor.fetchall():
        processed_row = {}
        for col, val in zip(columns, row):
            if type(val).__name__ == 'Decimal':
                processed_row[col] = float(val)
            else:
                processed_row[col] = val
        mart_data.append(processed_row)

    cursor.close()
    conn.close()
    return pd.DataFrame(mart_data)


# 3. Streamlit UI Layout
st.title("🧠 AI-Driven Cloud Data Warehouse Pipeline & Analytics Dashboard")
st.markdown("This control center monitors operational trends and leaks inside your Snowflake clusters.")
st.write("---")

try:
    # Pull data from Snowflake
    df = fetch_data_mart()

    # KPI Matrix Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Logged Queries", value=int(df["TOTAL_QUERIES_RUN"].sum()))
    with col2:
        st.metric(label="Peak System Latency", value=f"{df['MAX_EXECUTION_TIME_MS'].max():,} ms")
    with col3:
        st.metric(label="Avg Processing Scale", value=f"{df['AVG_MEGABYTES_SCANNED'].mean():.2f} MB")
    with col4:
        st.metric(label="Anti-Pattern Warnings", value=int(df["BAD_PRACTICE_COUNT"].sum()), delta_color="inverse")

    st.write("---")

    # Visualization Section
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Compute Distribution by Database User Profile")
        fig1 = px.bar(df, x="USER_NAME", y="TOTAL_QUERIES_RUN", color="USER_NAME", text_auto=True)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        st.subheader("Anti-Pattern Distribution vs Volume Scanned")
        fig2 = px.scatter(df, x="AVG_MEGABYTES_SCANNED", y="BAD_PRACTICE_COUNT", size="TOTAL_QUERIES_RUN",
                          hover_name="USER_NAME")
        st.plotly_chart(fig2, use_container_width=True)

    st.write("---")

    # Interactive AI Auditing Section
    st.subheader("🤖 Request Live Agent FinOps Audit")
    st.write("Click below to pass the structured Data Mart directly to the Gemini Analytics core.")

    if st.button("Run AI Infrastructure Audit"):
        with st.spinner("Analyzing optimization vectors..."):
            # Prepare payload
            payload = df.to_dict(orient="records")

            system_instruction = (
                "You are an expert Data Analyst and Cloud FinOps Executive.\n"
                "Analyze the provided Data Mart metrics summarizing user execution behaviors on Snowflake.\n"
                "Identify who the highest cost/resource-consuming users are, call out risks regarding 'bad practices' "
                "(like unnecessary full table scans or Cartesian products), and provide explicit business-level optimization steps."
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_instruction),
                ("user", "Here is the compiled Data Mart payload:\n\n{data}")
            ])

            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
            chain = prompt | llm
            report = chain.invoke({"data": json.dumps(payload, indent=2)})

            st.success("Analysis Complete!")
            st.markdown("### 📊 Executive Infrastructure Analytics Report")
            st.info(report.content)

except Exception as e:
    st.error(f"Failed to refresh dashboard stream: {e}")
