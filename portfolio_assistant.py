import google.generativeai as genai
import yfinance as yf
from datetime import datetime, timedelta
import re
import os
# import json # Not strictly needed for this version of FunctionResponse handling

class PortfolioAssistant:
    def __init__(self, portfolio: dict):
        self.portfolio = portfolio
        self.portfolio_summary = "\\n".join(f"- {ticker}: {shares} shares" for ticker, shares in portfolio.items())

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Define tool implementations mapping
        self.tool_functions = {
            "fetch_price": self.fetch_price,
            "extract_tickers_from_text": self.extract_tickers_from_text,
        }

        # Define tools schema for the LLM
        self.tools_schema = [
            {
                "name": "fetch_price",
                "description": "Fetches the historical closing stock price for a given ticker symbol and a specific number of days ago. Use for any questions about stock prices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol (e.g., 'AAPL' for Apple)."
                        },
                        "days_ago": {
                            "type": "integer",
                            "description": "Number of days in the past to fetch the price for (e.g., 0 for today, 1 for yesterday, 7 for a week ago). The current date is 21 Mayıs 2025."
                        }
                    },
                    "required": ["ticker", "days_ago"]
                }
            },
            {
                "name": "extract_tickers_from_text",
                "description": "Extracts potential stock ticker symbols (e.g., AAPL, MSFT) found directly in a piece of text. Returns a list of unique ticker-like strings. For company names not in ticker format, you (the main assistant) should try to map them to tickers using your general knowledge before calling fetch_price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text_to_scan": {
                            "type": "string",
                            "description": "The text to scan for ticker symbols."
                        }
                    },
                    "required": ["text_to_scan"]
                }
            }
        ]

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Or your preferred model
            tools=self.tools_schema
        )

        initial_context_prompt = f"""
You are a specialized financial assistant. Your sole purpose is to help users with their stock portfolio.
The current date is 21 Mayıs 2025.
Your user's current portfolio consists of:
{self.portfolio_summary}

Your capabilities and responsibilities:
1.  **Answer Stock Price Questions**:
    *   If the user asks for a stock price (current or past), you MUST use the `fetch_price` tool.
    *   You need to determine the correct 'ticker' and 'days_ago' from the user's query to use the `fetch_price` tool. For 'days_ago', calculate based on the current date 21 Mayıs 2025.
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
        self.chat = self.model.start_chat(
            history=[
                {'role': 'user', 'parts': [{'text': initial_context_prompt}]},
                {'role': 'model', 'parts': [{'text': "Understood. I am ready to assist with your portfolio. How can I help you today?"}]}
            ]
        )

    def fetch_price(self, ticker: str, days_ago: int) -> str:
        try:
            # Current date is fixed for consistent testing if needed, but using live datetime.today()
            # For days_ago calculation, the LLM uses the fixed current date from the prompt.
            base_date = datetime(2025, 5, 21) # As specified in prompt context for LLM
            date_to_fetch = base_date - timedelta(days=days_ago)
            
            # Adjust to the previous weekday if it's a weekend
            while date_to_fetch.weekday() >= 5: # 5 for Saturday, 6 for Sunday
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

    def extract_tickers_from_text(self, text_to_scan: str) -> list[str]:
        # Regex to find patterns like AAPL, GOOG, BRK.A, MSFT.
        tickers = re.findall(r'\\b[A-Z]{1,6}(?:\\.[A-Z])?\\b', text_to_scan.upper())
        unique_tickers = sorted(list(set(tickers)))

        if not unique_tickers and any(keyword in text_to_scan.lower() for keyword in ["my stock", "my portfolio", "all my shares", "everything i own", "all of them"]):
            return list(self.portfolio.keys())
        return unique_tickers

    def ask(self, user_prompt: str) -> str:
        try:
            response = self.chat.send_message(user_prompt)
            while True:
                candidate = response.candidates[0]
                if not candidate.content.parts:
                    return "I received an empty response. Please try again."

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
                            # Provide a more structured error to the LLM
                            function_response_content = f"Error executing tool {function_name}: {str(e)}"
                        
                        api_response_part = genai.types.Part(
                            function_response=genai.types.FunctionResponse(
                                name=function_name,
                                response={'result': function_response_content}
                            )
                        )
                        response = self.chat.send_message(parts=[api_response_part])
                    else:
                        # This case should ideally not be reached if the model only calls defined tools
                        error_message = f"Error: The model tried to call an unknown function: {function_name}."
                        api_response_part = genai.types.Part(
                            function_response=genai.types.FunctionResponse(
                                name=function_name,
                                response={'error': error_message} # Send error back
                            )
                        )
                        # It might be better to not send this back or handle differently,
                        # as the model shouldn't call unknown functions.
                        # For now, let's assume the model behaves. If not, this part needs review.
                        # Or, just return an error message to the user.
                        return error_message 
                else:
                    if hasattr(part, 'text') and part.text:
                        return part.text.strip()
                    else:
                        return "I'm sorry, I couldn't generate a text response for that."
        except Exception as e:
            print(f"Error in PortfolioAssistant.ask: {type(e).__name__} - {e}")
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
