import streamlit as st
import os
import subprocess
from google import genai

# Setup page layout
st.set_page_config(page_title="Self-Healing AI Agent", layout="wide")
st.title("🧰 Self-Healing Python Code Agent")
st.write("Paste a broken Python script below, and watch the agent fix it in real-time.")

# Check if Gemini key is set in Streamlit Secrets, otherwise fallback to sidebar input
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    GEMINI_API_KEY = st.sidebar.text_input("Paste your Gemini API Key here:", type="password")

# Two columns layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input Your Broken Code")
    # Sample error-prone code as default
    default_code = 'data = {"name": "Alice"}\nprint(data["age"]) # This will throw a KeyError!'
    user_code = st.text_area("Python Script:", value=default_code, height=300)
    
    run_btn = st.button("🔧 Heal My Code", type="primary")

if run_btn:
    # 1. Save user code to a temporary file
    with open("temp_broken.py", "w") as f:
        f.write(user_code)
        
    with col2:
        st.subheader("2. Agent Execution Logs")
        
        status_log = st.empty()
        status_log.info("🚀 Running script to capture runtime errors...")
        
        # Initialize default state values
        error_detected = False
        error_msg = ""
        
        # 2. Run script inside a try-block with a strict 5-second timeout safety guard
        try:
            result = subprocess.run(["python", "temp_broken.py"], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                st.success("🎉 Code executed perfectly with no errors!")
                st.code(result.stdout)
            else:
                error_detected = True
                error_msg = result.stderr
                st.error("❌ Crash Detected!")
                st.text(error_msg)
                
        except subprocess.TimeoutExpired:
            error_detected = True
            error_msg = "TimeoutExpired: The script execution exceeded the 5-second threshold. Possible infinite loop detected."
            st.error("❌ Timeout / Infinite Loop Detected!")
            st.text(error_msg)
            
        # 3. If any error or timeout occurred, intercept and pass context to Gemini
        if error_detected:
            if not GEMINI_API_KEY:
                st.warning("⚠️ Missing API Key! Please paste your Gemini API Key in the sidebar or save it in App Secrets.")
            else:
                status_log.warning("🧠 Analyzing traceback with gemini-3.5-flash-lite...")
                
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    prompt = f"Fix this broken Python code. Break any infinite loops or handle missing data appropriately. Return ONLY the raw code inside a markdown block.\n\nCode:\n{user_code}\n\nError:\n{error_msg}"
                    
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=prompt
                    )
                    
                    # 4. Extract code block safely
                    raw_response = response.text
                    if "```python" in raw_response:
                        fixed_code = raw_response.split("```python")[1].split("```")[0].strip()
                    elif "```" in raw_response:
                        fixed_code = raw_response.split("```")[1].split("```")[0].strip()
                    else:
                        fixed_code = raw_response.strip()
                    
                    # 5. Overwrite and display fix
                    st.success("✅ Code Healed Successfully!")
                    st.code(fixed_code, language="python")
                    
                    # Save fixed code back to check it
                    with open("temp_broken.py", "w") as f:
                        f.write(fixed_code)
                    status_log.success("🏁 Automation Complete.")
                    
                except Exception as e:
                    st.error(f"API Error: {str(e)}")
