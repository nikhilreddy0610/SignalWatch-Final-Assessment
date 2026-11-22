"""Lab 10.1: bank transfers with multi-document transactions."""

import os
import random
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from bson.decimal128 import Decimal128
from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import PyMongoError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
MAX_ATTEMPTS = 5
BASE_RETRY_DELAY_SECONDS = 0.1


class InsufficientFundsError(ValueError):
    """Raised when an account cannot cover a transfer."""


class AccountNotFoundError(ValueError):
    """Raised when a transfer references an unknown account."""


def _money(value: Decimal | int | float | str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("amount must be a valid decimal number") from error
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be greater than zero")
    return amount


def seed_accounts(accounts) -> None:
    accounts.database["transactions"].drop()
    accounts.drop()
    accounts.insert_many(
        [
            {"account_id": "ACC-001", "holder": "Arjun", "balance": Decimal128("5000.00"), "version": 0},
            {"account_id": "ACC-002", "holder": "Sneha", "balance": Decimal128("3000.00"), "version": 0},
            {"account_id": "ACC-003", "holder": "Rahul", "balance": Decimal128("1000.00"), "version": 0},
        ]
    )


def transfer_funds(
    client: MongoClient,
    accounts,
    from_id: str,
    to_id: str,
    amount: Decimal | int | float | str,
    description: str,
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_delay_seconds: float = BASE_RETRY_DELAY_SECONDS,
) -> None:
    """Transfer funds atomically; retry only transient transaction failures."""
    value = _money(amount)
    if from_id == to_id:
        raise ValueError("source and destination accounts must be different")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")

    transactions = accounts.database["transactions"]
    for attempt in range(max_attempts):
        try:
            with client.start_session() as session:
                with session.start_transaction(
                    read_concern=ReadConcern("snapshot"),
                    write_concern=WriteConcern("majority"),
                ):
                    if accounts.find_one({"account_id": from_id}, session=session) is None:
                        raise AccountNotFoundError(f"source account {from_id} does not exist")

                    debit = accounts.update_one(
                        {"account_id": from_id, "balance": {"$gte": Decimal128(value)}},
                        {"$inc": {"balance": Decimal128(-value), "version": 1}},
                        session=session,
                    )
                    if debit.matched_count != 1:
                        raise InsufficientFundsError(
                            f"insufficient funds in {from_id} (required {value})"
                        )

                    credit = accounts.update_one(
                        {"account_id": to_id},
                        {"$inc": {"balance": Decimal128(value), "version": 1}},
                        session=session,
                    )
                    if credit.matched_count != 1:
                        raise AccountNotFoundError(f"destination account {to_id} does not exist")

                    transactions.insert_one(
                        {
                            "from": from_id,
                            "to": to_id,
                            "amount": Decimal128(value),
                            "description": description,
                            "timestamp": datetime.now(timezone.utc),
                        },
                        session=session,
                    )
            return
        except PyMongoError as error:
            if not error.has_error_label("TransientTransactionError"):
                raise
            if attempt + 1 == max_attempts:
                raise
            delay = base_delay_seconds * (2**attempt) * random.uniform(0.5, 1.5)
            print(f"  Transient transaction error; retrying in {delay:.2f}s")
            time.sleep(delay)


def _balance(accounts, account_id: str) -> Decimal:
    account = accounts.find_one({"account_id": account_id})
    if account is None:
        raise AccountNotFoundError(f"account {account_id} does not exist")
    return account["balance"].to_decimal()


def run_demo(client: MongoClient) -> None:
    accounts = client["bank"]["accounts"]
    seed_accounts(accounts)
    print("\n=== Lab 10.1: Bank transfer transaction ===")
    print("Initial balances:")
    for account in accounts.find({}, sort=[("account_id", 1)]):
        print(f"  {account['account_id']}: ${account['balance'].to_decimal():,.2f}")

    transfer_funds(client, accounts, "ACC-001", "ACC-002", "1500.00", "Lab transfer")
    print("  Successful transfer: ACC-001 -> ACC-002 ($1,500.00)")

    before = (_balance(accounts, "ACC-001"), _balance(accounts, "ACC-003"))
    try:
        transfer_funds(client, accounts, "ACC-003", "ACC-001", "5000.00", "Insufficient-funds test")
    except InsufficientFundsError as error:
        print(f"  Expected failure: {error}")
    else:
        raise AssertionError("insufficient-funds transfer unexpectedly succeeded")

    after = (_balance(accounts, "ACC-001"), _balance(accounts, "ACC-003"))
    if before != after:
        raise AssertionError("failed transfer changed an account balance; rollback failed")
    if accounts.database["transactions"].count_documents({}) != 1:
        raise AssertionError("failed transfer unexpectedly wrote transaction history")

    print("  Rollback verified: neither account balance changed.")
    print("Final balances:")
    for account in accounts.find({}, sort=[("account_id", 1)]):
        print(f"  {account['account_id']}: ${account['balance'].to_decimal():,.2f}")


if __name__ == "__main__":
    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=10_000) as mongo_client:
        run_demo(mongo_client)
