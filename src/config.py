class Config:
    """Stores all application-wide configuration constants."""
    TSV_FILE = 'db/uniprot.tsv' 
    DB_TABLE_NAME = 'proteins' 
    DEFAULT_TOP_RESULTS = 5
    
    # NLP Model Constants
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    GENERATOR_MODEL = 'gpt2'
    MAX_NEW_TOKENS = 150
    EMBEDDINGS_FILE = 'embeddings_proteomic.npy'

    # Mapping of user intent to sanitized column names (for Text-to-SQL)
    # ATENÇÃO: 'location' ajustado para 'Subcellular_location_CC' (um único underscore)
    SQL_COL_MAP = {
        "mass": "Mass", 
        "length": "Length", 
        "location": "Subcellular_location_CC",
        "process": "Gene_Ontology__biological_process_", 
        "function": "Gene_Ontology__molecular_function_",
        "coagulation": "Gene_Ontology__biological_process_", 
        "inhibitor": "Gene_Ontology__molecular_function_"
    }