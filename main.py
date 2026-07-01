from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="SellerSprite GPT Action", version="1.0.0")

GPT_ACTION_KEY = "123456"


class AsinRequest(BaseModel):
    marketplace: str
    asin: str
    size: int = 10


@app.get("/health")
def health():
    return {
        "ok": True,
        "message": "服务器已上线"
    }


@app.post("/asin/deep-dive")
def asin_deep_dive(
    req: AsinRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    if x_api_key != GPT_ACTION_KEY:
        raise HTTPException(status_code=401, detail="API Key 错误")

    return {
        "ok": True,
        "message": "测试成功：GPT 已经能调用你的服务器",
        "query": {
            "marketplace": req.marketplace,
            "asin": req.asin,
            "size": req.size
        },
        "detail": {
            "asin": req.asin,
            "marketplace": req.marketplace,
            "price": "测试数据",
            "rating": "测试数据",
            "reviews": "测试数据",
            "bsr": "测试数据"
        },
        "traffic_keywords": [
            {
                "keyword": "cooling blanket",
                "search_volume": 10000,
                "purchase_rate": "测试数据",
                "ppc_bid": "测试数据"
            }
        ]
    }
