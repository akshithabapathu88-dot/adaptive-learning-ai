import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
import json
from .embeddings import EmbeddingManager

class VectorStore:
    def __init__(self, collection_name: str = "learning_content", persist_directory: str = "./chroma_db"):
        """
        Initialize the vector store using ChromaDB.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = collection_name
        self.embedding_manager = EmbeddingManager()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with 'content', 'topic', 'difficulty_level', and optional 'metadata'
            
        Returns:
            List of document IDs
        """
        ids = []
        contents = []
        metadatas = []
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            contents.append(doc['content'])
            
            # Create metadata
            metadata = {
                'topic': doc.get('topic', ''),
                'difficulty_level': doc.get('difficulty_level', ''),
                'source': doc.get('source', 'generated')
            }
            
            # Add any additional metadata
            if 'metadata' in doc:
                metadata.update(doc['metadata'])
            
            metadatas.append(metadata)
        
        # Generate embeddings
        embeddings = self.embedding_manager.generate_embeddings(contents)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=contents,
            metadatas=metadatas
        )
        
        return ids
    
    def search(self, query: str, topic: str = None, difficulty_level: str = None, 
               n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            topic: Optional topic filter
            difficulty_level: Optional difficulty level filter
            n_results: Number of results to return
            
        Returns:
            List of similar documents with their metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.generate_embeddings(query)
        
        # Build filter
        where_filter = {}
        if topic:
            where_filter['topic'] = topic
        if difficulty_level:
            where_filter['difficulty_level'] = difficulty_level
        
        # Search
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def get_documents_by_topic(self, topic: str, difficulty_level: str = None) -> List[Dict[str, Any]]:
        """
        Get all documents for a specific topic and optionally difficulty level.
        
        Args:
            topic: Topic to filter by
            difficulty_level: Optional difficulty level filter
            
        Returns:
            List of documents
        """
        where_filter = {'topic': topic}
        if difficulty_level:
            where_filter['difficulty_level'] = difficulty_level
        
        results = self.collection.get(
            where=where_filter,
            include=['documents', 'metadatas']
        )
        
        formatted_results = []
        for i in range(len(results['ids'])):
            formatted_results.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return formatted_results
    
    def delete_documents(self, document_ids: List[str]):
        """Delete documents by their IDs."""
        self.collection.delete(ids=document_ids)
    
    def update_document(self, document_id: str, content: str, metadata: Dict[str, Any]):
        """Update a document's content and metadata."""
        # Generate new embedding
        embedding = self.embedding_manager.generate_embeddings(content)
        
        # Update the document
        self.collection.update(
            ids=[document_id],
            embeddings=[embedding.tolist()],
            documents=[content],
            metadatas=[metadata]
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection_name,
            'embedding_dimension': self.embedding_manager.get_embedding_dimension()
        }
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        # Delete and recreate the collection
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
