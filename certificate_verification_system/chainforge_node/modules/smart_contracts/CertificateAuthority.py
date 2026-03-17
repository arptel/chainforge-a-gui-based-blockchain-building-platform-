class CertificateAuthority:
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
