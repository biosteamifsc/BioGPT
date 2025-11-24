import os
from typing import Dict, Any, Optional

# Import Infrastructure components
from .config import Config
from .infrastructure.infra_manager import InfraManager

# Import Domain components
from .domain.context import ServiceContext
from .domain.text_to_sql_engine import TextToSqlEngine
from .domain.rag_engine import RAGEngine

# --- PUBLIC API STATE AND FUNCTIONS ---

# Global variables to manage state and cleanup
global_service_context: Optional[ServiceContext] = None
global_infra_manager: Optional[InfraManager] = None 

def initialize_bio_service() -> bool:
    """
    Initializes the entire BioGPT service infrastructure and domain context.
    Must be called before the API starts accepting queries.
    """
    global global_service_context, global_infra_manager
    
    if not os.path.exists(Config.TSV_FILE):
        print(f"FATAL: {Config.TSV_FILE} not found. Cannot start service.")
        return False

    # 1. Initialize Infrastructure (Data Loading, DB Setup, Model Loading)
    global_infra_manager = InfraManager()
    if not global_infra_manager.initialize_infrastructure():
        return False
        
    # 2. Create the global context object (DI Container)
    global_service_context = ServiceContext(global_infra_manager)
    
    print("BioGPT Service initialization successful.")
    return True

def shutdown_bio_service():
    """Cleans up infrastructure resources (temporary DB files) upon application shutdown."""
    if global_infra_manager:
        global_infra_manager.cleanup()

def process_hybrid_query(user_query: str, model_type: str = 'rag') -> Dict[str, Any]:
    """
    Main entry point for the hybrid query engine.
    Orchestrates the chosen engine and formats the output.
    """
    if global_service_context is None:
        return {"status": "error", "message": "Service not initialized. Check server logs."}

    results: Dict[str, Any] = {
        "status": "success", "model_type": model_type.upper(), "user_query": user_query
    }
    
    context = global_service_context

    # --- RAG Model Execution ---
    if model_type.lower() == 'rag':
        rag_engine = RAGEngine(context) # Dependency injection
        
        results['response'] = rag_engine.generate_response(user_query)
        # Populate context list for API output clarity
        results['retrieved_contexts'] = rag_engine.semantic_search(user_query)
        
    # --- SQL Model Execution ---
    elif model_type.lower() == 'sql':
        sql_engine = TextToSqlEngine(context) # Dependency injection
        
        sql_query = sql_engine.translate_query(user_query)
        results['sql_query'] = sql_query
        
        formatted_result = sql_engine.execute_and_format(sql_query)
        
        if formatted_result['status'] == 'success':
            results.update(formatted_result)
        else:
            results['status'] = 'error'
            results['message'] = formatted_result['message']

    else:
        results['status'] = 'error'
        results['message'] = f"Invalid model_type specified: {model_type}. Use 'rag' or 'sql'."
        
    return results