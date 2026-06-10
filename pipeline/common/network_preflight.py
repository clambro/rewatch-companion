"""Network preflight checks for web-dependent pipeline runs."""

import http.client
import json
from dataclasses import asdict, dataclass
from pathlib import Path

TRACE_HOST = "www.cloudflare.com"
TRACE_PATH = "/cdn-cgi/trace"
BASELINE_PATH = Path(__file__).resolve().parents[2] / ".local" / "network-baseline.json"
TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class NetworkIdentity:
    """Public network identity returned by the preflight endpoint."""

    ip: str
    loc: str
    colo: str


def write_network_baseline() -> NetworkIdentity:
    """Record the current public network identity as the local no-VPN baseline."""
    identity = current_network_identity()
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(asdict(identity), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return identity


def assert_network_baseline() -> NetworkIdentity:
    """Ensure the current public IP matches the saved no-VPN baseline."""
    if not BASELINE_PATH.exists():
        raise RuntimeError(
            "Network baseline is missing. Turn the VPN off and run "
            "`uv run poe rw -- network baseline` from pipeline/ before generating essays "
            "or images.",
        )

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current = current_network_identity()
    if current.ip != baseline["ip"]:
        raise RuntimeError(
            "Network preflight failed: current public IP does not match the saved no-VPN "
            f"baseline. Baseline IP: {baseline['ip']} ({baseline.get('loc', 'unknown')}). "
            f"Current IP: {current.ip} ({current.loc}). Turn off the VPN or rerun "
            "`uv run poe rw -- network baseline` if your normal connection changed.",
        )

    return current


def current_network_identity() -> NetworkIdentity:
    """Fetch the current public network identity."""
    connection = http.client.HTTPSConnection(TRACE_HOST, timeout=TIMEOUT_SECONDS)
    try:
        connection.request(
            "GET",
            TRACE_PATH,
            headers={"User-Agent": "rewatch-pipeline-network-preflight"},
        )
        response = connection.getresponse()
        trace = response.read().decode("utf-8")
    except OSError as error:
        raise RuntimeError(
            f"Network preflight failed while fetching https://{TRACE_HOST}{TRACE_PATH}: {error}",
        ) from error
    finally:
        connection.close()

    if response.status != http.HTTPStatus.OK:
        raise RuntimeError(
            "Network preflight failed while fetching "
            f"https://{TRACE_HOST}{TRACE_PATH}: HTTP {response.status}.",
        )

    fields = dict(line.split("=", 1) for line in trace.splitlines() if "=" in line)
    if not fields.get("ip"):
        raise RuntimeError(
            "Network preflight failed: "
            f"https://{TRACE_HOST}{TRACE_PATH} did not return a public IP.",
        )

    return NetworkIdentity(
        ip=fields["ip"],
        loc=fields.get("loc", "unknown"),
        colo=fields.get("colo", "unknown"),
    )
