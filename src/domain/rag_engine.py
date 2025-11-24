from typing import Dict, Any, List
from numpy import ndarray
from pandas import DataFrame
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import Config
from .context import ServiceContext


class RAGEngine:
    """
    Implements the RAG (Retrieval-Augmented Generation) logic, using semantic 
    search for retrieval and a generative model for synthesis.
    """

    def __init__(self, context: ServiceContext):
        # Dependencies injected from the context
        self.nlp_model = context.nlp_model
        self.embeddings = context.embeddings
        self.generator = context.generator
        self.df_data = context.df_data

    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Performs semantic search using embeddings."""
        if self.nlp_model is None or self.embeddings is None or self.df_data is None:
            return []

        query_embedding = self.nlp_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'Entry_Name': self.df_data.iloc[idx]['Entry_Name'],
                'Similarity_Score': f"{similarities[idx]:.4f}",
                'Context_Bio': self.df_data.iloc[idx]['Context_NLP'] 
            })
        return results

    def generate_response(self, query: str) -> str:
        """Retrieves context and generates a natural language response."""
        if self.generator is None:
            return "Error: Generative Model not initialized."
            
        top_contexts = self.semantic_search(query, top_k=3)
        if not top_contexts:
            return "Sorry, I couldn't find relevant biological context for that query."

        # 1. Context Augmentation
        aggregated_context = " ".join([f"|Protein: {c['Entry_Name']}, Context: {c['Context_Bio']}" for c in top_contexts])
        
        # 2. Instruction for Generative Model
        instruction_prompt = (
            f"Based ONLY on this context: '{aggregated_context}'. "
            f"Answer the user's question clearly, listing the relevant proteins: {query}"
        )

        try:
            generated_text = self.generator(instruction_prompt, num_return_sequences=1, do_sample=False)[0]['generated_text']
            # Clean the repeated prompt
            final_response = generated_text.replace(instruction_prompt, "").strip()
            return final_response if final_response else "No specific answer generated from the provided context."
        except Exception as e:
            return f"Error during text generation: {e}"