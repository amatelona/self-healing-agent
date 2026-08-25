import streamlit as st
import os
import subprocess
from google import genai

# Setup page layout
st.set_page_config(page_title="Self-Healing AI Agent", layout="wide")
st.title("🧰 Self-Healing Python Code Agent")
st.write("Paste a broken Python script below, and watch the agent fix it in real-time.")

# Set your Gemini Key (or use st.text_input to let recruiters paste theirs)
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
        
        # 2. Run the broken script and capture error
        status_log = st.empty()
        status_log.info("🚀 Running script to capture runtime errors...")
        
        result = subprocess.run(["python", "temp_broken.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            st.success("🎉 Code executed perfectly with no errors!")
            st.code(result.stdout)
        else:
            # 3. Intercept error and send to Gemini
            error_msg = result.stderr
            st.error("❌ Crash Detected!")
            st.text(error_msg)
            
            status_log.warning("🧠 Analyzing traceback with gemini-3.5-flash-lite...")
            
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                prompt = f"Fix this broken Python code. Return ONLY the raw code inside a markdown block.\n\nCode:\n{user_code}\n\nError:\n{error_msg}"
                
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt
                )
                
                # 4. Extract code block
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
