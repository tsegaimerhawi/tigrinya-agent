# Tigrinya Agent - Complete Project Overview

## 🎯 Project Purpose

A complete NLP pipeline for processing Tigrinya (Ge'ez script) newspapers, enabling:
- **Document Collection**: Automated scraping of Haddas Ertra newspapers
- **Text Processing**: Cleaning and preprocessing Tigrinya text
- **Linguistic Analysis**: POS tagging and grammatical validation
- **Semantic Search**: Vector database for question answering
- **RAG System**: Retrieval-Augmented Generation for Tigrinya content

---

## 📊 Complete Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACQUISITION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   scraper.py                                                     │
│   └─> Downloads PDFs from shabait.com                           │
│       └─> Creates pdf_metadata.json                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TEXT EXTRACTION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   pdf_processor.py                                               │
│   └─> Extracts text from PDFs                                    │
│   └─> Removes English, noise, navigation elements                │
│   └─> Keeps only Ge'ez script (U+1200-U+137F)                   │
│       └─> Creates raw_data.json                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   preprocessor.py                                                │
│   └─> Fixes OCR character duplication errors                     │
│   └─> Splits text into sentences                                 │
│   └─> Validates Ge'ez script                                    │
│       └─> Creates preprocessed_data.json                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    NLP ANALYSIS LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   main.py (3-Agent Pipeline)                                    │
│   │                                                              │
│   ├─> Agent 1: agent_tagger.py                                  │
│   │   └─> POS Tagging (Noun, Verb, Adjective, Particle)        │
│   │   └─> Uses Gemini 2.5 Flash LLM                             │
│   │   └─> Validates Ge'ez script                                │
│   │                                                              │
│   ├─> Agent 2: agent_critic.py                                  │
│   │   └─> Senior Tigrinya Grammarian                            │
│   │   └─> Validates POS tags                                    │
│   │   └─> Checks prefixes, proper nouns, morphology            │
│   │   └─> Returns PASSED or FEEDBACK                            │
│   │                                                              │
│   └─> Agent 3: agent_refiner.py                                 │
│       └─> Data Engineer                                         │
│       └─> Converts dates to YYYY-MM-DD                         │
│       └─> Generates topic summaries                             │
│       └─> Structures data for storage                           │
│           └─> Creates refined_articles.json                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR STORAGE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Option A: store_data.py                                        │
│   └─> Uses refined_articles.json                                │
│   └─> Generates embeddings (gemini-embedding-001)               │
│   └─> Stores in Qdrant (collection: tigrinya_corpus)           │
│                                                                  │
│   Option B: llama_ingest.py                                      │
│   └─> Uses preprocessed sentences                                │
│   └─> Generates embeddings (gemini-embedding-001)               │
│   └─> Stores in Qdrant (collection: tigrinya_llamaindex)       │
│   └─> Includes rate limiting for free tier                       │
│                                                                  │
│   Option C: run_pipeline.py                                       │
│   └─> Complete pipeline: POS → Critic → Refiner → Qdrant        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL & RAG LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   retriever.py                                                   │
│   └─> Semantic search in Qdrant                                  │
│   └─> Uses cosine similarity                                    │
│                                                                  │
│   agent_rag.py                                                   │
│   └─> RAG Agent                                                  │
│   └─> Retrieves relevant documents                              │
│   └─> Generates answers using Gemini 2.5 Flash                  │
│                                                                  │
│   chat.py / app.py                                               │
│   └─> User interface for Q&A                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow

### **Phase 1: Data Collection**

```bash
python scraper.py
```

**What happens:**
1. Navigates to `https://shabait.com/category/newspapers/haddas-ertra-news/`
2. Collects article URLs across multiple pages (up to 50 pages)
3. Downloads PDFs to `pdfs/` directory
4. Extracts titles, dates, URLs
5. Creates `pdf_metadata.json` with download status

**Output:** `pdfs/*.pdf` + `pdf_metadata.json`

---

### **Phase 2: Text Extraction & Cleaning**

```bash
python pdf_processor.py
```

**What happens:**
1. Reads `pdf_metadata.json`
2. Extracts text from each PDF using `pdfplumber`
3. **Cleaning process:**
   - Removes English words (`\b[a-zA-Z]+\b`)
   - Removes navigation elements (bullets, symbols)
   - Removes page numbers, dates, URLs
   - Removes lines with too many special characters
   - Keeps only Ge'ez script (U+1200-U+137F), numbers, punctuation
4. Calculates word counts
5. Creates `raw_data.json`

**Output:** `raw_data.json` (cleaned Ge'ez text)

---

### **Phase 3: Preprocessing**

```bash
python preprocessor.py
```

**What happens:**
1. Reads `raw_data.json`
2. **Fixes OCR errors:**
   - Detects character duplication (e.g., "ንንኣኣሌሌ" → "ንኣሌ")
   - Removes duplicate characters
3. **Sentence splitting:**
   - Splits text into sentences
   - Validates sentence boundaries
4. Creates `preprocessed_data.json`

**Output:** `preprocessed_data.json` (sentences ready for NLP)

---

### **Phase 4: NLP Analysis (3-Agent Pipeline)**

```bash
python main.py
```

**What happens:**

#### **Agent 1: POS Tagger** (`agent_tagger.py`)
- Uses **Gemini 2.5 Flash** LLM
- Tags each word: Noun, Verb, Adjective, Particle
- Special focus on geopolitical entities
- Validates Ge'ez script purity
- Output: `pos_tags` list

#### **Agent 2: Critic** (`agent_critic.py`)
- **Senior Tigrinya Grammarian** (skeptical)
- Validates POS tags
- Checks for:
  - Missing prefixes (ካ, ኣዝ, ን, ብ, መ)
  - Proper noun accuracy
  - Morphological consistency
- Returns: `PASSED` or `FEEDBACK` list

#### **Agent 3: Refiner** (`agent_refiner.py`)
- **Data Engineer**
- Converts Tigrinya dates → YYYY-MM-DD
- Generates 3-5 word topic summaries
- Structures data for storage
- Creates article IDs
- Output: `refined_articles.json`

**Output:** `complete_pipeline_results.json` + `refined_articles.json`

---

### **Phase 5: Vector Storage**

**Option A: Store Refined Articles**
```bash
python store_data.py
```
- Reads `refined_articles.json`
- Generates embeddings (gemini-embedding-001, 768 dims)
- Stores in Qdrant collection: `tigrinya_corpus`

**Option B: Store Sentences (LlamaIndex)**
```bash
python llama_ingest.py
```
- Reads `preprocessed_data.json` or `pdf_metadata.json`
- Processes in batches (rate limiting for free tier)
- Generates embeddings (gemini-embedding-001, 3072 dims)
- Stores in Qdrant collection: `tigrinya_llamaindex`

**Option C: Complete Pipeline**
```bash
python run_pipeline.py
```
- Runs POS → Critic → Refiner → Qdrant in one go

**Output:** Qdrant vector database with embeddings

---

### **Phase 6: Question Answering (RAG)**

```bash
python agent_rag.py
# or
python chat.py
```

**What happens:**
1. User asks a question (in Tigrinya or English)
2. **Retriever** (`retriever.py`):
   - Generates query embedding
   - Searches Qdrant using cosine similarity
   - Returns top-k relevant documents
3. **RAG Agent** (`agent_rag.py`):
   - Formats retrieved context
   - Sends to Gemini 2.5 Flash LLM
   - Generates answer based on context
4. Returns answer to user

**Example:**
```
Q: ኤርትራ ኣብ ኣድዋ እንታይ ኣጋጢሙ?
A: [Answer based on retrieved newspaper articles]
```

---

## 🗂️ Key Files & Their Roles

### **Data Collection**
- `scraper.py` - Downloads PDFs from shabait.com
- `pdf_processor.py` - Extracts and cleans text from PDFs

### **Preprocessing**
- `preprocessor.py` - Fixes OCR errors, splits sentences

### **NLP Agents**
- `agent_tagger.py` - POS tagging with Gemini LLM
- `agent_critic.py` - Grammatical validation
- `agent_refiner.py` - Data structuring and date normalization
- `main.py` - Orchestrates 3-agent pipeline

### **Vector Storage**
- `store_data.py` - Stores refined articles in Qdrant
- `llama_ingest.py` - Stores sentences in Qdrant (with rate limiting)
- `run_pipeline.py` - Complete pipeline with storage

### **Retrieval & RAG**
- `retriever.py` - Semantic search in Qdrant
- `agent_rag.py` - RAG agent for Q&A
- `chat.py` - Chat interface
- `app.py` - Web interface (if available)

### **Utilities**
- `check_qdrant.py` - Verify Qdrant connection
- `list_models.py` - List available Google AI models
- `validate_results.py` - Validate processed data

---

## 🔧 Configuration

### **Environment Variables**
```bash
# .env_config or .env
GOOGLE_API_KEY=your_api_key_here
```

### **Qdrant Setup**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### **Dependencies**
- `playwright` - Web scraping
- `pdfplumber` - PDF text extraction
- `langchain-google-genai` - LLM integration
- `qdrant-client` - Vector database
- `llama-index` - Document processing (optional)

---

## 📈 Data Flow Summary

```
PDFs → Text Extraction → Cleaning → Preprocessing
  ↓
POS Tagging → Grammatical Validation → Data Refinement
  ↓
Embedding Generation → Vector Storage (Qdrant)
  ↓
Semantic Search → RAG → Answer Generation
```

---

## 🎯 Use Cases

1. **Document Digitization**: Convert PDF newspapers to searchable text
2. **Linguistic Research**: POS tagging and grammatical analysis
3. **Semantic Search**: Find relevant articles by meaning
4. **Question Answering**: Ask questions about Tigrinya news/history
5. **Corpus Building**: Create structured Tigrinya language corpus

---

## 🚀 Quick Start

```bash
# 1. Collect data
python scraper.py

# 2. Extract text
python pdf_processor.py

# 3. Preprocess
python preprocessor.py

# 4. Run NLP pipeline
python main.py

# 5. Store in vector DB
python llama_ingest.py --batch-size 30 --batch-delay 90

# 6. Ask questions
python agent_rag.py
```

---

## 📊 Output Files

- `pdf_metadata.json` - Download tracking
- `raw_data.json` - Cleaned text
- `preprocessed_data.json` - Sentences
- `refined_articles.json` - Structured NLP data
- `complete_pipeline_results.json` - Full pipeline results
- Qdrant collections: `tigrinya_corpus`, `tigrinya_llamaindex`

---

This is a **complete end-to-end NLP pipeline** for Tigrinya language processing! 🎉
