"""Optional Web3 client for the local PredictionRegistry contract."""

from __future__ import annotations

import json
import os
from pathlib import Path


def register_prediction(ticker: str, signal: str, prediction_hash: str) -> str | None:
    if os.getenv("BLOCKCHAIN_ENABLED", "false").lower() != "true":
        return None

    from web3 import Web3

    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    contract_address = os.getenv("CONTRACT_ADDRESS", "")
    private_key = os.getenv("WALLET_PRIVATE_KEY", "")
    if not contract_address or not private_key:
        raise RuntimeError("CONTRACT_ADDRESS and WALLET_PRIVATE_KEY are required")

    artifact_path = (
        Path(__file__).resolve().parents[1]
        / "blockchain/artifacts/contracts/PredictionRegistry.sol/PredictionRegistry.json"
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"Cannot connect to blockchain at {rpc_url}")

    account = web3.eth.account.from_key(private_key)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(contract_address), abi=artifact["abi"]
    )
    hash_bytes = bytes.fromhex(prediction_hash)
    transaction = contract.functions.recordPrediction(
        ticker.upper(), signal, hash_bytes
    ).build_transaction(
        {
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address),
            "chainId": web3.eth.chain_id,
            "gas": 300_000,
            "gasPrice": web3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()

