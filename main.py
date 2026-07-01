import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="SellerSprite GPT Action", version="2.0.0")

GPT_ACTION_KEY = "123456"
SELLERSPRITE_SECRET = os.getenv("SELLERSPRITE_SECRET")
SELLERSPRITE_BASE_URL = "https://api.sellersprite.com"


class AsinRequest(BaseModel):
    marketplace: str
    asin: str
    size: int = 10


def previous_month() -> str:
    today = datetime.utcnow().replace(day=1)
    prev = today - timedelta(days=1)
    return prev.strftime("%Y%m")


def seller_headers():
    if not SELLERSPRITE_SECRET:
        raise HTTPException(status_code=500, detail="Render 未设置 SELLERSPRITE_SECRET")

    return {
        "secret-key": SELLERSPRITE_SECRET,
        "Content-Type": "application/json;charset=utf-8",
        "x-request-id": str(uuid.uuid4())
    }


async def seller_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(
            SELLERSPRITE_BASE_URL + path,
            headers=seller_headers(),
            json=payload
        )

    try:
        return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="卖家精灵返回的不是 JSON")


@app.get("/health")
def health():
    return {
        "ok": True,
        "message": "服务器已上线",
        "seller_secret_set": bool(SELLERSPRITE_SECRET)
    }


@app.get("/privacy")
def privacy():
    return {
        "name": "SellerSprite GPT Action",
        "privacy": "This service only forwards ASIN and marketplace requests to the configured SellerSprite API. It does not store user conversation content."
    }


@app.post("/asin/deep-dive")
async def asin_deep_dive(
    req: AsinRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    if x_api_key != GPT_ACTION_KEY:
        raise HTTPException(status_code=401, detail="API Key 错误")

    marketplace = req.marketplace.upper().strip()
    asin = req.asin.upper().strip()
    size = min(req.size, 10)
    month = previous_month()

    keyword_order_raw = await seller_post("/v1/keyword-order", {
        "marketplace": marketplace,
        "asins": [asin],
        "reverseType": "M",
        "date": month,
        "page": 1,
        "size": 50
    })

    if keyword_order_raw.get("code") != "OK":
        return {
            "ok": False,
            "source": "sellersprite",
            "message": keyword_order_raw.get("message"),
            "code": keyword_order_raw.get("code"),
            "query": {
                "marketplace": marketplace,
                "asin": asin,
                "month": month
            },
            "tip": "如果提示 ERROR_SECRET_KEY，说明卖家精灵密钥错误；如果提示 ERROR_VISIT_MAX，说明调用次数可能用完。"
        }

    items = keyword_order_raw.get("data", {}).get("items", [])[:size]

    keywords = []
    for item in items:
        keywords.append({
            "keyword": item.get("keyword"),
            "keyword_cn": item.get("keywordCn"),
            "searches": item.get("searches"),
            "search_rank": item.get("searchRank"),
            "monopoly_click_rate": item.get("monopolyClickRate"),
            "conversion_share_rate": item.get("cvsShareRate"),
            "top3_clicking_rate": item.get("top3ClickingRate"),
            "top3_conversion_rate": item.get("top3ConversionRate"),
            "conversion_type": item.get("conversionType")
        })

    return {
        "ok": True,
        "source": "sellersprite",
        "message": "已获取卖家精灵真实出单词数据",
        "query": {
            "marketplace": marketplace,
            "asin": asin,
            "month": month,
            "size": size
        },
        "detail": {
            "asin": asin,
            "marketplace": marketplace,
            "price": "数据缺失",
            "rating": "数据缺失",
            "reviews": "数据缺失",
            "bsr": "数据缺失"
        },
        "traffic_keywords": keywords,
        "keyword_order": keywords,
        "data_gap": [
            "暂未接入 ASIN 基础详情",
            "暂未接入流量来源",
            "暂未接入完整流量词列表"
        ]
    }
