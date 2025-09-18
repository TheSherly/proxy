import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

API_BASE_URL = "https://score.hsborges.dev/api"

@app.get("/proxy_scores")
async def proxy_scores(cpf: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/score",
                params={"cpf": cpf},
                headers={"accept": "application/json", "client-id": "julio"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
