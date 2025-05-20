from google import genai
import yfinance as yf
from datetime import datetime, timedelta
import re
import os
gemini_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=gemini_key)



detector_chat = client.chats.create(model="gemini-1.5-flash")
context_chat = client.chats.create(model="gemini-1.5-flash")
portfolio = {
    "AAPL": 10,
    "TSLA": 5,
    "MSFT": 7
}
portfolio_summary = "\n".join(f"{ticker}: {shares} shares" for ticker, shares in portfolio.items())
initial_context = f"""
You are a financial assistant that helps a user manage their portfolio.
The user's portfolio includes: {portfolio_summary}
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
context_chat.send_message(initial_context)
def get_query_type(text):
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
        response = detector_chat.send_message(prompt)
        return response.text.strip().lower()
    except:
        return "general"

def extract_tickers(text):
    prompt = f"""
You are a financial assistant. The user might refer to stocks in the following ways:
- Using ticker symbols (e.g., AAPL)
- Using company names (e.g., Apple, Microsoft)
- Saying "my stocks" or "my portfolio" to refer to their whole portfolio
Their portfolio contains: {', '.join(portfolio.keys())}
Your job:
1. Read their message and return ALL relevant tickers.
2. If they say "my stocks", return ALL tickers in the portfolio.
3. If they mention companies outside the portfolio (e.g., Google), still return those tickers.
4. Always respond with a comma-separated list of tickers (e.g., AAPL,GOOG,MSFT)
User message: "{text}"
Return only a comma-separated list of valid stock tickers.
"""
    try:
        response = detector_chat.send_message(prompt)
        raw = response.text.strip().upper()
        tickers = [ticker.strip() for ticker in raw.split(",") if re.match(r"^[A-Z]{1,6}$", ticker.strip())]
        return list(set(tickers)) if tickers else list(portfolio.keys())
    except:
        return list(portfolio.keys())

def extract_days_ago(text):
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
        response = detector_chat.send_message(prompt)
        match = re.search(r'\d+', response.text)
        return int(match.group()) if match else 0
    except:
        return 0

def fetch_price(ticker, days_ago):
    try:
        date = datetime.today() - timedelta(days=days_ago)
        while date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
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

def classify_query(text):
    prompt = f"""
You are a classifier for a portfolio assistant.
Classify the user's message as either:
- data_query → asks for prices, values, worth, etc.
- general_chat → unrelated to stock prices

User: "{text}"
Answer only with: data_query or general_chat
"""
    try:
        response = detector_chat.send_message(prompt)
        return "data_query" if "data_query" in response.text.lower() else "general_chat"
    except:
        return "data_query"
def handle_query(user_input):
    query_type = get_query_type(user_input)
    tickers = extract_tickers(user_input)
    days_ago = extract_days_ago(user_input)
    if query_type == "ownership":
        return "\n".join([f"You own {portfolio.get(t, 0)} shares of {t}" for t in tickers])
    elif query_type == "portfolio_value":
        total = 0.0
        breakdown = []
        for t in tickers:
            try:
                data = yf.Ticker(t).history(period="1d")
                if not data.empty:
                    price = data["Close"].iloc[0]
                    value = price * portfolio.get(t, 0)
                    breakdown.append(f"{t}: {portfolio[t]} × ${price:.2f} = ${value:.2f}")
                    total += value
            except:
                continue
        breakdown.append(f"\nTotal estimated portfolio value: ${total:.2f}")
        return "\n".join(breakdown)

    elif query_type == "price":
        return "\n".join([fetch_price(t, days_ago) for t in tickers])

    else:
        response = context_chat.send_message(user_input)
        return response.text.strip()
print("Chat with finbot (type 'exit' to quit):")
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye.")
        break

    classification = classify_query(user_input)
    if classification == "data_query":
        result = handle_query(user_input)
        print("Gemini:", result)
    else:
        response = context_chat.send_message(user_input)
        print("Gemini:", response.text.strip())
