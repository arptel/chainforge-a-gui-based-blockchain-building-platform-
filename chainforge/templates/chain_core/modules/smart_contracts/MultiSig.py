class MultiSig:
    def __init__(self):
        self.proposals = {} # id -> proposal details

    def propose(self, proposal_id, action_payload, required_sigs):
        if proposal_id not in self.proposals:
            self.proposals[proposal_id] = {
                "payload": action_payload,
                "required": required_sigs,
                "signatures": [],
                "executed": False
            }
        return True

    def approve(self, proposal_id, address_sig):
        if proposal_id in self.proposals:
            prop = self.proposals[proposal_id]
            if address_sig not in prop["signatures"]:
                prop["signatures"].append(address_sig)
        return True

    def execute(self, proposal_id):
        prop = self.proposals.get(proposal_id)
        if prop and len(prop["signatures"]) >= prop["required"] and not prop["executed"]:
            prop["executed"] = True
            return True
        raise Exception("Not ready for execution")
