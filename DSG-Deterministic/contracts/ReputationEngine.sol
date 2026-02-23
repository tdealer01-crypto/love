// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ReputationEngine {

    struct Node {
        uint256 success;
        uint256 failure;
    }

    mapping(address => Node) public nodes;

    function success(address user) external {
        nodes[user].success++;
    }

    function reputation(address user) public view returns (uint256) {
        Node memory n = nodes[user];
        uint256 total = n.success + n.failure;
        if (total == 0) return 0;
        return (n.success * 100) / total;
    }
}
