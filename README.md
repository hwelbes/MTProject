# Automated Exploratory Data Analysis (EDA) & Cleaning Dashboard

## Project Description
An automated web dashboard designed to eliminate the time bottleneck of data preprocessing and cleaning. Built for junior data analysts, business intelligence students, and academic researchers, the platform automates standard data-profiling metrics, provides AI-driven anomaly explanations, and executes routine cleaning workflows with one click.

## Core Features
* **Seamless Data Ingestion:** Drag-and-drop file upload supporting `.csv` and `.xlsx` formats.
* **Automated Data Quality Health Score:** Instant detection of missing values, duplicate rows, incorrect data types, and numerical outliers.
* **One-Click Data Remediation:** Automated duplicate removal, missing-value imputation, and standardization with clean dataset export.
* **AI-Powered Insights:** LLM integration that translates statistical summaries into plain-English anomaly explanations and cleaning recommendations.

## Planned Technology Stack
* **Frontend & Backend:** Streamlit / FastAPI
* **Data Core Engine:** Python, Pandas, NumPy
* **AI Integration:** LLM API (for automated data profiling insights)
* **Containerization:** Docker
* **CI/CD:** GitHub Actions
* **Cloud Deployment:** Google Cloud Platform (GCP)

## Current MVP Status
This repository includes a working Streamlit-based prototype of the dashboard. It supports file upload, automated quality scoring, missing-value treatment, duplicate removal, and downloadable cleaned exports.

## Local Development
1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Start the app:
   `streamlit run app.py`
4. Open the local URL shown in the terminal.

## Project Structure
* `app.py` — dashboard UI and workflow
* `src/eda_dashboard/core.py` — loading, profiling, and cleaning logic
* `src/eda_dashboard/insights.py` — heuristic-based anomaly recommendations
* `Dockerfile` — containerized deployment
* `.github/workflows/ci.yml` — basic CI validation

## Future Enhancements
* Add FastAPI backend endpoints for batch inference and deployment
* Integrate a real LLM API for natural-language explanations
* Publish the app to GCP using a CI/CD deployment pipeline
