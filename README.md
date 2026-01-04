# AUTO TRADING TERMINAL

professional MT5-style chart analysis terminal (analysis-only).
Auto trading with an algorithm of 60% success rate 
## Setup
1. python -m venv venv
2. venv\Scripts\activate
3. pip install -r requirements.txt
4. python -m app.main(RUN)
5. You must have the program MT5 with a working account DEMO(recommended)
IMPORTANT STEP (IF YOU NEED AI ANALYSIS): MAKE AN .ENV FILE AND PUT YOUR AI API IN IT MUST BE OPEN ROUTER (FREE) WITH THIS LAYOUT:
OPENROUTER_API_KEY="your api key"
OPENROUTER_MODEL=deepseek/deepseek-chat
