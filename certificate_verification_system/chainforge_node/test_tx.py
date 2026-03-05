import sys
sys.path.append('c:/Users/ARTH PATEL/OneDrive/Desktop/ARTH/Sem-6/Blockchain/certificate_verification_system/backend')
from chainforge_client import chainforge_client
import auth

# Get a real keypair
priv, pub = auth.generate_keypair()
print(f"Generated Key: {pub}")

resp = chainforge_client.execute_contract(
    user_address=pub,
    private_key=priv,
    contract_name="CertificateRegistry",
    method_name="issue_certificate",
    params={"cert_id": "TEST-123", "student_name": "Test", "degree": "Test", "year": 2026, "issuer_id": pub}
)

print(f"Response: {resp}")
