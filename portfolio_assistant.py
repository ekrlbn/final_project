import google.generativeai as genai
import yfinance as yf
from datetime import datetime, timedelta
import re

class PortfolioAssistant:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.portfolio_summary = "\n".join(f"{ticker}: {shares} shares" for ticker, shares in portfolio.items())

        # Configure Gemini API
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.detector_chat = self.model.start_chat()
        self.context_chat = self.model.start_chat()

        # Initialize context
        initial_context = f"""
You are a financial assistant that helps a user manage their portfolio.
The user's portfolio includes: {self.portfolio_summary}
Your responsibilities:
- Respond to questions about stock prices (current or past).
- Respond to questions about ownership ("What do I own?").
- Respond to general inquiries about the value or performance of their portfolio.
- If the user asks for explanations or calculations, you MUST explain in detail how the answer was computed.
- Always include intermediate steps if the user asks for the math behind portfolio values.
Do NOT answer unrelated questions such as:
- Weather
- Emotions or mental health
- Jokes, general knowledge, or personal advice history or anything outside of finance 
If the user asks something outside your domain, firmly respond:
"I'm a financial assistant, so I can only help with stock and portfolio-related questions."
If the user asks something vague (e.g., "how is my portfolio?"), assume they mean to check its current value.
Only give concise, helpful answers unless explanation is explicitly requested — in that case, show full calculation logic.
Never say you don't have access to real-time data. If needed, ask for clarification like: "Which stock do you mean?"
Return ticker prices using actual data, using the `fetch_price()` and portfolio context provided.
"""
        self.context_chat.send_message(initial_context)

    def get_query_type(self, text):
        prompt = f"""
Classify the user's message as one of:
- "ownership" → Asking how many shares they own
- "price" → Asking about stock price
- "portfolio_value" → Asking total worth of their portfolio
- "general" → Anything else
Message: "{text}"
Respond with ONLY one of: ownership, price, portfolio_value, general
"""
        try:
            response = self.detector_chat.send_message(prompt)
            return response.text.strip().lower()
        except:
            return "general"

    def extract_tickers(self, text):
        prompt = f"""
You are a financial assistant. The user might refer to stocks in the following ways:
- Using ticker symbols (e.g., AAPL)
- Using company names (e.g., Apple, Microsoft)
- Saying "my stocks" or "my portfolio" to refer to their whole portfolio
Their portfolio contains: {', '.join(self.portfolio.keys())}
Your job:
1. Read their message and return ALL relevant tickers.
2. If they say "my stocks", return ALL tickers in the portfolio.
3. If they mention companies outside the portfolio (e.g., Google), still return those tickers.
4. Always respond with a comma-separated list of tickers (e.g., AAPL,GOOG,MSFT)
User message: "{text}"
Return only a comma-separated list of valid stock tickers.
"""
        try:
            response = self.detector_chat.send_message(prompt)
            raw = response.text.strip().upper()
            tickers = [ticker.strip() for ticker in raw.split(",") if re.match(r"^[A-Z]{1,6}$", ticker.strip())]
            return list(set(tickers)) if tickers else list(self.portfolio.keys())
        except:
            return list(self.portfolio.keys())

    def extract_days_ago(self, text):
        prompt = f"""
Extract how many days ago the user is referring to in this sentence.
also the dates such as 2025 05 07 or the 7th of May.
If the year is not specified, assume 2025.

Examples:
- "2 days ago" → 2
- "yesterday" → 1
- "today" → 0
- "last week" → 7
- "last month" → 30

Text: "{text}"
Answer with a number only.
"""
        try:
            response = self.detector_chat.send_message(prompt)
            match = re.search(r'\d+', response.text)
            return int(match.group()) if match else 0
        except:
            return 0

    def fetch_price(self, ticker, days_ago):
        try:
            date = datetime.today() - timedelta(days=days_ago)
            while date.weekday() >= 5:
                date -= timedelta(days=1)
            start = date.strftime('%Y-%m-%d')
            end = (date + timedelta(days=1)).strftime('%Y-%m-%d')

            t = yf.Ticker(ticker)
            data = t.history(start=start, end=end)

            if not data.empty:
                price = data["Close"].iloc[0]
                return f"{ticker} closing price on {start} was ${price:.2f}"
            else:
                return f"No data found for {ticker} on {start}."
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_query(self, user_input):
        query_type = self.get_query_type(user_input)
        tickers = self.extract_tickers(user_input)
        days_ago = self.extract_days_ago(user_input)

        if query_type == "ownership":
            return "\n".join([f"You own {self.portfolio.get(t, 0)} shares of {t}" for t in tickers])

        elif query_type == "portfolio_value":
            total = 0.0
            breakdown = []
            for t in tickers:
                try:
                    data = yf.Ticker(t).history(period="1d")
                    if not data.empty:
                        price = data["Close"].iloc[0]
                        value = price * self.portfolio.get(t, 0)
                        breakdown.append(f"{t}: {self.portfolio[t]} × ${price:.2f} = ${value:.2f}")
                        total += value
                except:
                    continue
            breakdown.append(f"\nTotal estimated portfolio value: ${total:.2f}")
            return "\n".join(breakdown)

        elif query_type == "price":
            return "\n".join([self.fetch_price(t, days_ago) for t in tickers])

        else:
            response = self.context_chat.send_message(user_input)
            return response.text.strip()
