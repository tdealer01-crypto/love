#!/bin/bash
set -e

REPO="DSG-Deterministic"
rm -rf $REPO
mkdir -p $REPO/{contracts,deploy,terraform}
cd $REPO

########################
# package.json
########################
cat > package.json <<PKG
{
  "name": "dsg-agent-wallet-node",
  "version": "1.0.0",
  "license": "MIT",
  "devDependencies": {
    "hardhat": "^2.19.0",
    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
    "@openzeppelin/contracts": "^5.0.0",
    "dotenv": "^16.0.0"
  }
}
PKG

########################
# hardhat.config.js
########################
cat > hardhat.config.js <<HH
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.20",
  networks: {
    base: {
      url: process.env.BASE_RPC,
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
HH

########################
# .env example
########################
cat > .env.example <<ENV
BASE_RPC=https://mainnet.base.org
PRIVATE_KEY=YOUR_PRIVATE_KEY
ENV

########################
# README
########################
cat > README.md <<README
# DSG Agent Wallet Node (Base Mainnet)

Full Web3 Production Version

Token Supply: 100,000,000 DSG  
Stake Lock: 30 Days  
Network: Base Mainnet  

## Research DOIs

- https://doi.org/10.5281/zenodo.18244246
- https://doi.org/10.5281/zenodo.18225586
- https://doi.org/10.5281/zenodo.18212854

## Deploy

npm install  
npx hardhat compile  
npx hardhat run deploy/deploy.js --network base
README

########################
# CONTRACTS
########################

cat > contracts/DSGCreditToken.sol <<TOKEN
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract DSGCreditToken is ERC20 {

    constructor() ERC20("DSG Credit Token", "DSG") {
        _mint(msg.sender, 100000000 * 10 ** decimals());
    }
}
TOKEN

cat > contracts/StakeManager.sol <<STAKE
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
STAKE

cat > contracts/HarmonicGate.sol <<GATE
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract HarmonicGate {

    enum Grade { HG0, HG1, HG2, HG3, HG4 }

    function validate(Grade grade, uint256 stake) public pure returns (bool) {
        if (grade == Grade.HG0) return true;
        if (grade == Grade.HG1 && stake > 0) return true;
        if (grade == Grade.HG2 && stake >= 1 ether) return true;
        if (grade == Grade.HG3 && stake >= 5 ether) return true;
        if (grade == Grade.HG4 && stake >= 10 ether) return true;
        return false;
    }
}
GATE

cat > contracts/ReputationEngine.sol <<REP
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
REP

cat > contracts/DSGAgentWalletNode.sol <<CORE
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
CORE

########################
# DEPLOY SCRIPT
########################
cat > deploy/deploy.js <<DEPLOY
const hre = require("hardhat");

async function main() {
  const Token = await hre.ethers.getContractFactory("DSGCreditToken");
  const token = await Token.deploy();
  await token.waitForDeployment();

  const Stake = await hre.ethers.getContractFactory("StakeManager");
  const stake = await Stake.deploy();
  await stake.waitForDeployment();

  const Gate = await hre.ethers.getContractFactory("HarmonicGate");
  const gate = await Gate.deploy();
  await gate.waitForDeployment();

  const Rep = await hre.ethers.getContractFactory("ReputationEngine");
  const rep = await Rep.deploy();
  await rep.waitForDeployment();

  const Core = await hre.ethers.getContractFactory("DSGAgentWalletNode");
  const core = await Core.deploy(
    await stake.getAddress(),
    await gate.getAddress(),
    await rep.getAddress()
  );
  await core.waitForDeployment();

  console.log("DSG Token:", await token.getAddress());
  console.log("StakeManager:", await stake.getAddress());
  console.log("HarmonicGate:", await gate.getAddress());
  console.log("ReputationEngine:", await rep.getAddress());
  console.log("Core:", await core.getAddress());
}

main();
DEPLOY

########################
# TERRAFORM (optional backend infra)
########################
cat > terraform/main.tf <<TF
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}
TF

echo "✅ DSG Base Production Project Created"
EOF
