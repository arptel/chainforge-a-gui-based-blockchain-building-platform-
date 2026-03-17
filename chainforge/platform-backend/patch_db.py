
import sqlite3
import json
import os

db_path = r'c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\chainforge\platform-backend\chainforge.db'
if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)

# Patch ALL projects just to be safe, but specifically 18
project_ids = [18] # We can add more if needed

REGISTRY_CODE = """class CertificateRegistry:
    def __init__(self):
        pass

    def issue_certificate(self, caller: str, cert_id: str, student_name: str, degree: str, year: int, issuer_id: str, state: dict = None) -> dict:
        if state is None: return {'error': 'Execution environment did not provide global state'}
        cert_key = f'cert_{cert_id}'
        if cert_key in state: return {'error': 'Certificate ID already exists'}
        state[cert_key] = {
            'cert_id': cert_id,
            'student_name': student_name,
            'degree': degree,
            'year': year,
            'issuer_id': issuer_id,
            'is_revoked': False
        }
        return {'status': 'success', 'cert_id': cert_id}

    def revoke_certificate(self, caller: str, cert_id: str, requester_id: str, state: dict = None) -> dict:
        if state is None: return {'error': 'Execution environment did not provide global state'}
        cert_key = f'cert_{cert_id}'
        if cert_key not in state: return {'error': 'Certificate not found'}
        cert = state[cert_key]
        if cert['issuer_id'] != requester_id:
            return {'error': 'Unauthorized: Only the original issuer can revoke this certificate'}
        if cert['is_revoked']: return {'error': 'Certificate is already revoked'}
        cert['is_revoked'] = True
        return {'status': 'success', 'message': 'Certificate revoked'}

    def verify_certificate(self, caller: str, cert_id: str, state: dict = None) -> dict:
        if state is None: return {'error': 'Execution environment did not provide global state'}
        cert_key = f'cert_{cert_id}'
        if cert_key not in state: return {'status': 'not_found', 'is_valid': False}
        cert = state[cert_key]
        if cert['is_revoked']: return {'status': 'revoked', 'is_valid': False}
        return {'status': 'valid', 'is_valid': True}

    def get_certificate(self, caller: str, cert_id: str, state: dict = None) -> dict:
        if state is None: return {'error': 'Execution environment did not provide global state'}
        cert_key = f'cert_{cert_id}'
        if cert_key not in state: return {'error': 'Certificate not found'}
        return {'status': 'success', 'data': state[cert_key]}
"""

AUTHORITY_CODE = """class CertificateAuthority:
    def __init__(self):
        pass

    def issueCert(self, cert_id, subject_data, state: dict = None):
        if state is None: return False
        if 'ca_certs' not in state: state['ca_certs'] = {}
        state['ca_certs'][cert_id] = subject_data
        return True

    def revokeCert(self, cert_id, state: dict = None):
        if state is None: return False
        if 'ca_revoked' not in state: state['ca_revoked'] = []
        if cert_id not in state['ca_revoked']:
            state['ca_revoked'].append(cert_id)
        return True

    def verifyCert(self, cert_id, state: dict = None):
        if state is None: return False
        certs = state.get('ca_certs', {})
        revoked = state.get('ca_revoked', [])
        return cert_id in certs and cert_id not in revoked
"""

for pid in project_ids:
    cfg_row = conn.execute('SELECT config FROM projects WHERE id=?', (pid,)).fetchone()
    if not cfg_row: continue
    
    config = json.loads(cfg_row[0])
    updated = False
    
    for contract in config.get('smartContracts', []):
        name = contract.get('name', '').strip()
        if 'CertificateRegistry' in name:
            contract['code'] = REGISTRY_CODE
            updated = True
            print(f"Updated CertificateRegistry in project {pid}")
        elif 'CertificateAuthority' in name:
            contract['code'] = AUTHORITY_CODE
            updated = True
            print(f"Updated CertificateAuthority in project {pid}")
            
    if updated:
        new_cfg_str = json.dumps(config)
        conn.execute('UPDATE projects SET config=? WHERE id=?', (new_cfg_str, pid))
        conn.commit()
        print(f"Project {pid} updated in database.")

conn.close()
