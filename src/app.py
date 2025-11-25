from flask import Flask, request, jsonify
import sys
from typing import Dict, Any

# Import configurations and the service orchestrator
try:
    from .config import Config 
    from .bio_query_service import initialize_bio_service, shutdown_bio_service, process_hybrid_query
except ImportError:
    print("FATAL: Failed to import internal modules. Check package structure and __init__.py files.")
    sys.exit(1)

# --- Flask Application Setup ---
app = Flask(__name__)
app.config['SERVICE_INITIALIZED'] = False 

# --- API Routes and Hooks ---

@app.before_request
def setup_service():
    """Initializes the BioGPT service once per application lifecycle."""
    if not app.config.get('SERVICE_INITIALIZED'):
        if not initialize_bio_service():
            print("Application failed to initialize BioGPT service. Shutting down.")
            sys.exit(1)
        app.config['SERVICE_INITIALIZED'] = True

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Shutdown hook."""
    # Note: We avoid aggressive cleanup here to keep the DB file alive during the process life.
    pass

@app.route('/api/biogpt', methods=['POST'])
def biogpt_endpoint() -> tuple[Dict[str, Any], int]:
    """Hybrid API endpoint."""
    if not request.json:
        return jsonify({"status": "error", "message": "Request must be JSON."}), 400

    user_query = request.json.get('query')
    model_type = request.json.get('model_type', 'rag').lower()
    
    if not user_query or model_type not in ['rag', 'sql']:
        return jsonify({"status": "error", "message": "Invalid 'query' or 'model_type'."}), 400

    results = process_hybrid_query(user_query, model_type)

    if results['status'] == 'success':
        return jsonify(results), 200
    else:
        return jsonify(results), 500

@app.route('/')
def health_check():
    return "BioGPT Query Service is operational. Use POST /api/biogpt."

if __name__ == '__main__':
    # FORCE single-threaded mode to avoid SQLite concurrency issues during dev
    print("Starting BioGPT Flask API (Single-Threaded)...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)