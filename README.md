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
curl -X POST http://127.0.0.1:5000/api/biogpt \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the role of Complement C1q in the immune system?", "model_type": "rag"}'
```

**Response (JSON):**

```json
{
   "model_type":"RAG",
   "response":"What is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the immune system?\n\nWhat is the role of Complement C1q in the",
   "retrieved_contexts":[
      {
         "Context_Bio":"Protein: Glucan endo-1,3-beta-D-glucosidase 1 (Endo-1,3-beta-glucanase 1) (EC 3.2.1.39) (Laminarinase) (RmLam81A). Organism: Rhizomucor miehei. Subcellular Location: SUBCELLULAR LOCATION: Secreted, cell wall {ECO:0000250|UniProtKB:P53753}.. Biological Process: cell wall organization [GO:0071555]; polysaccharide catabolic process [GO:0000272]. Molecular Function: endo-1,3(4)-beta-glucanase activity [GO:0052861]; glucan endo-1,3-beta-D-glucosidase activity [GO:0042973]",
         "Entry_Name":"ENG1_RHIMI",
         "Similarity_Score":"0.7025"
      },
   ],
   "status":"success",
   "user_query":"What is the role of Complement C1q in the immune system?"
}
```

-----

### Example 2: `sql` (Text-to-SQL)

**Request:**

```bash
curl -X POST http://127.0.0.1:5000/api/biogpt      -H "Content-Type: application/json"      -d '{"query": "Count how many proteins are secreted.", "model_type": "sql"}'
```

**Response (JSON):**

```json
{
   "count":33597,
   "data":[
      
   ],
   "message":"Query executed successfully, found 33597 records.",
   "model_type":"SQL",
   "sql_query":"SELECT COUNT(*) FROM proteins WHERE 1=1 AND Subcellular_location_CC LIKE '%Secreted%'",
   "status":"success",
   "user_query":"Count how many proteins are secreted."
}
```