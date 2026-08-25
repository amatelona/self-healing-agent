#  AI-Driven Automated Code Repair Agent

We’ve all been there: your code crashes in production, and you have to spend time digging through confusing terminal logs to find the typo or missing key. I wanted to build something better.

This project is a smart background assistant that turns passive error logging into active, self-healing code. It monitors Python scripts while they run, catches crashes the moment they happen, asks a lightweight AI model (`gemini-3.5-flash-lite`) for a solution, and rewrites the file with a working fix entirely on its own.

##  What It Does
- **Catches Errors Silently:** It uses Python's native `subprocess` tool to watch your scripts run in an isolated space. If something breaks, it grabs the exact error message without crashing your main setup.
- **Smart Healing Loop:** It sends the broken code and the error straight to Gemini. It strips out the AI's conversational text, checks the raw code syntax, and updates your file. It will even try up to 3 times if the first fix isn't perfect.
- **Web Dashboard:** I wrapped the backend logic into a clean, simple Streamlit web page. You can paste any broken Python script on the left and watch the agent diagnose and repair it live on the right.
- **Safe and Secure:** No hardcoded API keys here! The project handles your secret access tokens using secure, encrypted cloud environments.

##  The Tech Stack
- **Language:** Python
- **AI Brain:** Google Gemini API (`gemini-3.5-flash-lite`)
- **System Magic:** Python's native `subprocess` and `re` (Regex) modules
- **Web App Layout:** Streamlit Cloud Framework

##  How to Try It Out
1. **Live Web Link:** Click the website link in the "About" section on the right side of this GitHub page to test it out right in your browser!
2. **Run It Locally:**
   If you want to run it on your own machine, open your terminal and run:
   ```bash
   pip install google-genai streamlit
   python -m streamlit run app.py
   ```
