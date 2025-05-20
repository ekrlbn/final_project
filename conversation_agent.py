import os
import google.generativeai as genai
import global_session
from portfolio_assistant import PortfolioAssistant # Import PortfolioAssistant

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")
# Consider managing chat history more carefully, perhaps re-initializing for new sessions or users.
# For now, using a single global chat object.
chat = model.start_chat(history=[])

def message_chat(message):
    if not global_session.current_user:
        return "Please log in to use the assistant."

    # --- Portfolio Assistant Integration ---
    # Simple intent detection for portfolio-related queries
    # You might want to make this more sophisticated, e.g., using another LLM call or NLP library.
    portfolio_keywords = [
        "stock", "portfolio", "shares", "price of", "value of my", "ticker",
        "investments", "asset", "holding"
    ]
    is_portfolio_query = any(keyword in message.lower() for keyword in portfolio_keywords)

    if is_portfolio_query:
        # Retrieve portfolio data from the current user.
        # Assumes global_session.current_user has a 'portfolio' attribute that is a dict.
        # e.g., user_object.portfolio = {"AAPL": 10, "MSFT": 5}
        user_portfolio_data = getattr(global_session.current_user, 'portfolio', {})

        if not isinstance(user_portfolio_data, dict):
            # Fallback or error if portfolio data is not in the expected format
            user_portfolio_data = {}
            # You could also return a message like:
            # "Your portfolio data is not correctly configured. Please contact support."

        if not user_portfolio_data:
            # Optional: If user has no portfolio, you could guide them or inform them.
            # For now, PortfolioAssistant will be initialized with an empty portfolio
            # and will respond accordingly (e.g., "Your portfolio is currently empty.").
            pass

        try:
            portfolio_agent = PortfolioAssistant(portfolio=user_portfolio_data)
            portfolio_response = portfolio_agent.ask(message)
            return portfolio_response
        except Exception as e:
            print(f"Error during PortfolioAssistant interaction: {e}")
            return "Sorry, I encountered an error while trying to access portfolio information."
    # --- End Portfolio Assistant Integration ---

    # Existing logic for profile questions / other reports
    # Note: The 'exported' flag's state management as a local variable is fragile.
    # It will reset on each call. Consider moving this state to global_session
    # or checking profile completeness directly from global_session.current_user.
    current_user_dict = global_session.current_user.to_dict()

    user_structure = """
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
  """
    system_prompt1 = f"""
  {user_structure} this is structure of a user. And {current_user_dict} is the user logged in right now.
  You are responsible for asking relative questions and getting answers about user's fields. First check if the user has already filled the fields.
  If the user has already filled the fields, you can skip asking them and say "which operation you want to perform next?".
  If the user has not filled the fields, ask them in a conversational way.
  Ask and fill required: true fields certainly.
  Fill them in order and ask follow up questions dont move to the next question until 
  the answers is satisfactory expect clarity in the answers from the user
 
  Do NOT ask anything other than these fields.
  Do NOT add any fields other than given ones.
  Do NOT miss any attributes make sure you ask all of them and ask them in order.
  Do NOT change name of fields. Do NOT modify the structure.
  Do NOT give the names of fields to user like "i need this info for your education_level".
 
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

    # This 'exported' variable's scope is local to this function call.
    # This means its state isn't preserved across multiple calls to message_chat
    # for the same user session if the profile isn't fully completed in one go.
    # A more robust approach would be to check if the necessary fields in
    # global_session.current_user are filled.
    # exported = False # This will reset on every call.

    # Example: Check if profile seems complete based on a few key fields
    # This is a more robust way to check than a local 'exported' flag.
    profile_seems_complete = all(
        current_user_dict.get(key) for key in ["name_surname", "email", "age"] # Add other essential fields
    )

    if not profile_seems_complete: # If profile is not complete, go through profile filling
        # Only send system_prompt1 if it's the beginning of the profile conversation
        # This check is basic; you might need more sophisticated history tracking.
        # A better way: manage a 'profile_filling_mode' state in global_session.
        
        # Simplified history check for sending system_prompt1
        # This assumes that if system_prompt1 was the last thing the user part of history,
        # we are continuing a profile filling conversation.
        # A more robust state management (e.g., in global_session) is recommended.
        
        send_initial_profile_prompt = True
        if chat.history:
            # Check if the last model message or user message implies we are in profile filling.
            # This is still a heuristic.
            for entry in reversed(chat.history):
                if entry.role == 'model' and "which operation you want to perform next?" in entry.parts[0].text.lower():
                    send_initial_profile_prompt = False # Profile was likely just completed
                    break
                if entry.role == 'user' and system_prompt1 in entry.parts[0].text: # if prompt1 was sent by us
                    send_initial_profile_prompt = False # We are likely mid-conversation for profile
                    break
            if not chat.history: # No history, definitely send it
                 send_initial_profile_prompt = True


        if send_initial_profile_prompt:
            # Consider clearing history or using a dedicated chat for profile filling
            # to avoid mixing contexts if the main 'chat' object is used for other things.
            # For this example, we'll send it if it seems like a new profile session.
            chat.send_message(system_prompt1)

        response = chat.send_message(message)
        bot_reply = response.text
    
        if "```json" in bot_reply:
            # IMPORTANT: Here you should parse the json from bot_reply
            # and update global_session.current_user with the new data.
            # e.g., 
            # import json
            # extracted_json_string = bot_reply[bot_reply.find("```json")+7 : bot_reply.rfind("```")]
            # try:
            #   new_data = json.loads(extracted_json_string)
            #   for key, value in new_data.items():
            #       if hasattr(global_session.current_user, key):
            #           setattr(global_session.current_user, key, value)
            #   # Persist to DB if necessary: db.update_user(global_session.current_user.email, new_data)
            #   bot_reply = "Bot: Your profile has been updated based on our conversation. You can now ask for a report or other information.\\n\\n" + bot_reply
            #   profile_seems_complete = True # Update state
            # except json.JSONDecodeError:
            #   bot_reply = "Bot: I tried to update your profile but received an unexpected format. Let's try that part again.\\n\\n" + bot_reply
            #
            # For now, just a placeholder message:
            bot_reply = "Bot: Your profile information is being processed. You can now ask for a report or other information.\\n\\n" + bot_reply
            # After this, profile_seems_complete should ideally be re-evaluated or set to True.
        return bot_reply
    else: # Profile is complete, now use system_prompt2 for report selection
        # Send system_prompt2 to guide the user for next actions
        # Avoid sending it repeatedly if already in this state.
        send_report_prompt = True
        if chat.history:
            for entry in reversed(chat.history):
                if entry.role == 'user' and system_prompt2 in entry.parts[0].text:
                    send_report_prompt = False
                    break
        
        if send_report_prompt:
            chat.send_message(system_prompt2) 

        response = chat.send_message(message)
        bot_reply = response.text
        # TODO: Add logic here to call other agents (longevity, health)
        # based on user's choice from system_prompt2 or the content of 'message'.
        # For example:
        # if "retirement plan" in message.lower():
        #   from longevity_agent import LongevityAgent # Assuming you have this
        #   longevity_agent = LongevityAgent(user_data=current_user_dict)
        #   return longevity_agent.get_retirement_plan(message) # Or similar method
        return bot_reply
