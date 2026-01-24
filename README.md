# Tigrinya Agent - Haddas Ertra Newspaper Scraper & Processor

A comprehensive tool for scraping, downloading, and processing Haddas Ertra Tigrinya newspapers from shabait.com. Extracts clean Ge'ez script text suitable for NLP and AI applications.

## Features

- 🕷️ **Automated Scraping**: Downloads up to 20+ Haddas Ertra newspaper PDFs
- 📄 **Multi-page Navigation**: Handles pagination to access older articles
- 🔍 **Smart PDF Detection**: Locates download links using image-based navigation
- 🧹 **Text Cleaning**: Removes English words, navigation elements, and noise
- 🌍 **Ge'ez Script Focus**: Preserves only Tigrinya characters, numbers, and punctuation
- 📊 **Metadata Tracking**: Complete tracking of download and processing status
- 🔄 **Batch Processing**: Handles multiple PDFs efficiently

## Installation

### Prerequisites

- Python 3.8+
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/tsegaimerhawi/tigrinya-agent.git
cd tigrinya-agent
```

### Step 2: Create Virtual Environment

```bash
python -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

## Usage

### Step 1: Scrape and Download PDFs

Run the scraper to download Haddas Ertra newspapers:

```bash
python scraper.py
```

This will:
- Navigate to shabait.com Haddas Ertra section
- Collect article URLs across multiple pages
- Download PDFs using direct links
- Save metadata to `pdf_metadata.json`

### Step 2: Process and Extract Text

Process the downloaded PDFs to extract clean Tigrinya text:

```bash
python pdf_processor.py
```

This will:
- Extract text from all downloaded PDFs using pdfplumber
- Clean text to remove English words and navigation elements
- Keep only Ge'ez script characters (መበል, ዓመት, ኤርትራውያን, etc.)
- Save structured JSON to `raw_data.json`

### Step 3: Validate Results

Check the processing results:

```bash
python validate_results.py
```

This shows:
- Total PDFs processed
- Word counts per article
- Confirmation of English word removal

## File Structure

```
tigrinya-agent/
├── scraper.py              # PDF downloader and scraper
├── pdf_processor.py        # Text extraction and cleaning
├── validate_results.py     # Results validation script
├── pdf_metadata.json       # Download tracking metadata
├── raw_data.json          # Processed text data
├── requirements.txt       # Python dependencies
├── pdfs/                  # Downloaded PDF files (gitignored)
└── README.md              # This file
```

## Output Format

### raw_data.json Structure

```json
[
  {
    "index": 1,
    "news_title": "Haddas Ertra 23 January 2026",
    "article_url": "https://shabait.com/2026/01/23/haddas-ertra-23-january-2026/",
    "publication_date": "On Jan 23, 2026",
    "pdf_filename": "On Jan 23, 2026_Haddas Ertra 23 January 2026.pdf",
    "pdf_url": "http://www.erinewspapers.com/hadas-eritrea/haddas_eritra_23012026.pdf",
    "extracted_text": "መበል ዓመት ቁ. ዓርቢ ጥሪ ገጻት ናቕፋ ገገጽጽ...",
    "word_count": 12732,
    "processing_status": "completed"
  }
]
```

## Configuration

### Changing Number of Articles

Edit `scraper.py` and modify the `max_articles` variable:

```python
max_articles = 20  # Change this number
```

### Rate Limiting

The scraper includes 4-second delays between downloads. Adjust in `scraper.py`:

```python
time.sleep(4)  # Change delay time
```

## Text Cleaning Features

The processor performs comprehensive cleaning:

1. **Noise Removal**: PAGE numbers, prices, URLs, copyright text
2. **English Word Removal**: All ASCII letter sequences
3. **Navigation Elements**: Bullets (•), special characters (), menu items
4. **Character Filtering**: Keeps only Ge'ez script (፡።፣፤፥፦፧፨) + numbers + punctuation
5. **Whitespace Cleanup**: Normalizes spacing and line breaks

## Troubleshooting

### Common Issues

**"No PDF link found"**
- Some articles may not have downloadable PDFs
- Check if the article page structure has changed

**"Download failed"**
- Network timeouts - the script retries automatically
- Server blocking - increase delays between requests

**"No Ge'ez text found"**
- PDF may be image-based rather than text-based
- OCR would be needed for image PDFs

### Manual Verification

Check downloaded PDFs:
```bash
ls -la pdfs/
```

Validate metadata:
```bash
python -c "import json; print(len(json.load(open('pdf_metadata.json'))))"
```

## Dependencies

- **playwright**: Web scraping and browser automation
- **pdfplumber**: PDF text extraction
- **requests**: HTTP downloads
- **pandas** (future): Data analysis features

## License

This project is for educational and research purposes. Please respect website terms of service and copyright laws when using the scraped content.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Author

Tsegai Merhawi - Tigrinya NLP and newspaper digitization project
