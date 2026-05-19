```markdown
# HTW Berlin Modules Scraper 🎓💻

A robust Python automation script built to systematically extract all degree programs (Studiengänge) and their corresponding study modules (courses) from the official [HTW Berlin website](https://www.htw-berlin.de/). The script navigates dynamic web pages, locates the official Study and Examination Regulations (StPO) PDF files, extracts the module names directly from the PDF tables, and compiles a clean, structured JSON database.

## ✨ Features

* **Dynamic Web Scraping:** Uses `Selenium` to handle JavaScript-rendered components and dynamic routing on the university's website.
* **Deep Navigation Logic:** Employs a smart prioritization algorithm to search for PDF files. If the StPO is not on the main program page, the script automatically scans and navigates through relevant sub-tabs (e.g., `Ordnungen`, `Studienablauf`, `Studium`).
* **Strict PDF Filtering:** Avoids false positives by strictly matching URLs and link texts against specific keywords (like `StPO`, `AMBl`, `_BA.pdf`), while actively ignoring general university administrative documents (e.g., `Satzung`, `Ausschuss`).
* **In-Memory PDF Parsing:** Uses `requests` and `pdfplumber` to download and parse PDF files directly in memory without cluttering the local storage.
* **Automated Data Structuring:** Cleans and exports the extracted data into a ready-to-use `JSON` format, ideal for database seeding (e.g., Supabase, PostgreSQL, MongoDB).

## 🛠️ Prerequisites

Before running this script, ensure you have the following installed:

* **Python 3.8+**
* **Google Chrome** browser installed on your machine.
* The following Python libraries:

```bash
pip install selenium pdfplumber requests

```

## 🚀 Usage

1. Clone this repository to your local machine.
2. Navigate to the project directory.
3. Run the script:

```bash
python scraper.py

```

*Note: The script runs with the browser visible (`detach: True`) by default to allow manual handling of Cookie consent banners if they block navigation. You can change it to `--headless` in the `webdriver.ChromeOptions()` for background execution.*

## 📂 Output Structure

Once the script completes execution, it generates a file named `htw_modules.json` in the root directory. The JSON structure looks like this:

```json
[
    {
        "fachbereich": "Not specified",
        "studiengang": "Bachelor Angewandte Informatik",
        "url": "[https://ai.htw-berlin.de/](https://ai.htw-berlin.de/)",
        "module": [
            "Programmierung 1",
            "Datenbanken",
            "Software Engineering",
            "..."
        ]
    },
    ...
]

```

## ⚠️ Important Notes

* **Execution Time:** The script visits over 80 program pages, downloads PDFs, and parses tables. It may take between 5 to 10 minutes to complete.
* **Website Structure Changes:** This script relies on the current HTML structure and CSS classes of the HTW Berlin website. If the university significantly updates its UI, the CSS selectors in the script may need adjustment.
* **PDF Layout Variations:** Module extraction assumes the module names are located in the second column (`row[1]`) of the PDF tables, which is the standard format for most HTW StPO documents. Edge cases with different table structures might require manual addition or script adjustments.

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```
