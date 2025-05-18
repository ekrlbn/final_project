import os
import time
from typing import List, Optional

from pypdf import PdfReader

from langchain_text_splitters import RecursiveCharacterTextSplitter

import chromadb
from chromadb import EmbeddingFunction
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
load_dotenv()

# Define path variable at the beginning
DOCS_PATH = os.path.join(os.getcwd(), "docs")
CHROMA_PATH = os.path.join("chroma_db")
EMBEDDING_FUNC: EmbeddingFunction = embedding_functions.SentenceTransformerEmbeddingFunction()
# embedding_functions.GoogleGenerativeAiEmbeddingFunction(
#     api_key=os.environ.get("GOOGLE_API_KEY"),
#     model_name="models/embedding-001"
# )

# Create directories if they don't exist
os.makedirs(DOCS_PATH, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text

def split_text_into_chunks(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = ["\n\n" ".", ". "]
) -> List[str]:
    """
    Split text into smaller chunks with specified size and overlap.
    
    Args:
        text: The text to split
        chunk_size: The size of each chunk
        chunk_overlap: The overlap between chunks
        separators: List of separators to use for splitting
        
    Returns:
        List of text chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


def add_document_to_collection(
    pdf_name: str,
    collection_name: str = "pdf_collection", 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200,
    embedding_func: embedding_functions.EmbeddingFunction = None
):
    """
    Process a PDF file and add its chunks to a ChromaDB collection.
    
    Args:
        pdf_path: Path to the PDF file
        collection_name: Name of the collection to add documents to
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
    """
    # Check if the PDF file exists
    pdf_path = os.path.join(DOCS_PATH, pdf_name)
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        print("Please place a PDF file at this location or update the path.")
        return

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Split text into chunks
    chunks = split_text_into_chunks(text, chunk_size, chunk_overlap)
    
    # Initialize Google embedding function directly here
    if embedding_func is None:
        embedding_func = EMBEDDING_FUNC
    
    # Initialize client
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Create new collection with the embedding function
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func,
    )
    
    collection.delete(where={"source": os.path.basename(pdf_name)})
    
    # Add chunks to collection
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas={
                "source": os.path.basename(pdf_name),
                "chunk": i,
                "last_modified": os.path.getmtime(pdf_path),
                "added": time.time(),
            },
            ids=[f"doc_{os.path.basename(pdf_name)}_{i}"]
        )
    
    print(f"Added {len(chunks)} chunks from {pdf_name} to collection {collection_name}")
    return collection

def query_collection(
    query: str,
    collection_name: str = "pdf_collection",
    n_results: int = 5,
    embedding_func: embedding_functions.EmbeddingFunction = None
):
    """
    Query the collection and return relevant chunks.
    
    Args:
        query: The query text
        collection_name: Name of the collection to query
        n_results: Number of results to return
    
    Returns:
        List of relevant document chunks with their metadatas
    """
    # Initialize Google embedding function
    if embedding_func is None:
        embedding_func = EMBEDDING_FUNC
    
    # Initialize client and get collection
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=collection_name, embedding_function=embedding_func)
    
    # Query collection
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    
    return results

def print_results(results):
    # Print the number of relevant chunks found
    print(f"Found {len(results['documents'][0])} relevant chunks:")

    for i, (doc, metadata, distance) in enumerate(zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
    )):
        print(f"\nResult {i+1} (distance: {distance:.4f}):")
        print(f"Source: {metadata['source']}, Chunk: {metadata['chunk']}")
        print(f"Text snippet: {doc[:150]}..." if len(doc) > 150 else doc)