class MultiSig:
    def __init__(self):
        pass

    def propose(self, caller=None, state=None, proposal_id=None, action_payload=None, required_sigs=None, **kwargs):
        if state is None: return False
        proposals = state.setdefault("system.multisig.proposals", {})
        if proposal_id not in proposals:
            proposals[proposal_id] = {
                "payload": action_payload,
                "required": required_sigs,
                "signatures": [],
                "executed": False
            }
        return True

    def approve(self, caller=None, state=None, proposal_id=None, address_sig=None, **kwargs):
        if state is None: return False
        proposals = state.setdefault("system.multisig.proposals", {})
        if proposal_id in proposals:
            prop = proposals[proposal_id]
            if address_sig not in prop["signatures"]:
                prop["signatures"].append(address_sig)
        return True

    def execute(self, caller=None, state=None, proposal_id=None, **kwargs):
        if state is None: return False
        proposals = state.setdefault("system.multisig.proposals", {})
        prop = proposals.get(proposal_id)
        if prop and len(prop["signatures"]) >= prop["required"] and not prop["executed"]:
            prop["executed"] = True
            return True
        return {"error": "Not ready for execution"}

