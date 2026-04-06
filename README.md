# Major Project

This repository contains a news analytics solution built as a full-stack project. It includes:

- a Python FastAPI backend that connects to Databricks and exposes analytics APIs
- a React + Vite frontend dashboard for visualizing news sentiment, categories, channels, and trends
- Databricks ETL scripts for a bronze/silver/gold data pipeline
- a separate machine learning workspace for scraping, preprocessing, sentiment analysis, and classification

## Project Overview

The primary goal of this project is to ingest news article data, process it through a multi-stage pipeline, enrich it with sentiment and category labels, and present interactive insights through a web dashboard.

Key capabilities:

- list and filter news articles by channel, category, sentiment, date, and keywords
- compute dashboard summaries such as sentiment distribution, daily volumes, and top negative alerts
- compare channel statistics and channel-level sentiment metrics
- show project and lineage metadata for the ETL pipeline
- run a separate ML workspace for scraping, sentiment modeling, and classification experiments

---

## Repository Structure

- `backend/`
  - FastAPI application in `backend/app/main.py`
  - Databricks SQL integration in `backend/app/database.py`
  - API route modules in `backend/app/routes/`
  - Dependencies listed in `backend/requirements.txt`

- `frontend/`
  - React application bootstrapped with Vite
  - Page components in `frontend/src/pages/`
  - Shared components in `frontend/src/components/`
  - API client in `frontend/src/api.js`
  - Dependencies and scripts in `frontend/package.json`

- `databricks/`
  - ETL scripts representing incremental pipeline stages:
    - `01_extract_to_volume.py` – extract raw source news data to a staging volume
    - `02_volume_to_bronze.py` – ingest raw data into the bronze layer
    - `03_bronze_to_silver.py` – clean and standardize bronze records into silver
    - `04_silver_to_gold.py` – enrich silver data into gold-level tables with sentiment/category metadata

- `major project/ml/`
  - Separate machine learning workspace with its own requirements
  - Scrapers, preprocessing, sentiment mapping, and classification modules
  - `main.py` entrypoint for running ML experiments and pipelines

---

## Backend Architecture

The backend serves as a read-only API layer on top of Databricks data.

### Core backend files

- `backend/app/main.py`
  - Creates the FastAPI app
  - Registers routers under the `/api` prefix
  - Enables CORS for local frontend origins

- `backend/app/database.py`
  - Loads Databricks connection settings from `.env`
  - Exposes `get_connection()`, `execute_query()`, and `execute_scalar()` helpers

### API Endpoints

The API routes are coded in `backend/app/routes/` and expose the following endpoints:

- `GET /api/health`
  - Simple health check returning `{ "status": "ok" }`

- `GET /api/dashboard/dates`
  - Returns the available article dates for dashboard filtering

- `GET /api/dashboard?date=<YYYY-MM-DD>`
  - Returns dashboard summary data, including:
    - total article count
    - sentiment distribution
    - category and channel distributions
    - top negative alerts
    - sentiment trends, polarity and volume over time
    - category-level, channel-level, and ministry-level sentiment breakdowns

- `GET /api/articles`
  - Returns paginated articles with optional query filters:
    - `page`, `per_page`
    - `channel`, `category`, `sentiment`, `date`
    - `search`, `sort_by`
  - Each article includes cleaned body text, sentiment scores, channel, category, and URL

- `GET /api/channels`
  - Returns summary statistics per channel, including article counts, average scores, and negative alert counts

- `GET /api/channels/compare?channels=...&category=...`
  - Compares two or more channels and returns grouped article details for each selected channel

- `GET /api/categories`
  - Returns available category labels and their article counts

- `GET /api/trends?channel=...&category=...`
  - Returns time-series sentiment trends grouped by date and filtered by channel or category if provided

- `GET /api/project-info`
  - Returns high-level pipeline stats:
    - total articles
    - date range
    - channel count
    - category count
    - sentiment breakdown
    - hard-coded pipeline stage metadata for display

- `GET /api/lineage`
  - Returns a data lineage summary describing each pipeline stage
  - Includes counts for cleaned articles, sentiment-analyzed articles, and category metadata

### Data source

The backend reads from the Databricks table named in the route modules as:

- `major_project.news_pipeline.gold_articles`

This table is expected to contain enriched article records with sentiment scores, category labels, channel metadata, processed timestamps, and alert flags.

---

## Frontend Architecture

The frontend is a Vite-based React app that consumes the backend APIs and renders multiple dashboard views.

### Core frontend files

- `frontend/src/main.jsx`
  - App entrypoint and React root renderer

- `frontend/src/App.jsx`
  - Defines client-side routing using `react-router-dom`
  - Loads the shared `Layout` component and page routes

- `frontend/src/api.js`
  - Centralized API client with `fetchDashboard()`, `fetchArticles()`, `fetchChannels()`, `fetchCategories()`, `fetchTrends()`, `fetchProjectInfo()`, and `fetchLineage()` helpers
  - Uses `http://localhost:8001/api` as the default backend base URL

- `frontend/src/components/`
  - Reusable layout and visualization components used across pages

- `frontend/src/pages/`
  - `Dashboard.jsx` – main analytics dashboard
  - `NewsFeed.jsx` – article listing and search
  - `Channels.jsx` – channel comparison and channel stats
  - `Trends.jsx` – sentiment trend charts
  - `ProjectInfo.jsx` – project metadata and lineage details

### Data flow

1. The browser loads the React app from Vite.
2. Pages call `frontend/src/api.js` to fetch JSON data from the backend.
3. The backend queries Databricks and returns structured analytics results.
4. React renders charts, tables, and summaries using the returned data.

---

## Data Pipeline and ETL

This project is designed around a Databricks-style bronze/silver/gold pipeline.

- `01_extract_to_volume.py`
  - Responsible for ingesting raw news data and writing it to a volume or staging area

- `02_volume_to_bronze.py`
  - Reads raw volume data and writes it into a bronze layer with minimal transformation

- `03_bronze_to_silver.py`
  - Cleans and standardizes the bronze records into a silver dataset

- `04_silver_to_gold.py`
  - Enriches silver data with sentiment analysis, classification, and quality metadata into a gold dataset

The frontend and backend are designed to consume the gold-level enriched dataset, so the Databricks scripts are the upstream data preparation stage.

---

## Machine Learning Workspace

The `major project/ml/` directory is a separate workspace focused on machine learning and data collection.

### Contents

- `main.py`
  - Entry script for running the ML workflows

- `data_collection/`
  - Scrapers for websites and video content

- `preprocessing/`
  - Text cleaning and normalization utilities

- `sentiment_analysis/`
  - Sentiment mapping and analysis helpers

- `classification/`
  - Model training and classification logic

### Setup

This ML workspace has its own dependencies in `major project/ml/requirements.txt`.
Install them in a separate virtual environment before running any ML scripts.

---

## Setup and Run Instructions

### 1. Start the Backend

1. Open a terminal and navigate to the backend folder:

```powershell
cd backend
```

2. Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install backend dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in `backend/` with your Databricks connection values:

```text
DATABRICKS_HOST=https://<your-databricks-host>
DATABRICKS_HTTP_PATH=<your-http-path>
DATABRICKS_TOKEN=<your-access-token>
```

5. Start the backend server on the port expected by the frontend:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

6. Confirm the backend is running:

- `http://127.0.0.1:8001/api/health`

> Note: The frontend client expects `http://localhost:8001/api` by default. If you run the backend on a different port, update `frontend/src/api.js` accordingly.

### 2. Start the Frontend

1. Open a new terminal and navigate to `frontend/`:

```powershell
cd frontend
```

2. Install frontend dependencies:

```powershell
npm install
```

3. Start the development server:

```powershell
npm run dev
```

4. Open the browser at the URL shown in the terminal, usually:

- `http://127.0.0.1:5173`

### 3. Access the Application

- Frontend dashboard: `http://127.0.0.1:5173`
- Backend API root: `http://127.0.0.1:8001`

### 4. Run the ML Workspace

If you want to explore the machine learning side, use a separate environment.

```powershell
cd "major project/ml"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then run the relevant script, for example:

```powershell
python main.py
```

---

## Troubleshooting

- If the frontend fails to load data, verify the backend is running on port `8001` or update `frontend/src/api.js`.
- If the backend fails to connect, check `backend/.env` for correct Databricks values and ensure the `databricks-sql-connector` dependency is installed.
- If API responses are empty or slow, confirm that the `gold_articles` table exists in Databricks and contains the expected fields.
- If CORS errors appear, confirm the frontend origin is included in `backend/app/main.py` middleware.

---

## Notes

- The backend depends on Databricks SQL; it is not a standalone database server.
- The `databricks/` scripts represent ETL stages and are intended for use within a Databricks environment or compatible execution context.
- The `major project/ml/` folder is independent and can be used for model development and data collection outside the frontend/backend workflow.
