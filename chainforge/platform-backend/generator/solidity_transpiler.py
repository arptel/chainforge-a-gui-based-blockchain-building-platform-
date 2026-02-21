import os
import google.generativeai as genai

# Try to get API key from environment, or use a default if user provides one later
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAVA0cKA2SwVXh2Btwo4xpkHvN2S-gwXyQ")

def configure_gemini(api_key):
    global GEMINI_API_KEY
    GEMINI_API_KEY = api_key
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize if key exists in env
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def transpile(solidity_code: str, contract_name: str) -> str:
    """
    Uses Gemini LLM to transpile Solidity code into a Python class compatible
    with the ChainForge PythonVM.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing. Please provide a Gemini API Key to use the Solidity transpiler.")

    prompt = f"""
You are an expert compiler engineer. I need you to transpile the following Solidity smart contract into a Python class for a custom blockchain runtime.

**Rules for the Python Output:**
1. The output MUST be valid Python 3 code.
2. The Python class name MUST be exactly `{contract_name}`.
3. Every method in the class MUST take `self` as the first argument.
4. The smart contract has access to persistent blockchain state via `self.ctx.state` (which is a Python dictionary).
5. All Solidity `mapping` or state variables must be read from and written to `self.ctx.state`. 
   - Example Solidity: `mapping(address => uint256) balances; balances[msg.sender] = 10;`
   - Example Python: 
     ```python
     balances = self.ctx.state.get('balances', {{}})
     balances[self.ctx.msg_sender] = 10
     self.ctx.state['balances'] = balances
     ```
6. The sender of the transaction is available at `self.ctx.msg_sender` (equivalent to `msg.sender` in Solidity).
7. Return ONLY the raw Python code. Do not include markdown formatting like ```python ... ```. Do not include any explanations.
8. DO NOT define an `__init__` method that takes arguments other than `self`. The `ctx` variable is magically injected onto the instance by the runtime, you do not need to accept it in the constructor.

**Solidity Source Code:**
{solidity_code}
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Clean up the response in case the LLM still outputs markdown blocks
        python_code = response.text.strip()
        if python_code.startswith("```python"):
            python_code = python_code[9:]
        if python_code.startswith("```"):
            python_code = python_code[3:]
        if python_code.endswith("```"):
            python_code = python_code[:-3]
            
        return python_code.strip()
        
    except Exception as e:
        print(f"Error during LLM transpilation: {e}")
        raise
