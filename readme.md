# AgroFlow - Produce Distribution Management

AgroFlow is a modern, professional desktop application designed for a produce distribution company. It provides a centralized platform to manage daily orders, dynamic pricing, customer relationships, and a unique vendor fulfillment workflow.

## Features

*   **Modern UI:** A clean, visually appealing interface built with CustomTkinter.
*   **Theming:** Supports Light, Dark, and System appearance modes.
*   **Secure Login:** Hashed passwords and session management.
*   **Order Management:** A streamlined workflow for taking customer orders.
*   **Vendor Fulfillment:** A simulated vendor interface to update daily prices and stock.
*   **CRM:** Full CRUD (Create, Read, Update, Delete) for customer records.
*   **Inventory:** Full CRUD for a master product list.
*   **Bulk Import:** Import customers and products from CSV files.

## Setup & Installation

1.  **Prerequisites:**
    *   Python 3.8 or newer must be installed on your system.

2.  **Clone the Repository (or create the files):**
    If you have git, clone this project. Otherwise, create the `agroflow` directory and place the `app.py`, `database.py`, and `requirements.txt` files inside it. Create the `assets/` and `assets/icons/` subdirectories.

    ```bash
    git clone <repository-url>
    cd agroflow
    ```

3.  **Create a Virtual Environment (Recommended):**
    It's best practice to create a virtual environment to keep project dependencies isolated.

    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    Install the required Python packages using pip.

    ```bash
    pip install -r requirements.txt
    ```

5.  **Add Assets (Optional but Recommended):**
    *   Place a `logo.png` file in the `agroflow/assets/` directory for the login screen.
    *   Place 24x24 pixel PNG icons named `home.png`, `customers.png`, `inventory.png`, and `settings.png` into the `agroflow/assets/icons/` directory for the best visual experience.

## How to Run

Execute the `app.py` script from the root of the `agroflow` directory.

```bash
python app.py
```

The application window will open, starting with the login screen.

**Default Login:**
*   **Username:** `admin`
*   **Password:** `admin`

The database file `agroflow.db` will be automatically created in the `data/` folder upon first run.