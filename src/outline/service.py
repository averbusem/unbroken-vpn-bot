import aiohttp

from src.config import settings


class OutlineManager:
    def __init__(self):
        self.api_url = settings.OUTLINE_API_URL
        self.cert_sha256 = settings.OUTLINE_CERT_SHA256
        self.headers = {"Content-Type": "application/json"}
        if self.cert_sha256:
            self.headers.update({"Outline-Cert-SHA256": self.cert_sha256})

    async def create_key(self, name: str = "") -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/access-keys", headers=self.headers
            ) as response:
                data = await response.json()
                return data

    async def delete_key(self, key_id: str):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/access-keys/{key_id}", headers=self.headers
            ) as response:
                return response.status == 204

    async def get_data_usage(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/metrics/transfer", headers=self.headers
            ) as response:
                return await response.json()
