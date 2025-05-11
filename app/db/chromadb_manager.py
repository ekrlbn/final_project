# app/db/chromadb_manager.py

import chromadb
from chromadb.config import Settings as ChromaSettings

# from app.core.config import settings # Assuming you have settings in app.core.config

class ChromaDBManager:
    def __init__(self, path="./chroma_db_store", collection_name="retirement_docs"):
        # In a real app, get path and collection_name from config
        # self.client = chromadb.HttpClient(host='localhost', port=8000) # If running ChromaDB as a server
        self.client = chromadb.PersistentClient(path=path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        print(f"ChromaDB client initialized. Collection '{self.collection_name}' loaded/created.")

    def add_documents(self, documents: list, metadatas: list = None, ids: list = None):
        """Adds documents to the ChromaDB collection."""
        if not ids:
            ids = [f"doc_{i}" for i in range(len(documents))]
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(documents)} documents to '{self.collection_name}'.")

    def query_collection(self, query_texts: list, n_results: int = 5):
        """Queries the ChromaDB collection."""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        return results

    def get_collection_count(self):
        """Returns the number of items in the collection."""
        return self.collection.count()

# Example Usage (can be removed or moved to a test/script):
if __name__ == '__main__':
    manager = ChromaDBManager(path="./test_chroma_db", collection_name="test_collection")
    print(f"Initial count: {manager.get_collection_count()}")

    # manager.add_documents(
    #     documents=["This is a document about apples", "This is a document about bananas"],
    #     metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    #     ids=["doc1_id", "doc2_id"]
    # )
    # print(f"Count after adding: {manager.get_collection_count()}")

    # results = manager.query_collection(query_texts=["fruits"], n_results=1)
    # print(f"Query results: {results}") 