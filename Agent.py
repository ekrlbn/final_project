from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
llm_model = "gemini-2.0-flash"
class Agent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        #self.model = client.models.generate_content(model="gemini-2.0-flash",config={"system_instruction": role},contents="")

    def generate_response(self, prompt):
        response = client.models.generate_content(model=llm_model,config={"system_instruction": self.role},contents=prompt)
        return response.text
    
    def create_chat(self,prompt):
        chat = client.chats.create(model=llm_model,config={"system_instruction": self.role},contents=prompt)
        return chat
    
    def send_message(self,chat,message):
        response = chat.send_message(message)
        return response.text
    

