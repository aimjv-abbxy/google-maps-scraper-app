# Advanced Google Maps Lead Generation Scraper

A sophisticated desktop application built with Python to automate the process of scraping business lead data from Google Maps. This tool provides a user-friendly interface to generate targeted lead lists for any keyword or location worldwide.

![placeholder for a gif of the app in action](https://placehold.co/800x400?text=Your+App+In+Action.gif)
*(Suggestion: After the app is complete, you can record a short GIF of it working and replace the placeholder link above!)*

---

### About The Project

Finding leads for sales and marketing is often a tedious, manual process of searching on Google Maps and copy-pasting information. This project was built to solve that problem entirely. It provides a simple desktop app that acts as a powerful engine for building lead lists, capable of gathering thousands of unique business profiles automatically.

The application is designed to be resilient and user-friendly, handling modern web challenges like dynamic content and infinite scrolling, while preventing duplicate entries and saving data in a clean, ready-to-use format.

### Key Features

* **Customizable Searches:** Scrape data using any keyword, city/state/province, and country.
* **Dynamic Page Handling:** Intelligently scrolls through "infinite scroll" result lists to find all available leads.
* **Robust Data Extraction:** Clicks on each list item to scrape detailed information from the business's profile page.
* **Duplicate Prevention:** Keeps track of previously scraped businesses (based on address) to ensure the final list is unique, even across multiple runs.
* **Continue Previous Sessions:** Users can choose to continue a previous scrape, and the application will load the old data to avoid re-scraping the same leads.
* **User-Friendly GUI:** A clean and simple interface built with CustomTkinter lets any user run the scraper without touching the code.
* **Real-Time Logging:** See the scraper's progress live in the application's log window.
* **Headless Mode:** Option to run the scraper in the background without a visible browser window for faster performance.

### Built With

This project was built using the following key technologies:

* **Python**
* **Selenium** for browser automation and scraping
* **CustomTkinter** for the modern graphical user interface (GUI)

---

### Getting Started

To get a local copy up and running, follow these simple steps.

#### Prerequisites

Make sure you have Python and Git installed on your system.
* [Python](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

Installation

1.  Clone the repository:**
    ```sh
    git clone [https://github.com/aimjv-abbxy/google-maps-scraper-app.git](https://github.com/aimjv-abbxy/google-maps-scraper-app.git)
    ```
2.  Navigate to the project directory:**
    ```sh
    cd google-maps-scraper-app
    ```
3.  Create and activate a virtual environment:**
    On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * On macOS & Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
4. Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

Usage

1.  Make sure your virtual environment is activated.
2.  Run the application with the following command:
    ```sh
    python main_app.py
    ```
3.  Fill in the input fields in the application window and click "Start Scraping".

---

License

Distributed under the MIT License. See `LICENSE` for more information.
