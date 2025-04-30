# This is a simple general-purpose chatbot built on top of LangChain and Gradio.
# Before running this, make sure you have exported your Google API key as an environment variable:
# export GOOGLE_API_KEY="your-google-api-key"

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import AIMessage, HumanMessage
import gradio as gr

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def predict(message, history):
    history_langchain_format = []
    for msg in history:
        if msg['role'] == "user":
            history_langchain_format.append(HumanMessage(content=msg['content']))
        elif msg['role'] == "assistant":
            history_langchain_format.append(AIMessage(content=msg['content']))
    history_langchain_format.append(HumanMessage(content=message))
    gemini_response = model.invoke(history_langchain_format)
    return gemini_response.content

demo = gr.ChatInterface(
    predict,
    type="messages"
)

demo.launch()
