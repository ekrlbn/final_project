from datetime import datetime, timedelta
import portfolio_assistant
import google.generativeai as genai
import os
import yfinance as yf

base_date = datetime.today()
print(base_date)



genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
def weather_in_tokyo():
    '''returns the weather in Tokyo'''
    return 25
tools = [weather_in_tokyo]


#model = genai.GenerativeModel("gemini-1.5-flash", tools=tools)


sample_portfolio = {"AAPL": 10, "MSFT": 5, "GOOG": 15}
assistant = portfolio_assistant.PortfolioAssistant(portfolio=sample_portfolio)



model = genai.GenerativeModel("gemini-1.5-flash", tools=tools)
print(model)
response = model.generate_content("What is the weather in Tokyo?")
print(response)
print("**********")
print(response.candidates[0].content.parts[0].text)
print(response.candidates[0].content.parts[0].function_call)




sample_portfolio = {"AAPL": 10, "MSFT": 5, "GOOG": 15}
assistant = portfolio_assistant.PortfolioAssistant(portfolio=sample_portfolio)
print("Portfolio Assistant Initialized. Ask a question.")
    
#     # Test cases
queries = [
"What's the current price of Apple?",
"What is the Apple price 2 days ago?",
"What was the price of GOOG yesterday?",
"What was my last question?",
"",
"Tell me about my AAPL and MSFT holdings value.",
"What are the tickers for my stocks?", # Should use extract_tickers_from_text via LLM
"What is the weather like?" # Off-topic
]



for query in queries:
    response = assistant.ask_generate(query)
    print(response)

        
print("**********")
#print(fetch_price("AAPL",days_ago=2))


#for query in queries:
#    print(f"\\nUser: {query}")
#    response_text = assistant.ask(query)
#    print(f"Assistant: {response_text}")

#     # Test with a specific date
#print(f"\\nUser: What was the price of AAPL 7 days ago?")
#response_text = assistant.ask("What was the price of AAPL 7 days ago?")
#print(f"Assistant: {response_text}")