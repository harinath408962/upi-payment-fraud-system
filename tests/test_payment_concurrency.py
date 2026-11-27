
import concurrent.futures
import threading
import uuid

import requests


API_URL = "http://127.0.0.1:8000/payments/"
REQUEST_COUNT = 10
TIMEOUT = 30


def send_payment_request(barrier, idempotency_key, amount):
    payload = {
        "merchant_id": 1,
        "customer_id": 1,
        "payment_method_id": 1,
        "amount": amount,
        "currency": "INR"
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }

    try:
        barrier.wait(timeout=TIMEOUT)

        response = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT
        )

        try:
            body = response.json()
        except ValueError:
            body = {"raw_response": response.text}

        return {
            "amount": amount,
            "status_code": response.status_code,
            "body": body
        }

    except Exception as error:
        return {
            "amount": amount,
            "status_code": None,
            "error": str(error)
        }


def run_concurrent_requests(amounts, idempotency_key):
    barrier = threading.Barrier(len(amounts))

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(amounts)
    ) as executor:

        futures = [
            executor.submit(
                send_payment_request,
                barrier,
                idempotency_key,
                amount
            )
            for amount in amounts
        ]

        return [
            future.result()
            for future in concurrent.futures.as_completed(futures)
        ]


def test_identical_concurrent_requests():
    print("\n========== TEST 1: IDENTICAL REQUESTS ==========")

    idempotency_key = f"identical-test-{uuid.uuid4().hex}"

    amounts = [2500] * REQUEST_COUNT

    results = run_concurrent_requests(
        amounts,
        idempotency_key
    )

    for result in results:
        print(result)

    successful = [
        result for result in results
        if result["status_code"] == 201
    ]

    transaction_ids = {
        result["body"].get("transaction_id")
        for result in successful
    }

    all_success = (
        len(results) == REQUEST_COUNT
        and all(result["status_code"] == 201 for result in results)
        and len(transaction_ids) == 1
        and None not in transaction_ids
    )

    print("\nIdentical request summary:")
    print(f"Total requests: {len(results)}")
    print(f"Successful responses: {len(successful)}")
    print(f"Unique transaction IDs: {transaction_ids}")

    if all_success:
        print("RESULT: PASS")
        print("All identical requests reused one payment.")
    else:
        print("RESULT: FAIL")
        print("Identical request concurrency test failed.")

    return all_success


def test_conflicting_concurrent_requests():
    print("\n========== TEST 2: CONFLICTING REQUESTS ==========")

    idempotency_key = f"conflict-test-{uuid.uuid4().hex}"

    amounts = [
        2000 if index % 2 == 0 else 3000
        for index in range(REQUEST_COUNT)
    ]

    results = run_concurrent_requests(
        amounts,
        idempotency_key
    )

    for result in results:
        print(result)

    successful = [
        result for result in results
        if result["status_code"] == 201
    ]

    conflicts = [
        result for result in results
        if result["status_code"] == 409
    ]

    transaction_ids = {
        result["body"].get("transaction_id")
        for result in successful
    }

    created_amounts = {
        str(result["body"].get("amount"))
        for result in successful
    }

    all_pass = (
        len(results) == REQUEST_COUNT
        and len(successful) == 5
        and len(conflicts) == 5
        and len(transaction_ids) == 1
        and None not in transaction_ids
        and len(created_amounts) == 1
        and all(
            result["status_code"] in {201, 409}
            for result in results
        )
    )

    print("\nConflicting request summary:")
    print(f"Total requests: {len(results)}")
    print(f"Created responses: {len(successful)}")
    print(f"Conflict responses: {len(conflicts)}")
    print(f"Unique transaction IDs: {transaction_ids}")
    print(f"Created amount(s): {created_amounts}")

    if all_pass:
        print("RESULT: PASS")
        print("One request payload won; conflicting payloads were rejected.")
    else:
        print("RESULT: FAIL")
        print("Conflicting request concurrency test failed.")

    return all_pass


if __name__ == "__main__":
    print("PAYMENT IDEMPOTENCY AND CONCURRENCY TESTS")
    print(f"Requests per scenario: {REQUEST_COUNT}")

    identical_pass = test_identical_concurrent_requests()
    conflicting_pass = test_conflicting_concurrent_requests()

    print("\n========== FINAL TEST RESULT ==========")

    if identical_pass and conflicting_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        raise SystemExit(1)
