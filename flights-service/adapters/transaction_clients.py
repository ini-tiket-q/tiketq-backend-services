import httpx

TRANSACTION_SERVICE_URL = "http://transaction-service:8000/transactions/"

async def create_transaction(transaction_payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TRANSACTION_SERVICE_URL,
            json=transaction_payload,
            timeout=10
        )
        
        # Debugging logs
        print("🔁 [Transaction] POST", TRANSACTION_SERVICE_URL)
        print("📦 Payload:", transaction_payload)
        print("🔎 Status Code:", response.status_code)
        print("📄 Raw Response:", response.text)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Print error details to help debugging
            print("❌ HTTP Error:", e)
            print("❌ Response JSON:", response.json())
            raise

        return response.json()
