from flask import Flask, request, jsonify
import sys
from typing import Dict, Any

# Import configurations and the service orchestrator
from config import Config
from bio_query_service import initialize_bio_service, shutdown_bio_service, process_hybrid_query

# --- Flask Application Setup ---
app = Flask(__name__)

# --- API Routes and Hooks ---

@app.before_first_request
def setup_service():
    """Initializes the BioGPT service before the first request is served."""
    if not initialize_bio_service():
        print("Application failed to initialize BioGPT service. Shutting down.")
        sys.exit(1)

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Cleans up database resources upon application context teardown."""
    shutdown_bio_service()

@app.route('/api/biogpt', methods=['POST'])
def biogpt_endpoint() -> tuple[Dict[str, Any], int]:
    """
    Hybrid API endpoint for the BioGPT framework. Allows the user to select the
    underlying AI model (RAG or SQL).
    """
    
    # 1. Input Validation
    if not request.json:
        return jsonify({"status": "error", "message": "Request must be JSON."}), 400

    user_query = request.json.get('query')
    model_type = request.json.get('model_type', 'rag').lower() # Default to RAG
    
    if not user_query or model_type not in ['rag', 'sql']:
        return jsonify({"status": "error", "message": "Invalid 'query' or 'model_type'. Use 'rag' or 'sql'."}), 400

    # 2. Call the Hybrid Service Logic
    results = process_hybrid_query(user_query, model_type)

    # 3. Handle Status and Return Response
    if results['status'] == 'success':
        return jsonify(results), 200
    else:
        # Errors return the error message from the service
        return jsonify(results), 500


@app.route('/')
def health_check():
    """Simple endpoint to confirm the API service is running."""
    return "BioGPT Query Service is operational. Use POST /api/biogpt."


if __name__ == '__main__':
    # Standard Flask execution block
    print("Starting BioGPT Flask API...")
    app.run(host='0.0.0.0', port=5000, debug=True)