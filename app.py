import gradio as gr
import os
import shutil
import time
from google import genai
from dotenv import load_dotenv
from conversation_agent import message_chat
from typing import Optional
from user_info import create_profile_interface
from authentication import signup, login

# Import functions from document.py
from document import (
    add_document_to_collection,
    query_collection,
    DOCS_PATH,
    CHROMA_PATH
)

from rating_agent import evaluate_chunks

load_dotenv()

# Create docs directory if it doesn't exist
os.makedirs(DOCS_PATH, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)


# Default collection name
DEFAULT_COLLECTION = "pdf_collection"

def get_chunks(query:str) -> Optional[str]:
    """Get relevant chunks from the vector database using the query
    Parameters:
        query (str): The query to search for in the vector database
    Returns:
        str: The relevant chunks of text from the vector database 
        if the rating from the agent is high enough, otherwise None
    """

    try:
        # Step 1: Query the vector database to get relevant context
        results = query_collection(
            query=query,
            collection_name=DEFAULT_COLLECTION,
            n_results=3
        )

        # Step 2: Check if the distances are good enough
        # to pass the results to the rating agent
        is_valid = False
        for distance in results["distances"][0]:
            if distance < 1:
                is_valid = True
                break
        if not is_valid:
            print("No valid results found from the vector database.")
            return None

        print(f"\n\nNumber of chunks{len(results["documents"][0])}\n\n")  # Debugging line
        
        # Step 3: Extract context from results
        context_parts = []
        if results and "documents" in results and results["documents"] and len(results["documents"][0]) > 0:
            for i, (doc, metadata) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0]
            )):
                source = metadata.get('source', 'unknown')
                context_parts.append(f"Document: {source}\n{doc}")

        # Step 4: Evaluate the context using the rating agent
        input_tokens, rating = evaluate_chunks(query, context_parts)
        if rating.rating < 5:
            print(f"Rating is too low: {rating.rating}. No context will be used.")
            return None
        
        return "\n\n".join(context_parts)
        # print(f"Context found: {context}")  # Debugging line
    except Exception as e:
        return None

def process_query(query, history):
    """Process query using RAG pipeline and LLM"""
    context = get_chunks(query)
        # Step 3: If we have context, use it with the LLM to generate response
    if context:
        full_prompt = f"""Based on the following context, please answer the query.
Also, provide the sources of the information you used to answer the query at the end of your answer. 
        
Context:
{context}

Query: {query}

Answer:"""
        return message_chat(full_prompt)
    else:
        # No context found, just use the LLM directly
        return message_chat(query)
            

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
            chunk_overlap=0
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

with gr.Blocks(title="Retirement Planning Assistant") as demo:
    # Create state to track authentication
    auth_state = gr.State(False)
    user_info = gr.State({})
    
    # Create container components that can be shown/hidden
    with gr.Column(visible=False) as main_interface:
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
            gr.Markdown("I will help you plan your retirement.")
            
            # Main chat interface
            chatbot = gr.ChatInterface(
                fn=process_query,
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
    
    # Auth interface
    with gr.Column(visible=True) as auth_interface:
        gr.Markdown("# User Authentication System")
        with gr.Tabs() as tabs:
            with gr.Tab("Signup"):
                with gr.Column():
                    signup_name_surname = gr.Textbox(label="Name Surname")
                    signup_email = gr.Textbox(label="Email")
                    signup_password = gr.Textbox(label="Password", type="password")
                    signup_button = gr.Button("Sign Up")
                    signup_output = gr.Textbox(label="Result")

                    signup_button.click(
                        fn=signup,
                        inputs=[signup_name_surname, signup_email, signup_password],
                        outputs=signup_output,
                    )

            with gr.Tab("Login"):
                with gr.Column():
                    login_email = gr.Textbox(label="Email")
                    login_password = gr.Textbox(label="Password", type="password")
                    login_button = gr.Button("Login")
                    login_output = gr.Textbox(label="Result")

            with gr.Tab("Profile"):
                profile_components = create_profile_interface()

    # Update the login function to handle authentication state
    def handle_login(email, password):
        try:
            # Call the login function, but only extract the result message
            login_result = login(email, password)
            
            # Check if the result is a tuple or contains unexpected components
            if not isinstance(login_result, str):
                # If login is returning complex objects, extract just the message
                # This is a fallback in case your login function returns UI components
                login_result = "Login successful!" if any("success" in str(x).lower() 
                                                         for x in login_result if hasattr(x, "__str__")) else "Login failed"
            
            # Determine success based on the message
            success = "success" in login_result.lower()
            
            # Create user data (you might want to modify this)
            user_data = {"email": email} if success else {}
            
            return login_result, success, user_data
        except Exception as e:
            print(f"Login error: {str(e)}")
            return f"Login error: {str(e)}", False, {}

    # Toggle visibility based on auth state
    def update_ui(auth_successful, user_data):
        if auth_successful:
            return gr.update(visible=False), gr.update(visible=True)
        return gr.update(visible=True), gr.update(visible=False)

    # Wire up the login button
    login_button.click(
        fn=handle_login,
        inputs=[login_email, login_password],
        outputs=[login_output, auth_state, user_info]
    ).then(
        fn=update_ui,
        inputs=[auth_state, user_info],
        outputs=[auth_interface, main_interface]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch()