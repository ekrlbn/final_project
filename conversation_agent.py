from google import genai
#from portfolio_assistant import PortfolioAssistant
#from RetirementAgent import RetirementAgent
import Agent



system_prompt1 = """
{
  "name_surname": {
    "type": "string",
    "description": "The full name of the user.",
    "required": true
  },
  "age": {
    "type": "integer",
    "description": "The age of the user.",
    "required": true
  },
  "email": {
    "type": "string",
    "description": "The email address of the user.",
    "required": true
  },
  "gender": {
    "type": "string",
    "description": "The gender of the user.",
    "options": ["Male", "Female", "Other"],
    "required": true
  },
  "martial_status": {
    "type": "string",
    "description": "The marital status of the user.",
    "options": ["Single", "Married", "Divorced", "Widowed"],
    "required" : true
  },
  "number_of_children": {
    "type": "integer",
    "description": "The number of children the user has.",
    "required" : true
  },
  "education_level": {
    "type": "string",
    "description": "The highest level of education the user has completed.",
    "options": [
      "High School",
      "Associate's Degree",
      "Bachelor's Degree",
      "Master's Degree",
      "Doctorate",
      "Other"
    ]
    "required" : true
  },
  "occupation": {
    "type": "string",
    "description": "The occupation of the user.",
    "required": true
  },
  "anual_working_hours": {
    "type": "integer",
    "description": "The number of hours the user works in a week.",
    "required": true
  },
  "monthly_income": {
    "type": "integer",
    "description": "The monthly income of the user.",
    "required": true
  },
  "monthly_expenses": {
    "type": "integer",
    "description": "The monthly expenses of the user.",
    "required": true
  },
  "debt": {
    "type": "integer",
    "description": "The amount of debt the user has.",
    "required": true
  },
  "assets": {
    "type": "string",
    "description": "All kind of assets the user has.",
    "required": true,
    "example": "House worth $300,000, car worth $20,000, savings of $50,000, $10,000 in stocks."
  },
  "location": {
    "type": "string",
    "description": "The location of the user.",
    "required" : true
  },
  "chronic_diseases": {
    "type": "string",
    "description": "List of chronic diseases the user has.",
    "example": "Diabetes, hypertension, asthma.",
    "required": true
  },
  "lifestyle_habits": {
    "type": "string",
    "description": "List of lifestyle habits of the user.",
    "example": "Non-smoker, moderate alcohol consumption, regular exercise."
    "required" : true
  },
  "family_health_history": {
    "type": "string",
    "description": "Family health history of the user.",
    "example": "Father had heart disease, mother had breast cancer.",
    "required": true
  },
  "target_retirement_age": {
    "type": "integer",
    "description": "The age at which the user plans to retire.",
    "required": true
  },
  "target_retirement_income": {
    "type": "integer",
    "description": "The income the user wants to have at retirement.",
    "required": true
  }
}
Ask in this order
what is your full name 
what is 

this is structure of a user. Start as null for all of them. 
You are responsible for asking relative questions and getting answers about user's fields. 
Ask them in a conversational way. Ask and fill required: true fields certainly. 
Fill them in order and ask follow up questions dont move to the next question until the answers is satisfactory expect clarity in the answers from the user
You may ask and fill required:false fields if it is appropriate in conversation or already given by user.

Do NOT ask anything other than these fields.
Do NOT add any fields other than given ones.
Do NOT miss any attributes make sure you ask all of them and ask them in order.
Do NOT change name of fields. Do NOT modify the structure.
Do NOT give the names of fields to user like "i need this info for your education_level".



ONLY WHEN user says "Export profile as JSON", return ONLY the filled json structure.
After that do not ask further questions 
"""
system_prompt2="""
once you recive this prompt ignore all previous instructions and start a new conversation 
after this you will recive a json structure of the user
general assigner 
be very brief and concise in your answers
dont talk with your full capacity
You are strictly a agnet caller assistant and you are not allowed to give any other information . 
which report would you like to see?
- retirement plan
- portfolio report
- longevity report
- health report

"""
system_prompt3 = """json
{
  name_surname Onat Keser,
  age 28,
  email il@wewe.com,
  gender Male,
  martial_status Single,
  number_of_children 0,
  education_level High School,
  occupation plumber,
  anual_working_hours 40,
  monthly_income 2000,
  monthly_expenses 1000,
  debt 10000,
  assets 20 shares of Apple stock and $5000 in savings,
  location Utah,
  chronic_diseases null,
  lifestyle_habits Non-smoker, no alcohol, weekly basketball,
  family_health_history Grandfather has Alzheimer's, mother has bone cancer,
  target_retirement_age 60,
  target_retirement_income 2000
}
this is a json structure of the user.
when you are told print
you only print the above json structure and nothing else
 """

user_json=""




#gemini_key = "AIzaSyCSJPXO1B9g0Ex_bOKE8D0jLiJyFB5C75w"
#client = genai.Client(api_key=gemini_key)
gemini_config_structured = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 40,
    "response_mime_type": "application/json",
    "system_instruction": system_prompt1,
    
}
gemini_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 40,
    "system_instruction": system_prompt1,
    
}
agent = Agent.Agent("Retirement Planing Assistant",system_prompt1)
chat_session = agent.create_chat()

#chat = client.chats.create(model="gemini-2.0-flash",config=gemini_config)

user_json=""

print("hello welcome to the retirement planing")
exported = False
while exported==False:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    #chat.send_message(system_prompt1)
    response = chat_session.send_message(user_input)
    #response = chat.send_message(user_input)
    bot_reply = response.text
    
    if "```json" in bot_reply:
        user_json = bot_reply
        print("Bot: Your profile has been saved. You can now ask for a report.")  
        exported = True
        break
    if exported:
        print("Bot: Thank you, your profile has been saved. Have a great day!")
        break
    print("Bot:", bot_reply)
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    #chat.send_message(system_prompt2)
    response = agent.send_message(agent.chat,user_input)
    #response = chat.send_message(user_input)
