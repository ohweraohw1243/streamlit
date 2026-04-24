# Streamlit Business Analytics Dashboard

An interactive business analytics dashboard built with Streamlit that allows users to upload data files, visualize trends, and generate PDF reports.

## Features

- **File Upload**: Support for Excel (.xlsx) and CSV files
- **Data Storage**: SQLite database for persistent data storage
- **Interactive Charts**: Plotly-powered visualizations
- **PDF Reports**: Generate professional PDF reports from analysis

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`

## Project Structure

- `main.py` - Streamlit app entry point
- `config.py` - Configuration and constants
- `data/` - Data handling modules (file upload, database, processing)
- `visualization/` - Chart and dashboard components
- `reports/` - PDF report generation
- `utils/` - Helper utilities
- `db/` - SQLite database storage
- `uploads/` - Temporary file upload directory

## Requirements

- Python 3.11
- Streamlit
- Pandas
- Plotly
- SQLite3
- openpyxl
- fpdf2

## License

MIT
