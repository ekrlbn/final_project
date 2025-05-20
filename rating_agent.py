import os
from typing import List, Dict, Any
import time
from google.genai.errors import ClientError
from pydantic import BaseModel
from google import genai

class Rating(BaseModel):
    """Model to hold the rating and explanation."""
    rating: int

MODEL = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def evaluate_chunks(query: str, chunks: List[str]) -> tuple[int, Rating]:
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
        time.sleep(50)
        return evaluate_chunks(query, chunks) 


    print(f"\nTokens used: {response.usage_metadata.candidates_token_count}\n")
    if response.parsed is None or not response.parsed.rating or not response.parsed.rating in range(1, 11):
        print("\nInvalid response from AI model. Please check the model and the prompt.\n")
        return response.usage_metadata.prompt_token_count, Rating(rating=0)

    return response.usage_metadata.prompt_token_count, response.parsed