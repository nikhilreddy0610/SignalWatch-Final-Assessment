"""Lab 10.2: concurrent inventory reservation with transaction retries."""

import os
import random
import time
from threading import Lock
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from decimal import Decimal

from bson.decimal128 import Decimal128
from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.errors import PyMongoError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
MAX_ATTEMPTS = 15
BASE_RETRY_DELAY_SECONDS = 0.01
MAX_RETRY_DELAY_SECONDS = 0.1
PRODUCT_ID = "LAPTOP"
UNIT_PRICE = Decimal("999.00")
_RETRY_LOG_LOCK = Lock()


class ProductNotFoundError(ValueError):
    """Raised when a reservation references an unknown product."""


class InvalidQuantityError(ValueError):
    """Raised when a reservation asks for a non-positive quantity."""


class InventoryVersionConflict(Exception):
    """Raised when an optimistic version check loses a concurrent race."""


@dataclass(frozen=True)
class ReservationResult:
    status: str
    order_id: str | None = None
    detail: str = ""


def seed_inventory(inventory, product_id: str, stock: int) -> None:
    inventory.delete_one({"product_id": product_id})
    inventory.insert_one(
        {
            "product_id": product_id,
            "name": "Laptop",
            "stock": stock,
            "version": 0,
        }
    )


def reserve_inventory(
    client: MongoClient,
    inventory,
    orders,
    product_id: str,
    customer_id: str,
    quantity: int,
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_delay_seconds: float = BASE_RETRY_DELAY_SECONDS,
) -> ReservationResult:
    """Reserve stock and create its order in one retried transaction."""
    if quantity <= 0:
        raise InvalidQuantityError("quantity must be greater than zero")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")

    order_id = str(uuid.uuid4())
    for attempt in range(max_attempts):
        try:
            with client.start_session() as session:
                with session.start_transaction(
                    read_concern=ReadConcern("snapshot"),
                    write_concern=WriteConcern("majority"),
                ):
                    product = inventory.find_one({"product_id": product_id}, session=session)
                    if product is None:
                        raise ProductNotFoundError(f"product {product_id} does not exist")
                    if product["stock"] < quantity:
                        return ReservationResult(
                            "INSUFFICIENT",
                            detail=f"only {product['stock']} unit(s) remain",
                        )

                    update = inventory.update_one(
                        {
                            "product_id": product_id,
                            "stock": {"$gte": quantity},
                            "version": product["version"],
                        },
                        {"$inc": {"stock": -quantity, "version": 1}},
                        session=session,
                    )
                    if update.matched_count != 1:
                        raise InventoryVersionConflict("inventory version changed during reservation")

                    orders.insert_one(
                        {
                            "order_id": order_id,
                            "customer_id": customer_id,
                            "items": [
                                {
                                    "product_id": product_id,
                                    "qty": quantity,
                                    "price": Decimal128(UNIT_PRICE),
                                }
                            ],
                            "status": "pending",
                            "total": Decimal128(UNIT_PRICE * quantity),
                        },
                        session=session,
                    )
            return ReservationResult("RESERVED", order_id=order_id)
        except InventoryVersionConflict as error:
            if attempt + 1 == max_attempts:
                return ReservationResult("CONFLICT", detail=str(error))
            with _RETRY_LOG_LOCK:
                print(
                    f"  Inventory version conflict; retrying attempt "
                    f"{attempt + 2}/{max_attempts}",
                    flush=True,
                )
        except PyMongoError as error:
            if not error.has_error_label("TransientTransactionError"):
                raise
            if attempt + 1 == max_attempts:
                return ReservationResult("CONFLICT", detail=str(error))
            with _RETRY_LOG_LOCK:
                print(
                    f"  Transient transaction error; retrying attempt "
                    f"{attempt + 2}/{max_attempts}",
                    flush=True,
                )

        delay = min(
            base_delay_seconds * (2**attempt),
            MAX_RETRY_DELAY_SECONDS,
        ) * random.uniform(0.5, 1.5)
        time.sleep(delay)

    raise AssertionError("reservation retry loop exited unexpectedly")


def run_contention_demo(client: MongoClient) -> None:
    db = client["inventory"]
    inventory = db["inventory"]
    orders = db["orders"]
    inventory.delete_many({})
    orders.delete_many({})
    seed_inventory(inventory, PRODUCT_ID, stock=5)

    print("\n=== Lab 10.2: Concurrent inventory reservations ===")
    print("Submitting 10 concurrent requests for 5 units...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                reserve_inventory,
                client,
                inventory,
                orders,
                PRODUCT_ID,
                f"customer-{index:02d}",
                1,
            )
            for index in range(10)
        ]
        results = [future.result() for future in as_completed(futures)]

    for result in results:
        suffix = f" ({result.detail})" if result.detail else ""
        print(f"  {result.status}{suffix}")

    reserved = sum(result.status == "RESERVED" for result in results)
    remaining = inventory.find_one({"product_id": PRODUCT_ID})["stock"]
    order_count = orders.count_documents({})
    print(f"  Successful reservations: {reserved}/10")
    print(f"  Remaining stock: {remaining} | Orders created: {order_count}")
    if reserved != 5 or remaining != 0 or order_count != 5:
        raise AssertionError(
            "contention invariant failed: expected 5 orders and zero remaining stock"
        )


def run_throughput_benchmark(client: MongoClient, request_count: int = 40) -> None:
    db = client["inventory"]
    inventory = db["inventory"]
    orders = db["orders"]
    print("\n=== Throughput benchmark (reservations/second) ===")
    print(f"Requests per concurrency level: {request_count}")
    for workers in (1, 4, 8, 16):
        product_id = f"BENCH-{workers}"
        seed_inventory(inventory, product_id, stock=request_count)
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    reserve_inventory,
                    client,
                    inventory,
                    orders,
                    product_id,
                    f"benchmark-{index:03d}",
                    1,
                )
                for index in range(request_count)
            ]
            results = [future.result() for future in as_completed(futures)]
        elapsed = time.perf_counter() - started
        successful = sum(result.status == "RESERVED" for result in results)
        throughput = successful / elapsed if elapsed else 0
        print(
            f"  workers={workers:2d}: {successful:2d}/{request_count} succeeded "
            f"in {elapsed:.2f}s ({throughput:.2f} reservations/s)"
        )
        if successful != request_count:
            raise AssertionError(
                f"benchmark at concurrency {workers} had failed reservations"
            )


def run_demo(client: MongoClient) -> None:
    run_contention_demo(client)
    run_throughput_benchmark(client)


if __name__ == "__main__":
    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=10_000) as mongo_client:
        run_demo(mongo_client)
