import os
import time
import hashlib
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

API_KEY = os.environ["API_KEY"]
MAX_TIME_DRIFT = int(os.getenv("MAX_TIME_DRIFT", "30"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "10"))

RATE_LIMIT = {}


def verify_request(api_key: str, timestamp: str, signature: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=401)

    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=400)

    if abs(time.time() - ts) > MAX_TIME_DRIFT:
        raise HTTPException(status_code=401)

    expected = hashlib.sha256(f"{API_KEY}{timestamp}".encode()).hexdigest()
    if signature != expected:
        raise HTTPException(status_code=401)


def rate_limit(ip: str):
    now = time.time()
    hits = RATE_LIMIT.get(ip, [])
    hits = [t for t in hits if now - t < RATE_LIMIT_WINDOW]

    if len(hits) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429)

    hits.append(now)
    RATE_LIMIT[ip] = hits

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/payload")
async def payload(
    request: Request,
    x_api_key: str = Header(...),
    x_timestamp: str = Header(...),
    x_signature: str = Header(...)
):
    rate_limit(request.client.host)
    verify_request(x_api_key, x_timestamp, x_signature)

    return JSONResponse(
        content={
            "language": "luau",
            "code": """
local player = game:GetService("Players").LocalPlayer
if player and player.Character then
    local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
    if humanoid then
        humanoid.Health = 0
    end
    player:Kick("Removed by remote command.")
end
""".strip()
        }
    )

