class Governance:
    def propose(self, proposal_id, description):
        proposals_data = self.ctx.state.get('proposals', {})

        if proposals_data.get(proposal_id, {}).get('exists', False):
            raise Exception("Proposal already exists")

        proposals_data[proposal_id] = {
            'description': description,
            'voteCount': 0,
            'exists': True
        }

        self.ctx.state['proposals'] = proposals_data

    def vote(self, proposal_id):
        proposals_data = self.ctx.state.get('proposals', {})

        if not proposals_data.get(proposal_id, {}).get('exists', False):
            raise Exception("Proposal does not exist")

        current_proposal = proposals_data[proposal_id]
        current_proposal['voteCount'] += 1
        
        # Update the proposal in the proposals_data dictionary
        proposals_data[proposal_id] = current_proposal

        self.ctx.state['proposals'] = proposals_data

    def getProposal(self, proposal_id):
        proposals_data = self.ctx.state.get('proposals', {})

        if not proposals_data.get(proposal_id, {}).get('exists', False):
            raise Exception("Proposal does not exist")
        
        proposal = proposals_data[proposal_id]
        return proposal['description'], proposal['voteCount']