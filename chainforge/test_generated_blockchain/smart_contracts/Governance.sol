// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Governance {
    struct Proposal {
        string description;
        uint256 voteCount;
        bool exists;
    }

    mapping(uint256 => Proposal) public proposals;

    function propose(uint256 proposalId, string memory description) public {
        require(!proposals[proposalId].exists, "Proposal already exists");
        proposals[proposalId] = Proposal(description, 0, true);
    }

    function vote(uint256 proposalId) public {
        require(proposals[proposalId].exists, "Proposal does not exist");
        proposals[proposalId].voteCount += 1;
    }

    function getProposal(uint256 proposalId) public view returns (string memory description, uint256 voteCount) {
        require(proposals[proposalId].exists, "Proposal does not exist");
        return (proposals[proposalId].description, proposals[proposalId].voteCount);
    }
}