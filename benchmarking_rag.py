import os
import time

from chromadb import EmbeddingFunction
from chromadb.utils import embedding_functions
from pydantic import BaseModel
from document import query_collection, add_document_to_collection
from dotenv import load_dotenv
from typing import List, Dict, Any
from tqdm import tqdm
from google import genai
from google.genai.errors import ClientError
import pandas as pd

load_dotenv()

EMBEDDING_FUNC: EmbeddingFunction = embedding_functions.SentenceTransformerEmbeddingFunction()

MODEL = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

class Rating(BaseModel):
    """Model to hold the rating and explanation."""
    rating: int

class QueryResult(BaseModel):
    """Model to hold the query result."""
    query: int
    chunk_size: int
    chunk_overlap: int
    embedding_function: str
    chunk_count: int
    distance_max: float
    distance_avr: float
    rating: int

# Define embedding function to use (matches the one in document.py)

# Test queries to benchmark
test_queries = []
with open("test_queries.txt", "r") as f:
    test_queries = f.readlines()

print(test_queries)

def evaluate_chunks(query: str, chunks: List[str]) -> Rating:
    """Uses an AI model to evaluate the relevance of chunks to the query."""
    
    # Prepare the evaluation prompt
    main_prompt = f"""
    Query: {query}
    
    Retrieved chunks:
    {chunks}
    
    On a scale from 1-10, rate how relevant these chunks are to the query.
    Provide your rating and a brief explanation in this format:
    
    Rating: [1-10]
    Explanation: [Your explanation]
    """
    
    try: 
        response = MODEL.models.generate_content(
            model="gemini-2.0-flash",
            contents=main_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": Rating
            }
        )
    except ClientError as e:
        time.sleep(60)
        return evaluate_chunks(query, chunks) 


    print(f"\nTokens used: {response.usage_metadata.candidates_token_count}\n")
    if response.parsed is None or not response.parsed.rating or not response.parsed.rating in range(1, 11):
        print("\nInvalid response from AI model. Please check the model and the prompt.\n")
        return Rating(rating=0)

    return response.parsed

def run_benchmark(
        embedding_func: EmbeddingFunction = EMBEDDING_FUNC,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        n_results_arr: list[int] = [5],
        
) -> pd.DataFrame:
    """Runs benchmark on the RAG pipeline than saves results to a CSV file."""
    add_document_to_collection(
        pdf_name="sample.pdf",
        collection_name="test_collection",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        test=True,
        embedding_func=embedding_func
    )
    model_name = embedding_func.get_config().get("model_name")

    # Initialize results list
    benchmark_results: List[QueryResult] = []

    for n_result in n_results_arr:
        for idx in tqdm(range(len(test_queries)), desc="Processing queries", colour="green"):
            # Query the collection
            results = query_collection(
                query=test_queries[idx],
                collection_name="test_collection",
                n_results=n_result,
                embedding_func=embedding_func
            )

            # Extract relevant data from results
            if results and "documents" in results and results["documents"]:
                chunks = results["documents"][0]
                chunk_count = len(chunks)
                distances = results["distances"][0]
                distance_max = max(distances) if distances else 0
                distance_avr = sum(distances) / len(distances) if distances else 0
                # Evaluate the chunks using the AI model
                rating = evaluate_chunks(test_queries[idx], chunks)
                # Create a QueryResult object
                query_result = QueryResult(
                    query=idx,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunk_count=chunk_count,
                    distance_max=distance_max,
                    distance_avr=distance_avr,
                    rating=rating.rating,
                    embedding_function=model_name
                )
                benchmark_results.append(query_result)
            else:
                benchmark_results.append(QueryResult(
                    query=-1,
                    chunk_size=0,
                    chunk_overlap=0,
                    chunk_count=0,
                    distance_max=0,
                    distance_avr=0,
                    rating=0,
                    embedding_function=model_name
                ))

    # Save results to CSV
    results_df = pd.DataFrame([result.model_dump() for result in benchmark_results])
    results_df.to_csv("benchmark_results.csv", index=False, mode="a", header=not os.path.exists("benchmark_results.csv"))

    print("Benchmark results saved to benchmark_results.csv")

    return results_df

if __name__ == "__main__":
    # Run the benchmark
    
    models = [
        embedding_functions.SentenceTransformerEmbeddingFunction("all-mpnet-base-v2"),
        embedding_functions.SentenceTransformerEmbeddingFunction("multi-qa-mpnet-base-dot-v1"),
        embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            model_name="models/text-embedding-004"),
        embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2"),
    ]

    chunk_sizes = [1000]
    chunk_overlaps = [200]

    for model in models:
        for chunk_size in chunk_sizes:
            for chunk_overlap in chunk_overlaps:
                print(f"\nRunning benchmark with {model.get_config().get('model_name')}, "
                        f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n")
                run_benchmark(
                    embedding_func=model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    n_results_arr=[3, 5, 10]
                )