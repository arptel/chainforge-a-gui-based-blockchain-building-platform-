# Using the Smart Contract API

You asked about the benefits of using an API versus directly importing functions, and how to use the generated API. This guide explains the approach and provides a simple example.

## Why use an API?

When building a blockchain platform, your users (who create the chains) might want to interact with their smart contracts from various environments—web apps, mobile apps, or other backend systems.

### 1. Language Agnostic
**API**: You can call the API from ANY language (JavaScript, Python, Go, Rust, etc.) using standard HTTP requests.
**Import**: You can only import Python functions into other Python code. If your user wants to build a React website for their chain, they can't "import" the Python contract.

### 2. Remote Access
**API**: The smart contract runs on the blockchain node (server). You can interact with it from your laptop, a different server, or a public website.
**Import**: You would need to run your code on the SAME machine as the blockchain node to import the file.

### 3. Separation of Concerns
**API**: The blockchain logic is isolated. If you update the smart contract logic (e.g., bug fix), the API remains stable, and consumers don't necessarily need to redeploy their apps.
**Import**: Tightly couples your application code with the contract implementation.

### 4. Security & Permissions
**API**: We generated **API Keys** for each contract. The API layer enforces security, ensuring only authorized users can execute sensitive contract methods.
**Import**: Direct imports bypass this security layer unless you manually implement it everywhere.

---

## How to use the API (Example)

Let's say you created a **Storage** contract using the wizard.
- **Contract Name**: `MyStorage`
- **ID**: `contract_123`
- **API Key**: `sk_test_123`
- **Method**: The contract has a method `store(value)` and `retrieve()`.

### Example: Python Client

This script acts as a user application wanting to save data to the blockchain.

```python
import requests

# Configuration
NODE_URL = "http://localhost:8000"  # Address of the running blockchain node
CONTRACT_ID = "contract_123"        # ID from the wizard
API_KEY = "sk_test_123"             # Key from the wizard

def store_value(value):
    url = f"{NODE_URL}/api/v1/contracts/execute/{CONTRACT_ID}/store"
    headers = {"x-api-key": API_KEY}
    payload = {"args": {"value": value}}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"Success: {response.json()}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def get_value():
    url = f"{NODE_URL}/api/v1/contracts/execute/{CONTRACT_ID}/retrieve"
    headers = {"x-api-key": API_KEY}
    # No args for retrieve
    payload = {"args": {}} 
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"Current Value: {response.json()}")

# --- Usage ---
if __name__ == "__main__":
    print("Storing value 42...")
    store_value(42)
    
    print("Reading value...")
    get_value()
```

### Example: JavaScript (Frontend)

```javascript
const storeValue = async (val) => {
  const response = await fetch('http://localhost:8000/api/v1/contracts/execute/contract_123/store', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': 'sk_test_123'
    },
    body: JSON.stringify({
      args: { value: val }
    })
  });
  
  const data = await response.json();
  console.log(data);
}
```

By providing these standard API endpoints, you enable your users (the blockchain creators) to instantly build user-facing applications on top of their new chain without needing to understand the underlying Python/Solidity code or networking logic.
