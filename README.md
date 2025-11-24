# BioGPT

BioGPT is an API that makes proteomic data exploration simple and intuitive through natural language queries. Built on the UniProt biological database, it allows researchers, students, and developers to access complex biological information without needing SQL expertise or specialized file handling. 

By combining semantic search and structured querying, BioGPT connects everyday language with biological data, leveraging modern AI models to interpret questions and deliver human‑readable answers.

## Key Features:
Natural Language Interface: Ask biological questions in plain English.

- **Hybrid AI Engine:** Choose between semantic search (`RAG`) or precise filtering (`Text‑to‑SQL`);
- **Proteomic Focus:** Optimized for protein‑related queries using UniProt data;
- **RESTful API:** Easy integration into bioinformatics pipelines, apps, or research tools.

## Core Technologies

| Layer / Component | Technology | Role |
|-------------------|------------|------|
| **Hybrid Logic** | **RAG (Retrieval-Augmented Generation)** | Handles conceptual queries; interprets semantic meaning and synthesizes narrative answers. |
| **Structured Query** | **Text-to-SQL (Rule-Based)** | Translates natural language into executable SQLite queries for precise filtering and counting. |
| **NLP Models** | **Sentence Transformers (MiniLM)** | Generates embeddings for semantic search (RAG retrieval step). |
| **NLP Models** | **GPT-2 (Open Source)** | Synthesizes coherent, human-readable answers from retrieved biological context (RAG generation step). |
| **Data Infrastructure** | **Pandas & SQLite** | Loads UniProt TSV data into an in-memory SQLite database for fast structured querying. |
| **Web Framework** | **Flask (Python)** | Provides the RESTful API (`/api/biogpt`), handling input validation and JSON output. |

## Engines

- **RAG Engine:** Best for semantic queries and synthesized answers (e.g., *"Describe the function of this protein"*).  
- **Text-to-SQL Engine:** Best for precise filtering and counting (e.g., *"List proteins with mass > 100000"*).  

## API Usage

The BioGPT API exposes a single endpoint for query processing.

### Endpoint

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/biogpt` | Submits a natural language query to the hybrid engine. |

### Setup

1. **Dependencies:**  

   ```bash
   pip install pandas flask sentence-transformers scikit-learn transformers torch accelerate
   ```

2. **Run Application:**  

   ```bash
   cd src
   python app.py
   ```

### Request Body

| Field | Type | Description | Required | Options |
|-------|------|-------------|----------|---------|
| `query` | `string` | Natural language question. | Yes | - |
| `model_type` | `string` | Selects processing engine. Defaults to `rag`. | No | `rag`, `sql` |

### Example: `rag` (Semantic Search)

**Request:**

```json
{
  "query": "What is the primary function of proteins with zinc ion binding activity?",
  "model_type": "rag"
}
```

**Response (partial):**

```json
{
  "model_type": "RAG",
  "user_query": "...",
  "response": "Proteins with zinc ion binding activity, such as Carbonic Anhydrase (CA2) and Carboxypeptidase B2 (CPB2), are typically involved in enzyme catalysis and processes like pH regulation...",
  "retrieved_contexts": [
    // Top 3 relevant contexts
  ],
  "status": "success"
}
```

### Example: `sql` (Text-to-SQL)

**Request:**

```json
{
  "query": "Count how many secreted proteins have a mass above 100000.",
  "model_type": "sql"
}
```

**Response (partial):**

```json
{
  "model_type": "SQL",
  "user_query": "...",
  "sql_query": "SELECT COUNT(*) FROM proteins WHERE Subcellular_location__CC_ LIKE '%Secreted%' AND Mass > 100000",
  "count": 5,
  "data": [
    // Top 5 records matching the filter
  ],
  "status": "success"
}
```