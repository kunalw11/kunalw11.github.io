# AI-Driven Cloud Data Warehouse Pipeline & Performance Analytics Agent

## 🏗️ Project Overview
This project features an end-to-end automated ELT data pipeline built in Python that streams infrastructure telemetry logs into Snowflake, models them into an optimized performance data mart, and leverages an interactive Streamlit UI coupled with a generative AI agent (LangChain + Gemini) to execute live FinOps infrastructure cost audits.

## ⚙️ Tech Stack
* **Cloud Warehouse:** Snowflake (SQL, ELT Modeling, Star Schema design)
* **AI Orchestration:** LangChain, Google Gemini Pro API
* **Frontend UI:** Streamlit, Plotly Data Visualizations
* **Language/Libraries:** Python, Pandas, PyArrow, Cryptography

## 📂 Architecture & Files
* `phase1_pipeline.py` - Ingestion engine generating mock logs and bulk-loading to Snowflake staging.
* `phase2_analytics.py` - SQL aggregation pipeline engineering the Data Mart.
* `app.py` - Interactive analytical dashboard web application.
