import os
from adapters.external_api_bookings import MMBCClient
from adapters.fake_mmbc_bookings import FakeMMBCClient

MOCK_REMOTE = os.getenv("MOCK_REMOTE", "true").lower() == "true"

def build_mmbc():
    if MOCK_REMOTE:
        print("🧪 MOCK MODE: True")
        return FakeMMBCClient()
    else:
        print("🧪 MOCK MODE: False")
        return MMBCClient(
            base_url=os.getenv("MMBC_BASE_URL"),
            username=os.getenv("MMBC_USERNAME"),   # ✅ NEW
            user=os.getenv("MMBC_USER_ID"),
            password=os.getenv("MMBC_PASSWORD"),
            agent=os.getenv("MMBC_AGENT_CODE"),
            timeout=float(os.getenv("MMBC_TIMEOUT_SECONDS", "15")),
        )

mmbc = build_mmbc()
