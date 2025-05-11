# ui/app.py

import gradio as gr
import requests # To interact with the backend FastAPI app

BACKEND_URL = "http://localhost:8000" # Assuming backend runs on port 8000

def greet(name):
    return "Hello " + name + "!"

def chat_interface(message, history):
    # This is where the Gradio UI will send messages to the backend
    # and get responses to display.
    # For now, it just echoes the message.
    
    # Example: Send message to backend (you'll need an endpoint in your FastAPI app)
    # try:
    #     response = requests.post(f"{BACKEND_URL}/chat", json={"user_id": "test_user", "message": message})
    #     response.raise_for_status()
    #     backend_reply = response.json().get("reply", "Error getting reply from backend.")
    # except requests.RequestException as e:
    #     backend_reply = f"Error connecting to backend: {e}"
    #     print(backend_reply)
    # return backend_reply
    
    return message # Simple echo for now

# Define the Gradio interface
demo = gr.ChatInterface(fn=chat_interface, title="Retirement Planning Advisor")

# For more complex UIs, you can use gr.Blocks()
# with gr.Blocks() as demo:
#     gr.Markdown("## Retirement Planning Tool")
#     with gr.Row():
#         name_input = gr.Textbox(label="Enter your name")
#         greet_output = gr.Textbox(label="Greeting")
#     greet_button = gr.Button("Greet")
#     greet_button.click(greet, inputs=name_input, outputs=greet_output)

#     gr.Markdown("### Chat with the Advisor")
#     chatbot = gr.Chatbot()
#     msg_input = gr.Textbox(label="Your message")
#     clear_button = gr.Button("Clear Chat")

#     def user_chat(user_message, chat_history):
#         # Send to backend, get response
#         # For now, just echoing
#         bot_message = chat_interface(user_message, chat_history)
#         chat_history.append((user_message, bot_message))
#         return "", chat_history

#     msg_input.submit(user_chat, [msg_input, chatbot], [msg_input, chatbot])
#     clear_button.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    print("Launching Gradio Interface...")
    # To make it accessible on the network, use share=True (be careful with security)
    demo.launch() 