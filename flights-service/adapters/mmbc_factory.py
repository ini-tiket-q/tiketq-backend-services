import os
from adapters.external_api import MMBCClient
from adapters.fake_mmbc import FakeMMBCClient

def get_mmbc_client():
    # Prefer explicit toggle. If MOCK_REMOTE=true -> fake.
    if os.getenv("MOCK_REMOTE", "false").lower() == "true":
        return FakeMMBCClient()
    # Fallback: if base URL missing in development, also use fake
    if os.getenv("ENV", "development") == "development" and not os.getenv("MMBC_BASE_URL"):
        return FakeMMBCClient()
    return MMBCClient(
        base_url=os.getenv("MMBC_BASE_URL"),
        user=os.getenv("MMBC_USER_ID"),
        password=os.getenv("MMBC_PASSWORD"),
        agent=os.getenv("MMBC_AGENT_CODE"),
        timeout=float(os.getenv("MMBC_TIMEOUT_SECONDS", "15")),
    )

mmbc = get_mmbc_client()