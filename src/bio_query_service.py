import pandas as pd
import sqlite3
import os
from typing import Dict, Any, Optional

from .config import Config
from .infrastructure.infra_manager import InfraManager
from .domain.context import ServiceContext
from .domain.text_to_sql_engine import TextToSqlEngine
from .domain.rag_engine import RAGEngine

# --- PUBLIC API STATE AND FUNCTIONS ---

global_service_context: Optional[ServiceContext] = None
global_infra_manager: Optional[InfraManager] = None 

def execute_sql_query_thread_safe(query: str, db_path: str) -> pd.DataFrame | str:
    """
    Opens a connection, executes a SQL query, and closes the connection 
    immediately (making it thread-safe for Flask).
    """
    try:
        # Connection is created in the current thread (thread-safe!)
        with sqlite3.connect(db_path) as conn:
            result = pd.read_sql_query(query, conn)
            return result
    except Exception as e:
        return f"SQL Execution Error: {e}"


def initialize_bio_service() -> bool:
    """Initializes the entire BioGPT service."""
    global global_service_context, global_infra_manager
    
    if not os.path.exists(Config.TSV_FILE):
        print(f"FATAL: {Config.TSV_FILE} not found.")
        return False

    # 1. Initialize Infrastructure
    global_infra_manager = InfraManager()
    if not global_infra_manager.initialize_infrastructure():
        return False
        
    # 2. Create Global Context
    global_service_context = ServiceContext(global_infra_manager)
    
    print("BioGPT Service initialization successful.")
    return True

def shutdown_bio_service():
    """Cleans up resources."""
    if global_infra_manager:
        global_infra_manager.cleanup()

def process_hybrid_query(user_query: str, model_type: str = 'rag') -> Dict[str, Any]:
    """Main entry point for the hybrid query engine."""
    if global_service_context is None:
        return {"status": "error", "message": "Service not initialized."}

    results: Dict[str, Any] = {
        "status": "success", "model_type": model_type.upper(), "user_query": user_query
    }
    
    context = global_service_context

    # --- RAG Model Execution ---
    if model_type.lower() == 'rag':
        rag_engine = RAGEngine(context)
        results['response'] = rag_engine.generate_response(user_query)
        results['retrieved_contexts'] = rag_engine.semantic_search(user_query)
        
    # --- SQL Model Execution ---
    elif model_type.lower() == 'sql':
        sql_engine = TextToSqlEngine(context)
        
        # 1. Translate
        sql_query = sql_engine.translate_query(user_query)
        results['sql_query'] = sql_query
        
        # 2. Execute (Thread-Safe using DB Path from context)
        if context.db_path is None:
             return {"status": "error", "message": "Database path missing."}

        query_result = execute_sql_query_thread_safe(sql_query, context.db_path)
        
        # 3. Format
        if isinstance(query_result, pd.DataFrame):
            formatted_result = sql_engine.format_output(query_result)
            if formatted_result['status'] == 'success':
                results.update(formatted_result)
            else:
                results['status'] = 'error'
                results['message'] = formatted_result['message']
        else:
            results['status'] = 'error'
            results['message'] = query_result

    else:
        results['status'] = 'error'
        results['message'] = f"Invalid model_type: {model_type}."
        
    return results