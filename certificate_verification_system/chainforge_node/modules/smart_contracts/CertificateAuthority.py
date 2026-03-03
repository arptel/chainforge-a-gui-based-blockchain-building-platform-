class CertificateAuthority:
    def __init__(self):
        self.certs = {}
        self.revoked = []

    def issueCert(self, cert_id, subject_data):
        self.certs[cert_id] = subject_data
        return True

    def revokeCert(self, cert_id):
        if cert_id not in self.revoked:
            self.revoked.append(cert_id)
        return True

    def verifyCert(self, cert_id):
        return cert_id in self.certs and cert_id not in self.revoked
