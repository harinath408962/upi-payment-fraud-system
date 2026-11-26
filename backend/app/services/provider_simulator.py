
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

    provider_reference = f"RZP_SIM_{uuid4().hex[:12].upper()}"

    responses = {
        "SUCCESS": {
            "status": "SUCCESS",
            "message": "Payment completed successfully"
        },
        "FAILED": {
            "status": "FAILED",
            "message": "Payment failed at simulated provider"
        },
        "TIMEOUT": {
            "status": "TIMEOUT",
            "message": "Provider response timed out"
        },
        "PENDING": {
            "status": "PENDING",
            "message": "Payment is awaiting provider confirmation"
        }
    }

    return {
        "provider": "RAZORPAY_SIMULATOR",
        "provider_reference": provider_reference,
        "outcome": outcome,
        "message": responses[outcome]["message"],
        "simulated_at": datetime.now(timezone.utc).isoformat()
    }
