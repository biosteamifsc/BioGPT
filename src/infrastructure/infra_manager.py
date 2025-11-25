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
    Stores the thread-safe DB path (string) instead of connection objects.
    """
    def __init__(self, tsv_file: str = Config.TSV_FILE):
        self.tsv_file = tsv_file
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
            # Replace special characters with underscores
            new_col = new_col.replace(' ', '_').replace('[', '_').replace(']', '_').replace('(', '_').replace(')', '_').replace('-', '_').replace('/', '_').replace('\\', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace(':', '_')
            # Deduplicate underscores
            while '__' in new_col:
                new_col = new_col.replace('__', '_')
            # Strip leading/trailing underscores
            new_col = new_col.strip('_')
            # Handle numeric starts
            if new_col and new_col[0].isdigit():
                new_col = 'col_' + new_col
            sanitized[str(col)] = new_col
        return sanitized

    def _create_nlp_context(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """Aggregates key textual columns into a single 'Context_NLP' column."""
        def get_sanitized_name(original_name):
            return column_mapping.get(original_name, original_name)
            
        # Safety check: ensure columns exist before concatenation
        try:
            df['Context_NLP'] = (
                "Protein: " + df[get_sanitized_name('Protein names')].astype(str) + ". " +
                "Organism: " + df[get_sanitized_name('Organism')].astype(str) + ". " +
                "Subcellular Location: " + df[get_sanitized_name('Subcellular location [CC]')].astype(str) + ". " +
                "Biological Process: " + df[get_sanitized_name('Gene Ontology (biological process)')].astype(str) + ". " +
                "Molecular Function: " + df[get_sanitized_name('Gene Ontology (molecular function)')].astype(str)
            )
        except KeyError as e:
            print(f"WARNING: Missing column for NLP context: {e}")
            df['Context_NLP'] = ""
            
        return df

    def _setup_database(self, df_data: pd.DataFrame) -> bool:
        """Sets up the temporary SQLite database and populates it."""
        try:
            # Creates the file path
            self.temp_db_name = tempfile.NamedTemporaryFile(suffix='.db', delete=False).name
            
            # Use a temporary connection to load data
            with sqlite3.connect(self.temp_db_name) as conn:
                df_data.to_sql(Config.DB_TABLE_NAME, conn, if_exists='replace', index=False)
            
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
                print(f"INFO: Generating embeddings for {len(df_data)} records...")
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

            # 2. Setup DB (creates file and closes connection)
            if not self._setup_database(self.df_data):
                return False
                
            # 3. Setup NLP
            if not self._setup_nlp_models(self.df_data):
                return False

            return True

        except Exception as e:
            print(f"ERROR: Infrastructure initialization failed: {e}")
            return False

    def cleanup(self):
        """Deletes the temporary file."""
        if self.temp_db_name and os.path.exists(self.temp_db_name):
            os.unlink(self.temp_db_name)