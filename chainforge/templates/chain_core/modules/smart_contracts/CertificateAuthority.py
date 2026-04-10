class CertificateAuthority:
    def __init__(self):
        pass

    def issueCert(self, caller=None, state=None, cert_id=None, subject_data=None, **kwargs):
        if state is None: return False
        certs = state.setdefault("system.certs.issued", {})
        certs[cert_id] = subject_data
        return True

    def revokeCert(self, caller=None, state=None, cert_id=None, **kwargs):
        if state is None: return False
        revoked = state.setdefault("system.certs.revoked", [])
        if cert_id not in revoked:
            revoked.append(cert_id)
        return True

    def verifyCert(self, caller=None, state=None, cert_id=None, **kwargs):
        if state is None: return False
        certs = state.get("system.certs.issued", {})
        revoked = state.get("system.certs.revoked", [])
        return cert_id in certs and cert_id not in revoked

