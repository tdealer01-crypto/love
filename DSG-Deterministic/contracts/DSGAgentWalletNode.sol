// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./StakeManager.sol";
import "./HarmonicGate.sol";
import "./ReputationEngine.sol";

contract DSGAgentWalletNode {

    StakeManager public stakeManager;
    HarmonicGate public gate;
    ReputationEngine public reputation;

    constructor(address _stake, address _gate, address _rep) {
        stakeManager = StakeManager(_stake);
        gate = HarmonicGate(_gate);
        reputation = ReputationEngine(_rep);
    }

    function execute(HarmonicGate.Grade grade) external {
        (uint256 amount,) = stakeManager.stakes(msg.sender);
        require(gate.validate(grade, amount), "Invalid grade");
        reputation.success(msg.sender);
    }
}
