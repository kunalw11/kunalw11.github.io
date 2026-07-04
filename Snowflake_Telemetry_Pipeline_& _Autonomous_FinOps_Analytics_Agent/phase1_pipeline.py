import os
import json
import pandas as pd
from datetime import datetime, timedelta
import random
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# 1. Cryptographic Key Authentication Setup
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "snowflake_key.pem")
with open(desktop_path, "rb") as key_file:
    p_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

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


# 2. Generator function to simulate dirty enterprise app infrastructure logs
def generate_mock_logs(num_records=100):
    print(f"🏭 Generating {num_records} mock enterprise telemetry records...")
    queries = [
        "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE o.status = 'PENDING';",
        "SELECT order_id, SUM(price) FROM order_details GROUP BY order_id HAVING SUM(price) > 1000;",
        "SELECT * FROM application_logs WHERE log_level = 'ERROR' AND timestamp >= DATEADD(day, -7, CURRENT_TIMESTAMP());",
        "SELECT u.email, p.product_name FROM users u CROSS JOIN products p;",  # Inefficient Cartesian Join example
        "SELECT COUNT(DISTINCT session_id) FROM web_clicks WHERE page_path LIKE '%/checkout%';"
    ]

    data = []
    base_time = datetime.now()

    for i in range(num_records):
        query_text = random.choice(queries)
        exec_time = random.randint(200,
                                   15000) if "CROSS JOIN" in query_text or "SELECT *" in query_text else random.randint(
            10, 800)
        bytes_scnd = random.randint(500000, 2000000000) if "application_logs" in query_text else random.randint(1024,
                                                                                                                512000)

        record = {
            "TRANSACTION_ID": f"TXN-{100000 + i}",
            "TIMESTAMP": (base_time - timedelta(minutes=random.randint(1, 10000))).strftime('%Y-%m-%d %H:%M:%S'),
            "QUERY_TEXT": query_text,
            "EXECUTION_TIME_MS": exec_time,
            "BYTES_SCANNED": bytes_scnd,
            "USER_NAME": random.choice(["APP_SERVICE", "BI_REPORTING_USER", "DEV_KUNAL", "ANALYTICS_BOT"]),
            "STATUS": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILED"])
        }
        data.append(record)

    return pd.DataFrame(data)


# 3. Main Data Engineering Execution Loop
# 3. Main Data Engineering Execution Loop
try:
    print("🔌 Opening secure connection channel to Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()

    # Ensure the complete database environment path exists
    print("🏗️ Building database structures if missing...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS OPTIMIZATION_DB;")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS OPTIMIZATION_DB.ANALYTICAL_LOGS;")

    # Create the structured staging table explicitly if it doesn't exist
    print("🏗️ Ensuring structural landing tables exist in ANALYTICAL_LOGS...")
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS OPTIMIZATION_DB.ANALYTICAL_LOGS.RAW_INFRASTRUCTURE_LOGS
                   (
                       TRANSACTION_ID
                       VARCHAR
                   (
                       50
                   ),
                       TIMESTAMP TIMESTAMP_NTZ,
                       QUERY_TEXT STRING,
                       EXECUTION_TIME_MS INT,
                       BYTES_SCANNED INT,
                       USER_NAME VARCHAR
                   (
                       100
                   ),
                       STATUS VARCHAR
                   (
                       20
                   )
                       );
                   """)

    # Generate the log DataFrame
    df = generate_mock_logs(150)
    
    # Use Snowflake's high-speed internal Pandas tool to load the table
    print("🚀 Initiating high-speed Pandas bulk-load into RAW_INFRASTRUCTURE_LOGS...")
    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name="RAW_INFRASTRUCTURE_LOGS",
        database="OPTIMIZATION_DB",
        schema="ANALYTICAL_LOGS"
    )

    if success:
        print(f"💾 Success! Bulk-loaded {nrows} rows across {nchunks} memory chunk(s) into Snowflake.")
    else:
        print("❌ Data pipeline failed to verify the load rowcount.")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Pipeline Execution Halt: {e}")
