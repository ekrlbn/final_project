import Agent
from google import genai
from google.genai import types

        

agent = Agent.Agent("Trivia Assistant", "You are a helpful assistant that can answer questions about trivia. Only answer in Turkish.")
response = agent.generate_response("what time is it")
print(response)
#print(agent.role)
#print(agent.generate_response("What is the capital of France?.Tell me about the city"))



#chatbot = agent.create_chat()

#print(chatbot.send_message("What is the capital of France?.Tell me about the city"))

#msg = chatbot.send_message("What is the capital of France?.Tell me about the city").text


#print(msg)


class verification(Agent.Agent):

    
    def verify_user_data(self, user_data,prompt):
        

        # If all checks pass, you might want to send this to an LLM for further verification based on the prompt
        # For now, let's assume if all fields are present, it's "verified" for this local check.
        # response = self.create_chat().send_message(prompt) # Example of sending to LLM
        # return response.text
        return self.generate_response(user_data.text + prompt)
        
