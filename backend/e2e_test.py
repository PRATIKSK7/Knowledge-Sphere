import os
import time
import asyncio
import httpx

API_BASE = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "test_e2e@example.com",
    "password": "password123",
    "full_name": "E2E Tester"
}

async def run_e2e():
    async with httpx.AsyncClient() as client:
        # 1. Register
        print("Registering user...")
        res = await client.post(f"{API_BASE}/auth/register", json=TEST_USER)
        if res.status_code not in (200, 201, 400):
            print("Register failed:", res.text)
            return
            
        # 2. Login
        print("Logging in...")
        res = await client.post(
            f"{API_BASE}/auth/login", 
            data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
        )
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create dummy BERT paper
        print("Creating dummy BERT pdf...")
        os.system("echo 'BERT is a bidirectional transformer model. It uses attention mechanisms to understand context.' > /tmp/bert.txt")
        
        # 4. Upload
        print("Uploading document...")
        with open("/tmp/bert.txt", "rb") as f:
            res = await client.post(
                f"{API_BASE}/documents/upload",
                headers=headers,
                files={"file": ("bert.txt", f, "text/plain")}
            )
        if res.status_code not in (200, 201, 202):
            print("Upload failed:", res.text)
            return
        doc_id = res.json()["id"]
        print(f"Uploaded successfully. Document ID: {doc_id}")
        
        # 5. Poll for status
        print("Waiting for ingestion to complete...")
        for _ in range(30):
            res = await client.get(f"{API_BASE}/documents/{doc_id}", headers=headers)
            status = res.json()["status"]
            print(f"Status: {status}")
            if status == "COMPLETED":
                break
            if status == "FAILED":
                print("Ingestion failed!", res.json())
                return
            await asyncio.sleep(2)
            
        # 6. Test Chat
        print("Testing Chat...")
        res = await client.post(
            f"{API_BASE}/search/chat",
            headers=headers,
            json={"query": "What is BERT?"}
        )
        print(f"Chat Response [{res.status_code}]:", res.text)

        # 7. Test Graph Data
        print("Testing Graph Data...")
        res = await client.get(f"{API_BASE}/graph/data", headers=headers)
        print(f"Graph Data [{res.status_code}]:", len(res.json().get("nodes", [])))

        # 8. Test Literature Review
        print("Testing Lit Review...")
        res = await client.post(
            f"{API_BASE}/graph/literature-review",
            headers=headers,
            json={"topic": "BERT and Transformers", "format": "APA"}
        )
        print(f"Lit Review [{res.status_code}]:", res.text[:200])

if __name__ == "__main__":
    asyncio.run(run_e2e())
