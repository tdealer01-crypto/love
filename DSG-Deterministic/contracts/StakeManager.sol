// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract StakeManager {

    struct Stake {
        uint256 amount;
        uint256 unlockTime;
    }

    mapping(address => Stake) public stakes;
    uint256 public constant LOCK_PERIOD = 30 days;

    function stake() external payable {
        require(msg.value > 0, "No stake");
        stakes[msg.sender] = Stake(msg.value, block.timestamp + LOCK_PERIOD);
    }

    function withdraw() external {
        require(block.timestamp >= stakes[msg.sender].unlockTime, "Locked");
        uint256 amount = stakes[msg.sender].amount;
        stakes[msg.sender].amount = 0;
        payable(msg.sender).transfer(amount);
    }
}
