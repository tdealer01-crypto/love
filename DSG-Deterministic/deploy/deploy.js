const hre = require("hardhat");

async function main() {
  const Token = await hre.ethers.getContractFactory("SecureWalletAgentToken");
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
