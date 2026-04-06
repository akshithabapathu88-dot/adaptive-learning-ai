from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import torch

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding manager with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def generate_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the given text(s).
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32
        )
        
        return embeddings
    
    def compute_similarity(self, query_embedding: np.ndarray, 
                          document_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and document embeddings.
        
        Args:
            query_embedding: Embedding of the query
            document_embeddings: Embeddings of documents
            
        Returns:
            numpy array of similarity scores
        """
        # Normalize embeddings for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding, axis=-1, keepdims=True)
        doc_norm = document_embeddings / np.linalg.norm(document_embeddings, axis=-1, keepdims=True)
        
        # Compute cosine similarity
        similarities = np.dot(doc_norm, query_norm.T).flatten()
        
        return similarities
    
    def get_embedding_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        return self.embedding_dim
