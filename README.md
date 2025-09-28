# 100 Days of Problem Solving Tracker

Track Codeforces handles for 100 Days of problem solving challenge.

Currently supports only Codeforces.

# Features

- Scrapes Codeforces profiles to track problem-solving activity
- Generates daily reports in CSV format
- Generates a summary report of total problems solved by each user

# Requirements
- Python 3.x
- requests

# Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/fardinkamal62/100_days_of_CP_scraper
    ```
2. Navigate to the project directory:
    ```bash
    cd 100_days_of_CP_scraper
    ```
3. Initialize a virtual environment (optional but recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
4. Install the required packages:
    ```bash
    pip install requests
    ```

# Arguments
- `fetch_date` (optional): The date for which to fetch data.

    **Format:** YYYY-MM-DD. Defaults to today's date if not provided.
- `start_date` (optional): The start date of the 100 days challenge.
    
    **Format:** YYYY-MM-DD. Defaults to September 1, 2025 if not provided.


# Usage
1. Add Codeforces handles to `handles.txt`, one per line.
2. Run the scraper:
    
    - For today's data:
    ```bash
    python scraper.py
    ```
    - For a specific date (format: YYYY-MM-DD):
    ```bash
    python scraper.py YYYY-MM-DD
    ```
    Example:
    ```bash
    python scraper.py 2025-09-28
    ```

    - For a specific date with a custom start date (format: YYYY-MM-DD):
    ```bash
    python scraper.py YYYY-MM-DD YYYY-MM-DD
    ```
    Example start date is September 1, 2025 and fetch date is September 28, 2025:
    ```bash
    python scraper.py 2025-09-28 2025-09-01
    ```
3. Check the generated CSV files for daily reports(`daily_log.csv`) and summary reports(`progress.csv`).



# Used By
- [Dhaka International University Computer Programming Club](https://www.facebook.com/diucsecpc) for tracking their 2025 100 Days of Problem Solving challenge.