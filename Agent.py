from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
llm_model = "gemini-2.0-flash"
class Agent:
    def __init__(self, name, role, tools=None):
        self.name = name
        self.role = role
        self.tools = tools
        #self.model = client.models.generate_content(model="gemini-2.0-flash",config={"system_instruction": role},contents="")

    def generate_response(self, prompt):
        if self.tools:
            response = client.models.generate_content(model=llm_model, config={"system_instruction": self.role}, contents=prompt, tools=self.tools)
        else:
            response = client.models.generate_content(model=llm_model, config={"system_instruction": self.role}, contents=prompt)
        return response.text
    
    def create_chat(self):
        if self.tools:
            chat = client.chats.create(model=llm_model, config={"system_instruction": self.role}, history=None, tools=self.tools)
        else:
            chat = client.chats.create(model=llm_model, config={"system_instruction": self.role}, history=None)
        return chat
    
    def send_message(self, chat_session, message_content):
        """Sends a message using the provided chat session and returns only the LLM text response."""
        response_obj = chat_session.send_message(contents=message_content)
        # Extract text based on the known structure from traceback for chat messages
        return response_obj.text
    

