import argparse
import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from eth_account import Account
from web3 import Web3


MINIMAL_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "responseHash", "type": "bytes32"},
            {"internalType": "bool", "name": "passed", "type": "bool"},
            {"internalType": "string", "name": "details", "type": "string"},
        ],
        "name": "recordValidation",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isAuditor",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "minStakeToBeAuditor",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class CheckResult:
    passed: bool
    issues: List[str]


def _find_basic_equations(text: str) -> List[Tuple[int, int, int, str]]:
    """Find equations like '2 + 2 = 5' or '10-3=7'. Returns (a, b, c, op)."""
    pattern = re.compile(r"(?<!\d)(-?\d+)\s*([+\-*/])\s*(-?\d+)\s*=\s*(-?\d+)(?!\d)")
    out = []
    for m in pattern.finditer(text):
        a = int(m.group(1))
        op = m.group(2)
        b = int(m.group(3))
        c = int(m.group(4))
        out.append((a, b, c, op))
    return out


def _eval_equation(a: int, b: int, op: str) -> int | None:
    try:
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                return None
            if a % b != 0:
                return None
            return a // b
        return None
    except Exception:
        return None


def check_logical_consistency(text: str) -> CheckResult:
    issues: List[str] = []

    # Check arithmetic equalities written inline.
    for a, b, c, op in _find_basic_equations(text):
        expected = _eval_equation(a, b, op)
        if expected is None:
            issues.append(f"Equation '{a} {op} {b} = {c}' is not safely evaluable (division by zero or non-integer division).")
        elif expected != c:
            issues.append(f"Arithmetic mismatch: '{a} {op} {b} = {c}' (expected {expected}).")

    # Basic contradiction heuristics.
    lowered = text.lower()
    if "always" in lowered and "never" in lowered:
        issues.append("Contains both 'always' and 'never' which often signals overconfident universal claims.")

    if re.search(r"\btrue\b", lowered) and re.search(r"\bfalse\b", lowered) and "both" in lowered:
        issues.append("Contains 'true' and 'false' with 'both' which may indicate a direct contradiction.")

    # Detect mutually exclusive claims like: "X is greater than Y" and "Y is greater than X" for same pair.
    gt_pattern = re.compile(r"\b([a-zA-Z]{1,32})\s+is\s+greater\s+than\s+([a-zA-Z]{1,32})\b", re.IGNORECASE)
    gt_pairs = set()
    for m in gt_pattern.finditer(text):
        left = m.group(1).lower()
        right = m.group(2).lower()
        gt_pairs.add((left, right))

    for (a, b) in list(gt_pairs):
        if (b, a) in gt_pairs:
            issues.append(f"Contradictory ordering detected: '{a} > {b}' and '{b} > {a}'.")
            break

    return CheckResult(passed=(len(issues) == 0), issues=issues)


def keccak_text(w3: Web3, text: str) -> bytes:
    # Must match Solidity bytes32 expectations
    return w3.keccak(text=text)


def submit_validation(
    w3: Web3,
    contract_address: str,
    private_key: str,
    response_hash: bytes,
    passed: bool,
    details: str,
) -> str:
    acct = Account.from_key(private_key)
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=MINIMAL_ABI)

    # Optional pre-check for operator UX
    try:
        is_auditor = contract.functions.isAuditor(acct.address).call()
        if not is_auditor:
            min_stake = contract.functions.minStakeToBeAuditor().call()
            raise RuntimeError(
                f"Sender {acct.address} is not an auditor (stake below minStakeToBeAuditor={min_stake})."
            )
    except ValueError:
        # If the chain/node can't execute call, proceed to tx attempt.
        pass

    nonce = w3.eth.get_transaction_count(acct.address)
    tx = contract.functions.recordValidation(response_hash, passed, details).build_transaction(
        {
            "from": acct.address,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }
    )

    # EIP-1559 if supported
    try:
        latest = w3.eth.get_block("latest")
        if "baseFeePerGas" in latest:
            tx["maxPriorityFeePerGas"] = w3.to_wei(1, "gwei")
            tx["maxFeePerGas"] = tx["maxPriorityFeePerGas"] + int(latest["baseFeePerGas"]) * 2
    except Exception:
        pass

    if "gas" not in tx:
        tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()


def main() -> int:
    p = argparse.ArgumentParser(description="BotKiller Fiscal simulator: basic logical checks + on-chain validation record")
    p.add_argument("--rpc", default=os.environ.get("BOTKILLER_RPC_URL"), help="RPC URL (or BOTKILLER_RPC_URL)")
    p.add_argument(
        "--contract",
        default=os.environ.get("BOTKILLER_TOKEN_ADDRESS"),
        help="Deployed BotKillerToken contract address (or BOTKILLER_TOKEN_ADDRESS)",
    )
    p.add_argument(
        "--private-key",
        default=os.environ.get("BOTKILLER_PRIVATE_KEY"),
        help="Sender private key (or BOTKILLER_PRIVATE_KEY). Keep this secret.",
    )
    p.add_argument("--text", default=None, help="AI response text to validate")
    p.add_argument("--text-file", default=None, help="Path to a file containing the AI response")
    p.add_argument("--dry-run", action="store_true", help="Only run checks; do not submit on-chain")

    args = p.parse_args()

    if args.text is None and args.text_file is None:
        raise SystemExit("Provide --text or --text-file")

    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text or ""

    result = check_logical_consistency(text)

    issues_block = "\n".join(f"- {i}" for i in result.issues) if result.issues else "- (no issues detected)"
    details = f"passed={result.passed}\nissues:\n{issues_block}"

    if args.dry_run:
        print(details)
        return 0

    if not args.rpc or not args.contract or not args.private_key:
        raise SystemExit("Missing --rpc/--contract/--private-key (or env vars BOTKILLER_RPC_URL, BOTKILLER_TOKEN_ADDRESS, BOTKILLER_PRIVATE_KEY)")

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    if not w3.is_connected():
        raise SystemExit("Could not connect to RPC")

    response_hash = keccak_text(w3, text)
    tx_hash = submit_validation(w3, args.contract, args.private_key, response_hash, result.passed, details)

    print("Validation submitted")
    print(f"passed: {result.passed}")
    print(f"responseHash: 0x{response_hash.hex()}")
    print(f"tx: {tx_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
