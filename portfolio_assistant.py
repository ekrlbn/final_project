import google.generativeai as genai
import yfinance as yf
from datetime import datetime, timedelta
import re
import os




class PortfolioAssistant:
    '''This class is used to answer stock price questions and portfolio related questions'''
    def __init__(self, portfolio: dict):
        self.portfolio = portfolio
        self.portfolio_summary = "\\n".join(f"- {ticker}: {shares} shares" for ticker, shares in portfolio.items())

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        def fetch_price(ticker: str, days_ago: int) -> str:
            '''returns the closing price for a stock on a specific date. If date is not specified, it uses the current date.'''
            try:
                # For days_ago calculation, the LLM will use the actual current date.
                base_date = datetime.today()
                date_to_fetch = base_date - timedelta(days=days_ago)
            
                 # Adjust to the previous weekday if it's a weekend
                while date_to_fetch.weekday() >= 5: 
                    date_to_fetch -= timedelta(days=1)
            
                start_date_str = date_to_fetch.strftime('%Y-%m-%d')
                end_date_str = (date_to_fetch + timedelta(days=1)).strftime('%Y-%m-%d')

                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date_str, end=end_date_str, auto_adjust=True, prepost=False)

                if not data.empty and 'Close' in data.columns:
                    price = data["Close"].iloc[0]
                    # Ensure the date reported is the actual date from yfinance data
                    actual_date_str = data.index[0].strftime('%Y-%m-%d')
                    return f"The closing price for {ticker} on {actual_date_str} was ${price:.2f}."
                else:
                    # Fallback for days_ago=0 if specific date fails (e.g. market closed, very recent)
                    if days_ago == 0:
                        # Try to get the most recent info available
                        current_data = stock.history(period="2d", auto_adjust=True, prepost=False) # get last 2 days to ensure one is trading
                    if not current_data.empty and 'Close' in current_data.columns:
                        price = current_data["Close"].iloc[-1]
                        actual_date_str = current_data.index[-1].strftime('%Y-%m-%d')
                        return f"The most recent closing price for {ticker} on {actual_date_str} is ${price:.2f}."
                return f"No price data found for {ticker} for the target date around {date_to_fetch.strftime('%Y-%m-%d')}."
            except Exception as e:
                return f"Error fetching price for {ticker}: {str(e)}"
        # The following line caused the TypeError and is removed:
        # functions_to_llm[extract_tickers_from_text,fetch_price]
        
        # Create a list of the function objects to pass to the model
        defined_tools = [fetch_price]

        # Populate self.tool_functions for the 'ask' method to execute the calls.
        # The keys (function names) must match what the LLM will send in the function_call.
        self.tool_functions = {
            "fetch_price": fetch_price,
        }
    
        initial_context_prompt = f"""
You are a specialized financial assistant. Your sole purpose is to help users with their stock portfolio.
The current date is {datetime.today().strftime('%d %B %Y')}.
Your user's current portfolio consists of:
{self.portfolio_summary}

Your capabilities and responsibilities:
1.  **Answer Stock Price Questions**:
    *   If the user asks for a stock price (current or past), you MUST use the `fetch_price` tool.
    *   You need to determine the correct 'ticker' and 'days_ago' from the user's query to use the `fetch_price` tool. For 'days_ago', calculate based on the current date {datetime.today().strftime('%d %B %Y')}.
    *   If the user mentions company names (e.g., Apple), you should try to recall the ticker (e.g., AAPL) from your general knowledge. If you need to find ticker-like patterns in a block of text to confirm or extract multiple tickers, use the `extract_tickers_from_text` tool, then use `fetch_price` for each identified ticker.
2.  **Answer Ownership Questions**:
    *   If the user asks what stocks they own or how many shares, refer to the portfolio summary provided above and state it clearly.
3.  **Calculate Portfolio Value**:
    *   If the user asks for the current value of their portfolio (or specific stocks in it), you must:
        a. Identify the relevant tickers. If it's the whole portfolio, use all tickers from the summary. If specific stocks, identify them (use `extract_tickers_from_text` if needed for parsing, or your general knowledge for company names).
        b. For each ticker, use the `fetch_price` tool with `days_ago=0` to get the current price.
        c. Multiply the price by the number of shares (from the portfolio summary).
        d. Sum the values for all relevant tickers.
        e. You MUST explain your calculation steps clearly, showing the price, shares, and individual value for each stock, and then the total.
4.  **Stick to Finance**:
    *   Do NOT answer questions unrelated to finance, stocks, or the user's portfolio (e.g., weather, jokes, personal advice).
    *   If asked an off-topic question, politely respond: "I am a financial assistant and can only help with stock and portfolio-related questions."
5.  **Clarity and Conciseness**:
    *   Be concise unless an explanation or calculation is requested.
    *   Never say you don't have access to real-time data. Use your tools.
    *   If a query is vague (e.g., "how is my portfolio?"), interpret it as a request for its current total value.

You will interact by receiving a user prompt. You can either respond directly or call one of your tools. If you call a tool, you will receive its output and then you can formulate your final response.
"""
        self.model = genai.GenerativeModel(
            system_instruction=initial_context_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.5,
                top_p=0.95,
                top_k=40,
            ),
            model_name="gemini-2.0-flash", # 
            tools=defined_tools  # tool list
        )
        

    def ask_generate(self, user_prompt: str) -> str:
        try:
            # Initial call to the model
            # The 'tools' are already configured on self.model
            current_content_history = [{'role': 'user', 'parts': [{'text': user_prompt}]}]
            response = self.model.generate_content(current_content_history)

            while True:
                candidate = response.candidates[0]
                if not candidate.content.parts:
                    return "I received an empty response. Please try again."

                # Append model's response (which might contain a function call) to history
                # candidate.content is an SDK-provided Content object, which is fine to append directly.
                current_content_history.append(candidate.content)

                part = candidate.content.parts[0]
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    args = {key: value for key, value in function_call.args.items()}

                    if function_name in self.tool_functions:
                        function_to_call = self.tool_functions[function_name]
                        try:
                            function_response_content = function_to_call(**args)
                        except Exception as e:
                            function_response_content = f"Error executing tool {function_name}: {str(e)}"
                        
                        # Construct the function response part as a dictionary
                        tool_response_part_dict = {
                            'function_response': {
                                'name': function_name,
                                'response': {'result': function_response_content}
                            }
                        }
                        
                        # Append the function response to history with role "tool"
                        current_content_history.append({'role': 'tool', 'parts': [tool_response_part_dict]})
                        
                        # Call generate_content again with the updated history
                        response = self.model.generate_content(current_content_history)
                        print(current_content_history)
                    else:
                        error_message = f"Error: The model tried to call an unknown function: {function_name}."
                        return error_message
                else:
                    if hasattr(part, 'text') and part.text:
                        return part.text.strip()
                    else:
                        return "I'm sorry, I couldn't generate a text response for that."
            
        except Exception as e:
            print(f"Error in PortfolioAssistant.ask_generate: {type(e).__name__} - {e}")
            return "I encountered an unexpected error while processing your request. Please try again."

# Example Usage (for testing, not part of the class):
# if __name__ == '__main__':
#     sample_portfolio = {"AAPL": 10, "MSFT": 5, "GOOG": 15}
#     assistant = PortfolioAssistant(portfolio=sample_portfolio)

#     print("Portfolio Assistant Initialized. Ask a question.")
    
#     # Test cases
#     queries = [
#         "What's the current price of Apple?",
#         "How many shares of MSFT do I own?",
#         "What was the price of GOOG yesterday?",
#         "What is the total value of my portfolio?",
#         "Tell me about my AAPL and MSFT holdings value.",
#         "What are the tickers for my stocks?", # Should use extract_tickers_from_text via LLM
#         "What is the weather like?" # Off-topic
#     ]

#     for query in queries:
#         print(f"\\nUser: {query}")
#         response_text = assistant.ask(query)
#         print(f"Assistant: {response_text}")

#     # Test with a specific date
#     print(f"\\nUser: What was the price of AAPL 7 days ago?")
#     response_text = assistant.ask("What was the price of AAPL 7 days ago?")
#     print(f"Assistant: {response_text}")
