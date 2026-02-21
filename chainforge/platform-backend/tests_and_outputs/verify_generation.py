import sys
import os
import zipfile
import io
import json

# Add current directory to sys.path to ensure we can import from generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generator.builder import ChainBuilder
from schemas import Project

def verify_generation():
    print("Starting verification of blockchain generation...")

    # 1. Create a Mock Project with new configuration options
    mock_config = {
        "networkType": "public",
        "publicConsensus": "pow",
        "publicSyncMode": "fast",      # Testing New Feature
        "publicRuntime": "evm",        # Testing New Feature
        "publicToken": "native",
        "publicDeployment": "zip"
    }

    mock_project = Project(
        id=123,
        name="Test Chain",
        description="A test chain for verification",
        owner_id=1,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        config=mock_config
    )

    # 2. Run the Builder
    try:
        builder = ChainBuilder(mock_project)
        zip_bytes = builder.build_package()
        print("Successfully generated zip package.")
    except Exception as e:
        print(f"Error during generation: {e}")
        return False

    # 3. Inspect the Zip Content
    required_files = [
        "modules/sync/fast.py",
        "modules/sync/light.py",
        "modules/sync/realtime.py",
        "modules/vm/evm.py", 
        "modules/vm/wasm.py",
        "di.py",
        "main.py",
        "config/genesis.json"
    ]
    
    missing_files = []
    
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            file_list = zf.namelist()
            print(f"Zip contains {len(file_list)} files.")
            
            # Check for required files
            for file in required_files:
                if file not in file_list:
                    missing_files.append(file)
            
            if missing_files:
                print(f"FAILED: The following files are missing from the zip: {missing_files}")
                return False
            else:
                print("SUCCESS: All required modules are present in the zip.")

            # Check genesis.json content
            with zf.open("config/genesis.json") as f:
                genesis_config = json.load(f)
                print(f"Genesis Config: {json.dumps(genesis_config, indent=2)}")
                
                if genesis_config.get("publicSyncMode") == "fast":
                    print("SUCCESS: Config correctly propagated 'fast' sync mode.")
                else:
                    print(f"FAILED: Sync mode mismatch. Expected 'fast', got '{genesis_config.get('publicSyncMode')}'")
                    return False

    except Exception as e:
        print(f"Error reading zip file: {e}")
        return False

    return True

if __name__ == "__main__":
    if verify_generation():
        print("\nVerification PASSED!")
        sys.exit(0)
    else:
        print("\nVerification FAILED!")
        sys.exit(1)
