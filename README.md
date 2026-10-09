# ChainForecast

ChainForecast is a beginner-friendly AI and blockchain project for stock-market analysis. It finds historical price patterns similar to the latest market window using Dynamic Time Warping (DTW), estimates the following return, and can register a tamper-evident prediction hash on a local Ethereum blockchain.

The project runs without API keys. Demo mode uses generated price data; live mode uses public Yahoo Finance data through `yfinance`.

## Features

- DTW-based historical pattern matching
- Buy, Hold, or Sell signal with an explainable confidence score
- Chronological matching that avoids using future data
- Flask dashboard and JSON REST API
- SHA-256 prediction fingerprinting
- Solidity registry contract for immutable prediction records
- Local Hardhat blockchain with pre-funded development accounts

## Technology

- Python, Flask, NumPy, Pandas, yfinance
- Solidity, Hardhat, Ethers.js
- HTML and CSS

## Quick start (no blockchain)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
```

Open `http://127.0.0.1:5000`. The dashboard starts in demo mode and needs no key or external account.

To analyze a live ticker, turn off Demo mode in the form. Live data needs internet access but no API key.

## REST API

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","demo":true}'
```

Health check:

```bash
curl http://127.0.0.1:5000/api/health
```

## Optional local blockchain

The AI dashboard works without blockchain. To enable immutable prediction registration:

```bash
cd blockchain
npm install
npx hardhat node
```

In another terminal:

```bash
cd blockchain
npx hardhat run scripts/deploy.js --network localhost
```

Copy the printed contract address and configure the backend:

```bash
cp .env.example .env
```

Set `CONTRACT_ADDRESS` in `.env`, then restart the Flask app. The included private key is Hardhat's public development key and must never be used on a real network.

## Tests

```bash
python -m pytest
cd blockchain && npm test
```

## How the prediction works

1. Normalize the most recent 20 closing prices.
2. Compare that sequence with older 20-day windows using DTW.
3. Keep the five closest historical matches.
4. Measure what happened over the five days following each match.
5. Weight those outcomes by similarity and generate a Buy, Hold, or Sell signal.
6. Hash the prediction payload so the exact result can later be verified on-chain.

This is an educational project, not financial advice. Its output should not be used for real trading decisions.

