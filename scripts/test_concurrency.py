import getpass
import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"
NUMBER_OF_REQUESTS = 10


def login(username: str, password: str) -> str:
    login_data = urlencode(
        {
            "username": username,
            "password": password,
        }
    ).encode()

    request = Request(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode())

    return body["access_token"]


def send_order(
    token: str,
    address_id: str,
    product_id: str,
    barrier: threading.Barrier,
):
    body = json.dumps(
        {
            "address_id": address_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        }
    ).encode()

    request = Request(
        f"{BASE_URL}/orders",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    # All worker threads wait here and start together.
    barrier.wait()

    try:
        with urlopen(request, timeout=30) as response:
            response_body = json.loads(
                response.read().decode()
            )
            return response.status, response_body

    except HTTPError as error:
        error_body = json.loads(
            error.read().decode()
        )
        return error.code, error_body


def get_product(product_id: str):
    request = Request(
        f"{BASE_URL}/products/{product_id}",
        method="GET",
    )

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def main():
    username = input("Customer username: ")
    password = getpass.getpass("Customer password: ")
    address_id = input("Customer address ID: ")
    product_id = input("Concurrency Product ID: ")

    token = login(username, password)
    barrier = threading.Barrier(NUMBER_OF_REQUESTS)

    with ThreadPoolExecutor(
        max_workers=NUMBER_OF_REQUESTS
    ) as executor:
        futures = [
            executor.submit(
                send_order,
                token,
                address_id,
                product_id,
                barrier,
            )
            for _ in range(NUMBER_OF_REQUESTS)
        ]

        results = [
            future.result()
            for future in futures
        ]

    status_counts = Counter(
        status_code
        for status_code, _ in results
    )

    print("\nResponse counts:")
    print(dict(status_counts))

    for index, (status_code, body) in enumerate(
        results,
        start=1,
    ):
        print(
            f"Request {index}: "
            f"status={status_code}, body={body}"
        )

    product = get_product(product_id)

    print("\nFinal stock:")
    print(product["stock_quantity"])

    passed = (
        status_counts[201] == 1
        and status_counts[409] == NUMBER_OF_REQUESTS - 1
        and product["stock_quantity"] == 0
    )

    if passed:
        print("\nPASSED: no overselling occurred.")
    else:
        print("\nFAILED: concurrency result is incorrect.")


if __name__ == "__main__":
    main()