
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal


ProviderOutcome = Literal[
    "SUCCESS",
    "FAILED",
    "TIMEOUT",
    "PENDING"
]


def simulate_provider_response(
    outcome: ProviderOutcome
) -> dict:

    responses = {
        "SUCCESS": "Payment completed successfully",
        "FAILED": "Payment failed at simulated provider",
        "TIMEOUT": "Provider response timed out",
        "PENDING": "Payment is awaiting provider confirmation"
    }

    # A timeout means no provider acknowledgement was received.
    provider_reference = (
        None if outcome == "TIMEOUT"
        else f"RZP_SIM_{uuid4().hex[:12].upper()}"
    )

    return {
        "provider": "RAZORPAY_SIMULATOR",
        "provider_reference": provider_reference,
        "outcome": outcome,
        "message": responses[outcome],
        "simulated_at": datetime.now(timezone.utc).isoformat()
    }
