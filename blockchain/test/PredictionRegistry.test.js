const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("PredictionRegistry", function () {
  it("records and retrieves a prediction fingerprint", async function () {
    const Registry = await ethers.getContractFactory("PredictionRegistry");
    const registry = await Registry.deploy();
    const hash = ethers.sha256(ethers.toUtf8Bytes("example prediction"));

    await expect(registry.recordPrediction("AAPL", "BUY", hash))
      .to.emit(registry, "PredictionRecorded")
      .withArgs(0, (await ethers.getSigners())[0].address, "AAPL", "BUY", hash, anyValue);

    const record = await registry.getPrediction(0);
    expect(record.ticker).to.equal("AAPL");
    expect(record.signal).to.equal("BUY");
    expect(record.predictionHash).to.equal(hash);
    expect(await registry.predictionCount()).to.equal(1);
  });

  it("rejects an empty hash", async function () {
    const Registry = await ethers.getContractFactory("PredictionRegistry");
    const registry = await Registry.deploy();
    await expect(
      registry.recordPrediction("AAPL", "BUY", ethers.ZeroHash)
    ).to.be.revertedWith("Hash is required");
  });
});
