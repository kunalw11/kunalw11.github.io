import os
import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Configuration & Keys Setup
os.environ["GOOGLE_API_KEY"] = "[API_KEY]"  # Replace with your actual Gemini API key

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
    "user": "[username]",
    "private_key": private_key_der_bytes,
    "host": "[account_url]",
    "port": 443,
    "role": "ACCOUNTADMIN",
    "warehouse": "TUNING_PROJECT_WH",
    "database": "OPTIMIZATION_DB",
    "schema": "ANALYTICAL_LOGS"
}

# 2. Main Analytics & Orchestration Loop
try:
    print("🔌 Connecting to Snowflake Warehouse...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()

    # Data Transformation Step: Build a curated Data Mart
    print("📊 Executing ELT transformation to build AGGREGATE_PERFORMANCE_MART...")
    cursor.execute("""
        CREATE OR REPLACE TABLE OPTIMIZATION_DB.ANALYTICAL_LOGS.AGGREGATE_PERFORMANCE_MART AS
        SELECT 
            USER_NAME,
            COUNT(*) as TOTAL_QUERIES_RUN,
            ROUND(AVG(EXECUTION_TIME_MS), 2) as AVG_EXECUTION_TIME_MS,
            MAX(EXECUTION_TIME_MS) as MAX_EXECUTION_TIME_MS,
            ROUND(AVG(BYTES_SCANNED) / 1024 / 1024, 2) as AVG_MEGABYTES_SCANNED,
            SUM(CASE WHEN QUERY_TEXT LIKE '%CROSS JOIN%' OR QUERY_TEXT LIKE '%SELECT *%' THEN 1 ELSE 0 END) as BAD_PRACTICE_COUNT
        FROM OPTIMIZATION_DB.ANALYTICAL_LOGS.RAW_INFRASTRUCTURE_LOGS
        WHERE STATUS = 'SUCCESS'
        GROUP BY USER_NAME;
    """)

    # Extract the curated analytics from the Data Mart
    print("📥 Extracting processed metrics for AI analysis...")
    cursor.execute("SELECT * FROM OPTIMIZATION_DB.ANALYTICAL_LOGS.AGGREGATE_PERFORMANCE_MART;")
    columns = [col[0].lower() for col in cursor.description]

    # Convert any Decimal database types to floats on the fly during extraction
    mart_data = []
    for row in cursor.fetchall():
        processed_row = {}
        for col, val in zip(columns, row):
            # If the value is a database Decimal object, cast it to a standard Python float
            if type(val).__name__ == 'Decimal':
                processed_row[col] = float(val)
            else:
                processed_row[col] = val
        mart_data.append(processed_row)

    # 3. Pass the structured Data Mart payload to the Gemini Agent
    print("🧠 Initializing Gemini Analytics Agent...")
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

    print("🚀 Generating Executive Infrastructure Analytics Report...")
    report = chain.invoke({"data": json.dumps(mart_data, indent=2)})

    print("\n=================== 📊 EXECUTIVE FINOPS REPORT ===================")
    print(report.content)
    print("==================================================================")
    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Analytics Layer Failed: {e}")
