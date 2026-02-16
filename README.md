# Bitcoin Bet Suggester

This application performs a series of calculations and analyses various market data points (derivatives, news sentiment, etc.) to determine if a bet should be made on Bitcoin's price going up or down. It then exposes this betting suggestion and related attributes via a REST API, and also provides a dashboard.

## Features

*   **Data Collection:** Gathers real-time data from various sources including market data, derivatives, news, and Polymarket.
*   **Signal Engine:** Processes collected data to generate signals and a final betting recommendation (UP/DOWN/NEUTRAL) with a confidence score.
*   **REST API:** Provides programmatic access to the latest betting suggestion, signal attributes, and underlying data.
*   **Dashboard:** (Presumed, based on `app.py` rendering `index.html`) A web interface to visualize the analysis and signals.

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd dev_bit # Or your project directory
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` is presumed to exist based on `pip install -r requirements.txt` as a common setup step. If it doesn't, you might need to create it manually or install Flask, APScheduler, etc., individually.*

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will start a Flask server, typically on `http://0.0.0.0:5124`.
    The data refreshing process runs in the background and might take some moments to fetch initial data.

## API Endpoints

The application exposes several REST API endpoints. All responses are in JSON format.

### `/api/bet-suggestion` (NEW)

This endpoint provides the final betting recommendation, a count of the individual "up" and "down" signals contributing to the decision, and the current Polymarket line.

*   **URL:** `/api/bet-suggestion`
*   **Method:** `GET`
*   **Response Example:**
    ```json
    {
      "final_signal": {
        "direction": "UP",
        "confidence": 0.75,
        "weighted_score": 15.2
      },
      "up_attributes_count": 3,
      "down_attributes_count": 1,
      "polymarket_line": {
        "question": "Will Bitcoin be above $X by Y date?",
        "options": {
          "Yes": 0.6,
          "No": 0.4
        },
        "url": "https://polymarket.com/market/..."
      },
      "timestamp": "2026-02-16T12:30:00Z"
    }
    ```
*   **How to call (example using `curl`):**
    ```bash
    curl http://localhost:5124/api/bet-suggestion
    ```

### Other Endpoints

*   **`/api/dashboard-data`**: Returns the full dashboard state including all signals and data.
*   **`/api/signal`**: Returns just the current signal recommendation, BTC price, and odds value.
*   **`/api/news`**: Returns the latest news headlines and sentiment analysis.
*   **`/api/derivatives`**: Returns derivatives data (funding, open interest, long/short ratio, liquidations).
*   **`/api/polymarket`**: Returns current Polymarket market context.
*   **`/api/signal-history`**: Returns a history of recent signals.
*   **`/api/health`**: Health check endpoint.
