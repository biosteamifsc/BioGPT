import pandas as pd
import sqlite3
import os
import tempfile
import numpy as np
from typing import Dict, Optional, Any
from sentence_transformers import SentenceTransformer
from transformers import pipeline

from ..config import Config

class InfraManager:
    """
    Consolidates DB and NLP infrastructure initialization.
    Responsible for loading data, setting up DB, and loading all external models.
    """
    def __init__(self, tsv_file: str = Config.TSV_FILE):
        self.tsv_file = tsv_file
        self.db_conn: Optional[sqlite3.Connection] = None
        self.temp_db_name: Optional[str] = None
        self.column_mapping: Dict[str, str] = {}
        self.df_data: Optional[pd.DataFrame] = None 
        self.nlp_model: Optional[SentenceTransformer] = None
        self.embeddings: Optional[np.ndarray] = None
        self.generator: Optional[Any] = None

    def _sanitize_column_names(self, columns: pd.Index) -> Dict[str, str]:
        """Creates valid SQL column names from the raw TSV headers."""
        sanitized = {}
        for col in columns:
            new_col = str(col).strip()
            new_col = new_col.replace(' ', '_').replace('[', '_').replace(']', '_').replace('(', '_').replace(')', '_').replace('-', '_').replace('/', '_').replace('\\', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace(':', '_')
            while '__' in new_col:
                new_col = new_col.replace('__', '_')
            new_col = new_col.strip('_')
            if new_col and new_col[0].isdigit():
                new_col = 'col_' + new_col
            sanitized[str(col)] = new_col
        return sanitized

    def _create_nlp_context(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """Aggregates key textual columns into a single 'Context_NLP' column."""
        def get_sanitized_name(original_name):
            for original, sanitized in column_mapping.items():
                if original == original_name:
                    return sanitized
            return original_name
            
        df['Context_NLP'] = (
            "Protein: " + df[get_sanitized_name('Protein names')] + ". " +
            "Organism: " + df[get_sanitized_name('Organism')] + ". " +
            "Subcellular Location: " + df[get_sanitized_name('Subcellular location [CC]')] + ". " +
            "Biological Process: " + df[get_sanitized_name('Gene Ontology (biological process)')] + ". " +
            "Molecular Function: " + df[get_sanitized_name('Gene Ontology (molecular function)')]
        )
        return df

    def _setup_database(self, df_data: pd.DataFrame) -> bool:
        """Sets up the temporary SQLite database and populates it."""
        try:
            self.temp_db_name = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
            self.db_conn = sqlite3.connect(self.temp_db_name)
            df_data.to_sql(Config.DB_TABLE_NAME, self.db_conn, if_exists='replace', index=False)
            return True
        except Exception as e:
            print(f"ERROR in DB setup: {e}")
            return False

    def _setup_nlp_models(self, df_data: pd.DataFrame) -> bool:
        """Loads embedding model, pre-calculates embeddings, and loads the generative model."""
        try:
            # 1. Load Embedding Model
            self.nlp_model = SentenceTransformer(Config.EMBEDDING_MODEL)
            
            # 2. Load or Generate Embeddings
            if os.path.exists(Config.EMBEDDINGS_FILE):
                self.embeddings = np.load(Config.EMBEDDINGS_FILE)
            else:
                print(f"INFO: Generating embeddings for {len(df_data)} records (one-time process)...")
                self.embeddings = self.nlp_model.encode(df_data['Context_NLP'].tolist(), show_progress_bar=False)
                np.save(Config.EMBEDDINGS_FILE, self.embeddings)
            
            # 3. Load Generative Model
            self.generator = pipeline("text-generation", model=Config.GENERATOR_MODEL, max_new_tokens=Config.MAX_NEW_TOKENS)
            return True
        except Exception as e:
            print(f"ERROR in NLP setup: {e}")
            return False

    def initialize_infrastructure(self) -> bool:
        """Performs all necessary initializations."""
        if not os.path.exists(self.tsv_file):
            print(f"ERROR: TSV file not found at expected path: {self.tsv_file}")
            return False
            
        try:
            # 1. Load Data and Process Columns
            df = pd.read_csv(self.tsv_file, sep='\t', low_memory=False).fillna('')
            self.column_mapping = self._sanitize_column_names(df.columns)
            df_renamed = df.rename(columns=self.column_mapping)
            self.df_data = self._create_nlp_context(df_renamed, self.column_mapping)

            # 2. Setup DB
            if not self._setup_database(self.df_data):
                return False
                
            # 3. Setup NLP
            if not self._setup_nlp_models(self.df_data):
                return False

            return True

        except Exception as e:
            print(f"ERROR: Infrastructure initialization failed: {e}")
            return False

    def execute_query(self, query: str) -> pd.DataFrame | str:
        """Executes a given SQL query."""
        if self.db_conn is None:
            return "Database connection not established."

        try:
            result = pd.read_sql_query(query, self.db_conn)
            return result
        except Exception as e:
            return f"SQL Execution Error: {e}."

    def cleanup(self):
        """Closes the DB connection and deletes the temporary file."""
        if self.db_conn:
            self.db_conn.close()
        if self.temp_db_name and os.path.exists(self.temp_db_name):
            os.unlink(self.temp_db_name)