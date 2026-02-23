require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();
const path = require("path");

module.exports = {
  solidity: "0.8.20",
  paths: {
    root: path.join(__dirname, "."),
    sources: path.join(__dirname, "contracts"),
    artifacts: path.join(__dirname, "artifacts"),
    cache: path.join(__dirname, "cache"),
    tests: path.join(__dirname, "test"),
  },
  networks: {
    base: {
      url: process.env.BASE_RPC,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    }
  }
};
