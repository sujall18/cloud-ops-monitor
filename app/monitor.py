
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from prometheus_client import Gauge, start_http_server

URLS = [
    "https://example.com", 
    "https://httpbin.org/status/503",
    "http://localhost:4566/",
    "https://google.com"
]

CHECK_INTERVAL = 30

availability = Gauge(
    "health_monitor_up",
    "1 if the endpoint is healthy, otherwise 0",
    ["target"],
)

latency = Gauge(
    "health_monitor_latency_seconds",
    "Time taken for the HTTP check",
    ["target"],
)

http_status = Gauge(
    "health_monitor_http_status",
    "HTTP response status code, or 0 if unavailable",
    ["target"],
)


def check_url(url):
    start = time.perf_counter()
    status = 0

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CloudHealthMonitor/1.0"},
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            status = response.status

    except urllib.error.HTTPError as error:
        status = error.code

    except Exception as error:
        elapsed = time.perf_counter() - start
        return False, 0, elapsed, str(error)

    elapsed = time.perf_counter() - start
    return 200 <= status < 400, status, elapsed, None


def main():
    start_http_server(8000, addr="0.0.0.0")
    print("Metrics available at http://localhost:8000/metrics")

    while True:
        for url in URLS:
            healthy, status, elapsed, error = check_url(url)

            availability.labels(target=url).set(int(healthy))
            latency.labels(target=url).set(elapsed)
            http_status.labels(target=url).set(status)

            state = "UP" if healthy else "DOWN"
            print(
                f"{datetime.now(timezone.utc).isoformat()} "
                f"| {state} | {url} | HTTP {status} "
                f"| {elapsed * 1000:.2f}ms"
                + (f" | {error}" if error else ""),
                flush=True,
            )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
