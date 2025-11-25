# BioGPT

BioGPT is an API that makes proteomic data exploration simple and intuitive through natural language queries. Built on the **UniProt** biological database, it allows researchers, students, and developers to access complex biological information without needing SQL expertise or specialized file handling.

By combining semantic search and structured querying, BioGPT connects everyday language with biological data, leveraging modern AI models to interpret questions and deliver human‑readable answers.

## Key Features

* **Natural Language Interface:** Ask biological questions in plain text;
* **Hybrid AI Engine:** Dynamically choose between semantic search (`RAG`) for conceptual questions or precise filtering (`Text‑to‑SQL`) for data extraction;
* **Proteomic Focus:** Optimized for protein‑related queries using UniProt data;
* **RESTful API:** Easy integration into bioinformatics pipelines, apps, or research tools.

## Core Technologies

| Layer / Component | Technology | Role |
|-------------------|------------|------|
| **Hybrid Logic** | **RAG (Retrieval-Augmented Generation)** | Handles conceptual queries; interprets semantic meaning and synthesizes narrative answers. |
| **Structured Query** | **Text-to-SQL (Rule-Based)** | Translates natural language into executable SQLite queries for precise filtering and counting. |
| **NLP Models** | **Sentence Transformers (MiniLM)** | Generates embeddings for semantic search (RAG retrieval step). |
| **NLP Models** | **GPT-2 (Open Source)** | Synthesizes coherent, human-readable answers from retrieved biological context (RAG generation step). |
| **Data Infrastructure** | **Pandas & SQLite** | Loads UniProt TSV data into an in-memory SQLite database for fast, thread-safe structured querying. |
| **Web Framework** | **Flask (Python)** | Provides the RESTful API (`/api/biogpt`), handling input validation and JSON output. |

## Engines

* **RAG Engine:** Best for semantic queries and synthesized answers.
    * *Example:* "Describe the function of this protein."
* **Text-to-SQL Engine:** Best for precise filtering, counting, and numerical comparisons.
    * *Example:* "List proteins with mass > 100000."

## Installation & Setup

### 1. Clone repository

### 2. Install Dependencies
```bash
pip install pandas flask sentence-transformers scikit-learn transformers torch accelerate
````

### 3. Run Application

**Important:** Execute the application from the **project root directory** using the module flag (`-m`) to ensure correct package imports.

```bash
# From the BioGPT/ root directory:
python3 -m src.app
```

> The API will start at `http://127.0.0.1:5000/`

## API Usage

The BioGPT API exposes a single endpoint for all query processing.

### Endpoint

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/biogpt` | Submits a natural language query to the hybrid engine. |

### Request Body

| Field | Type | Description | Required | Options |
|-------|------|-------------|----------|---------|
| `query` | `string` | Natural language question. | Yes | - |
| `model_type` | `string` | Selects processing engine. Defaults to `rag`. | No | `rag`, `sql` |

-----

### Example 1: `rag` (Semantic Search)

**Request:**

```bash
curl -X POST [http://127.0.0.1:5000/api/biogpt](http://127.0.0.1:5000/api/biogpt) \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the primary function of proteins with zinc ion binding activity?", "model_type": "rag"}'
```

**Response (JSON):**

```json
{
  "model_type": "RAG",
  "user_query": "What is the primary function of proteins with zinc ion binding activity?",
  "response": "Proteins with zinc ion binding activity, such as Carbonic Anhydrase (CA2), are typically involved in enzyme catalysis...",
  "retrieved_contexts": [
    {
       "Entry_Name": "CA2_SHEEP",
       "Similarity_Score": "0.8120",
       "Context_Bio": "Protein: Carbonic anhydrase..."
    }
  ],
  "status": "success"
}
```

-----

### Example 2: `sql` (Text-to-SQL)

**Request:**

```bash
curl -X POST [http://127.0.0.1:5000/api/biogpt](http://127.0.0.1:5000/api/biogpt) \
     -H "Content-Type: application/json" \
     -d '{"query": "Count how many secreted proteins have a mass above 100000.", "model_type": "sql"}'
```

**Response (JSON):**

```json
{
  "model_type": "SQL",
  "user_query": "Count how many secreted proteins have a mass above 100000.",
  "sql_query": "SELECT COUNT(*) FROM proteins WHERE Subcellular_location_CC LIKE '%Secreted%' AND Mass > 100000",
  "count": 5,
  "data": [],
  "status": "success"
}
```