import gradio as gr
import os
import shutil
import time
from google import genai
from dotenv import load_dotenv

# Import functions from document.py
from document import (
    add_document_to_collection,
    query_collection,
    DOCS_PATH,
    CHROMA_PATH
)

load_dotenv()

# Create docs directory if it doesn't exist
os.makedirs(DOCS_PATH, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# Initialize the language model
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
chat = client.chats.create(model="gemini-2.0-flash")

# Default collection name
DEFAULT_COLLECTION = "pdf_collection"

def process_query_with_rag(query, history):
    """Process query using RAG pipeline and LLM"""
    try:
        # Step 1: Query the vector database to get relevant context
        results = query_collection(
            query=query,
            collection_name=DEFAULT_COLLECTION,
            n_results=3
        )
        
        # Step 2: Extract context from results
        context_parts = []
        if results and "documents" in results and results["documents"] and len(results["documents"][0]) > 0:
            for i, (doc, metadata) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0]
            )):
                source = metadata.get('source', 'unknown')
                context_parts.append(f"Document: {source}\n{doc}")
        
        context = "\n\n".join(context_parts)
        # print(f"Context found: {context}")  # Debugging line
        
        # Step 3: If we have context, use it with the LLM to generate response
        if context:
            full_prompt = f"""Based on the following context, please answer the query.
            
Context:
{context}

Query: {query}

    Answer:"""
            response = chat.send_message(full_prompt)
            return response.text
        else:
            # No context found, just use the LLM directly
            response = chat.send_message(f"Query: {query}\nAnswer:")
            return response.text + "\n\n(Note: No relevant documents were found in the database to answer this query.)"
            
    except Exception as e:
        return f"Error processing query: {str(e)}"

def upload_and_process_file(file):
    """Upload and process a file for the RAG pipeline"""
    if file is None:
        return gr.Warning("No file uploaded")
    
    try:
        # Get the filename from the uploaded file path
        file_name = os.path.basename(file.name)
        # Save the file to the docs directory
        destination_path = os.path.join(DOCS_PATH, file_name)
        shutil.copy(file.name, destination_path)
        
        # Process the file and add to collection
        start_time = time.time()
        add_document_to_collection(
            pdf_name=file_name,
            collection_name=DEFAULT_COLLECTION,
            chunk_size=1000,
            chunk_overlap=100
        )
        processing_time = time.time() - start_time
        
        return gr.Info(f"File '{file_name}' uploaded and processed successfully in {processing_time:.2f} seconds!")
    except Exception as e:
        return gr.Warning(f"Error processing file: {str(e)}")

def list_uploaded_documents():
    """List all documents that have been uploaded"""
    try:
        files = [f for f in os.listdir(DOCS_PATH) if f.lower().endswith('.pdf')]
        if not files:
            return "No documents have been uploaded yet."
        return "Uploaded documents:\n" + "\n".join(files)
    except Exception as e:
        return f"Error listing documents: {str(e)}"

with gr.Blocks(title="Document RAG Assistant") as demo:
    with gr.Sidebar():
        gr.Markdown("## Document Management")
        file_input = gr.File(label="Upload PDF Document", file_types=[".pdf"])
        upload_button = gr.Button("Upload and Process", variant="primary")
        document_status = gr.Textbox(label="Document Status", interactive=False)
        refresh_button = gr.Button("Refresh Document List")
        
        refresh_button.click(
            fn=list_uploaded_documents,
            outputs=[document_status]
        )
        
    with gr.Column():
        gr.Markdown("# Retirement Planning Assistant")
        gr.Markdown("I will help you plan you retirement.")
        
        # Main chat interface
        chatbot = gr.ChatInterface(
            fn=process_query_with_rag,
            chatbot=gr.Chatbot(height=600, type="messages"),
            textbox=gr.Textbox(placeholder="Ask a question about your documents...", container=False),
            title="Retirement Planning Assistant",
            examples=[
                "What are the main topics covered in the uploaded documents?", 
                "Can you summarize the key points from the documents?"
            ],
            type="messages",
        )
    
    # Handle file upload and processing
    upload_button.click(
        fn=upload_and_process_file,
        inputs=[file_input],
        outputs=[document_status]
    )
    
    # Initialize document list
    demo.load(
        fn=list_uploaded_documents,
        outputs=[document_status]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch()