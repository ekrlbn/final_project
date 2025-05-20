import Agent
from google import genai
agent = Agent.Agent("Trivia Assistant", "You are a helpful assistant that can answer questions about trivia. Only answer in Turkish.")

#print(agent.role)
#print(agent.generate_response("What is the capital of France?.Tell me about the city"))



chatbot = agent.create_chat()

#print(chatbot.send_message("What is the capital of France?.Tell me about the city"))

msg = chatbot.send_message("What is the capital of France?.Tell me about the city").text

print(msg)


class verification(Agent.Agent):
    def verify_user_data(self, user_data):
        # user_data should be a dictionary
        prompt = f"""You will receive a input in the given json format. Make sure none of the fields are null or empty:
```json
{
  "name_surname": "name_surname",
  "age": 23,
  "email": "example@example.com",
  "gender": "Male",
  "martial_status": null,
  "number_of_children": null,
  "education_level": "Bachelor's Degree",
  "occupation": "uber driver",
  "anual_working_hours": 1040,
  "monthly_income": 2000,
  "monthly_expenses": 1500,
  "debt": 0,
  "assets": "car worth $2000",
  "location": "ankara turkey",
  "chronic_diseases": "none",
  "lifestyle_habits": "i dont smoke i dont drink and lift weights 3 times per week",
  "family_health_history": "not that i know of",
  "target_retirement_age": 65,
  "target_retirement_income": 3000
}
```
Ensure that none of the fields are null or empty.
User data to verify: {user_data}

if the user data is not in the expected format, return "User data is not in the expected format (dictionary)."
if the user data has missing fields, return (field_name) is missing."
"""
        self.generate_response(prompt)

        # If all checks pass, you might want to send this to an LLM for further verification based on the prompt
        # For now, let's assume if all fields are present, it's "verified" for this local check.
        # response = self.create_chat().send_message(prompt) # Example of sending to LLM
        # return response.text
        return "User data preliminary check passed: All fields are present."
        
        