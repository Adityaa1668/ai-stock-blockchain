// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

contract PredictionRegistry {
    struct PredictionRecord {
        string ticker;
        string signal;
        bytes32 predictionHash;
        uint256 timestamp;
        address creator;
    }

    PredictionRecord[] private records;

    event PredictionRecorded(
        uint256 indexed recordId,
        address indexed creator,
        string ticker,
        string signal,
        bytes32 predictionHash,
        uint256 timestamp
    );

    function recordPrediction(
        string calldata ticker,
        string calldata signal,
        bytes32 predictionHash
    ) external returns (uint256 recordId) {
        require(bytes(ticker).length > 0, "Ticker is required");
        require(bytes(signal).length > 0, "Signal is required");
        require(predictionHash != bytes32(0), "Hash is required");

        recordId = records.length;
        records.push(
            PredictionRecord({
                ticker: ticker,
                signal: signal,
                predictionHash: predictionHash,
                timestamp: block.timestamp,
                creator: msg.sender
            })
        );

        emit PredictionRecorded(
            recordId,
            msg.sender,
            ticker,
            signal,
            predictionHash,
            block.timestamp
        );
    }

    function getPrediction(uint256 recordId) external view returns (PredictionRecord memory) {
        require(recordId < records.length, "Prediction does not exist");
        return records[recordId];
    }

    function predictionCount() external view returns (uint256) {
        return records.length;
    }
}

