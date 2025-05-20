import os

from chromadb import EmbeddingFunction
from chromadb.utils import embedding_functions
from pydantic import BaseModel
from document import query_collection, add_document_to_collection
from dotenv import load_dotenv
from typing import List, Dict, Any
from tqdm import tqdm
import pandas as pd
from rating_agent import evaluate_chunks

load_dotenv()

EMBEDDING_FUNC: EmbeddingFunction = embedding_functions.SentenceTransformerEmbeddingFunction()

class QueryResult(BaseModel):
    """Model to hold the query result."""
    query: int
    chunk_size: int
    chunk_overlap: int
    embedding_function: str
    chunk_count: int
    distance_max: float
    distance_avr: float
    input_tokens: int
    rating: int


# Test queries to benchmark
test_queries = []
with open("test_queries.txt", "r") as f:
    test_queries = f.readlines()

print(test_queries)


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
                input_tokens, rating = evaluate_chunks(test_queries[idx], chunks)
                # Create a QueryResult object
                query_result = QueryResult(
                    query=idx,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunk_count=chunk_count,
                    distance_max=distance_max,
                    distance_avr=distance_avr,
                    rating=rating.rating,
                    embedding_function=model_name,
                    input_tokens=input_tokens
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
                    embedding_function=model_name,
                    input_tokens=input_tokens
                ))

    # Save results to CSV
    results_df = pd.DataFrame([result.model_dump() for result in benchmark_results])
    results_df.to_csv("benchmark_results.csv", index=False, mode="a", header=not os.path.exists("benchmark_results.csv"))

    print("Benchmark results saved to benchmark_results.csv")

    return results_df

if __name__ == "__main__":
    # Run the benchmark
    
    models = [
        embedding_functions.SentenceTransformerEmbeddingFunction("multi-qa-MiniLM-L6-cos-v1"),
        embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            model_name="models/text-embedding-004"),
        embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2"),
    ]

    chunk_sizes = [500, 1000, 1500]
    chunk_overlaps = [0, 100, 200]

    for model in models:
        for chunk_size in chunk_sizes:
            for chunk_overlap in chunk_overlaps:
                print(f"\nRunning benchmark with {model.get_config().get('model_name')}, "
                        f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n")
                run_benchmark(
                    embedding_func=model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    n_results_arr=[3, 5]
                )