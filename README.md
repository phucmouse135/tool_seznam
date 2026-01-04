# Automation Tool

## Introduction
This project is a robust automation tool built using Python and Playwright. It is designed to execute multi-threaded browser automation tasks efficiently, featuring built-in proxy management, retry mechanisms, and integration with SMS verification services (OnlineSim).

## Folder Overview
- **`app/`**: Contains the core application logic and modules.
- **`data/`**: Directory for input and output data.
  - `input.txt`: Place your input data here (e.g., account credentials).
  - `success.txt`: Records successfully processed items.
  - `failed.txt`: Records items that failed processing.
- **`logs/`**: Stores runtime logs for monitoring and debugging.
- **`reports/`**: Generated reports from automation sessions.
- **`storage/`**: Used for persistent storage, such as browser contexts or cookies.
- **`utils.py`**: Utility helper classes for Logging, Proxy management, Browser control, and File operations.
- **`config.py`**: Central configuration file for the application.
- **`main.py`**: The main entry point script that orchestrates the worker threads.

## How to Run

### Prerequisites
- Python 3.12 or higher
- Google Chrome (optional, Playwright installs its own binaries)

### Installation

1.  **Clone the repository** (if applicable) or navigate to the project folder.

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers**:
    ```bash
    playwright install chromium
    ```

### Configuration

1.  **Environment Variables**:
    Create a `.env` file in the root directory. You can refer to `config.py` to see which variables are used (e.g., Proxy API URLs, API Keys).

2.  **Input Data**:
    Prepare your data in `data/input.txt`. The expected format is typically:
    ```text
    username|password
    ```

### Usage

**Run the main automation worker:**
```bash
python main.py
```

**Fetch OnlineSim tariffs:**
```bash
python get_tariffs_to_json.py
```
