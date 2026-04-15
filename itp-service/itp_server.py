"""ITP (Identical Twins Protocol) FastAPI Service
Message compression/decompression service for agent communications.
Port: 8100
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from collections import deque
import time

app = FastAPI(title="ITP Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Codebook ---
# Maps human-readable phrases/words to ITP short codes
CODEBOOK: dict[str, str] = {
    # Operations
    "analyze": "ANL",
    "synthesize": "SYN",
    "optimize": "OPT",
    "debug": "DBG",
    "report": "RPT",
    "plan": "PLN",
    "execute": "EXE",
    "review": "REV",
    "test": "TST",
    "document": "DOC",
    "search": "SRH",
    "validate": "VAL",
    "generate": "GEN",
    "transform": "TRN",
    "aggregate": "AGG",
    # Roles
    "service": "SVC",
    "director": "DIR",
    "worker": "WKR",
    "monitor": "MON",
    "agent": "AGT",
    "orchestrator": "ORC",
    # Status
    "success": "STS/OK",
    "error": "STS/ERR",
    "update": "STS/UPD",
    "pending": "STS/PEND",
    "acknowledged": "STS/ACK",
    # Data types
    "json data": "DAT/JSON",
    "text data": "DAT/TXT",
    "binary data": "DAT/BIN",
    "metrics data": "DAT/MTR",
    # Domain objects
    "trading": "TRD",
    "performance": "PERF",
    "system": "SYS",
    "memory": "MEM",
    "payment": "PAY",
    "wallet": "WLT",
    "self-improvement": "RSI",
}

# Reverse codebook for decoding
REVERSE_CODEBOOK: dict[str, str] = {v: k for k, v in CODEBOOK.items()}

# --- Stats ---
_stats = {
    "messages_processed": 0,
    "messages_compressed": 0,
    "total_original_tokens": 0,
    "total_compressed_tokens": 0,
}

# History ring buffer (last 1000 messages)
_history: deque = deque(maxlen=1000)


# --- Models ---
class EncodeRequest(BaseModel):
    message: str
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None


class EncodeResponse(BaseModel):
    encoded: str
    was_compressed: bool
    savings_pct: float
    original_tokens: int
    compressed_tokens: int


class DecodeRequest(BaseModel):
    message: str


class DecodeResponse(BaseModel):
    decoded: str
    was_itp: bool
    original: str


# --- Helpers ---
def _approx_tokens(text: str) -> int:
    """Rough token estimate: words + punctuation."""
    return max(1, len(text.split()))


def _encode_message(message: str) -> tuple[str, bool]:
    """
    Scan message for codebook phrases (longest match first),
    replace with ITP codes joined by '+', wrap in ITP:<codes>.
    Returns (encoded_str, was_compressed).
    """
    # Sort by length descending for greedy longest-match
    sorted_phrases = sorted(CODEBOOK.keys(), key=len, reverse=True)
    codes_found = []
    remaining = message.lower()
    used_positions: list[tuple[int, int, str]] = []

    for phrase in sorted_phrases:
        start = 0
        while True:
            idx = remaining.find(phrase, start)
            if idx == -1:
                break
            # Avoid overlapping with already-matched spans
            overlap = any(s <= idx < e for s, e, _ in used_positions)
            if not overlap:
                used_positions.append((idx, idx + len(phrase), CODEBOOK[phrase]))
            start = idx + 1

    if not used_positions:
        return message, False

    # Build encoded string
    used_positions.sort(key=lambda x: x[0])
    codes_found = [code for _, _, code in used_positions]
    encoded = "ITP:" + "+".join(codes_found)

    # Only compress if it actually saves space (>10% reduction)
    orig_len = len(message)
    enc_len = len(encoded)
    if orig_len == 0 or (orig_len - enc_len) / orig_len <= 0.10:
        return message, False

    return encoded, True


def _decode_message(message: str) -> tuple[str, bool]:
    """
    Decode ITP:<codes> format back to human-readable.
    Returns (decoded_str, was_itp).
    """
    if not message.startswith("ITP:"):
        return message, False

    codes_part = message[4:]  # strip "ITP:"
    codes = codes_part.split("+")
    decoded_parts = []
    for code in codes:
        decoded_parts.append(REVERSE_CODEBOOK.get(code, code))

    return " ".join(decoded_parts), True


# --- Endpoints ---
@app.post("/tools/encode", response_model=EncodeResponse)
async def encode(req: EncodeRequest) -> EncodeResponse:
    encoded, was_compressed = _encode_message(req.message)
    orig_tokens = _approx_tokens(req.message)
    comp_tokens = _approx_tokens(encoded)
    savings = max(0.0, round((orig_tokens - comp_tokens) / orig_tokens * 100, 2)) if orig_tokens > 0 else 0.0

    _stats["messages_processed"] += 1
    if was_compressed:
        _stats["messages_compressed"] += 1
    _stats["total_original_tokens"] += orig_tokens
    _stats["total_compressed_tokens"] += comp_tokens

    _history.append({
        "type": "encode",
        "original": req.message,
        "encoded": encoded,
        "was_compressed": was_compressed,
        "savings_pct": savings,
        "source_agent": req.source_agent,
        "target_agent": req.target_agent,
        "ts": time.time(),
    })

    return EncodeResponse(
        encoded=encoded,
        was_compressed=was_compressed,
        savings_pct=savings,
        original_tokens=orig_tokens,
        compressed_tokens=comp_tokens,
    )


@app.post("/tools/decode", response_model=DecodeResponse)
async def decode(req: DecodeRequest) -> DecodeResponse:
    decoded, was_itp = _decode_message(req.message)

    _stats["messages_processed"] += 1
    _history.append({
        "type": "decode",
        "original": req.message,
        "decoded": decoded,
        "was_itp": was_itp,
        "ts": time.time(),
    })

    return DecodeResponse(decoded=decoded, was_itp=was_itp, original=req.message)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "codebook_entries": len(CODEBOOK),
        "messages_processed": _stats["messages_processed"],
    }


@app.get("/tools/stats")
async def stats():
    total_orig = _stats["total_original_tokens"]
    total_comp = _stats["total_compressed_tokens"]
    overall_savings = (
        round((total_orig - total_comp) / total_orig * 100, 2)
        if total_orig > 0 else 0.0
    )
    return {
        "messages_processed": _stats["messages_processed"],
        "messages_compressed": _stats["messages_compressed"],
        "compression_rate_pct": (
            round(_stats["messages_compressed"] / _stats["messages_processed"] * 100, 2)
            if _stats["messages_processed"] > 0 else 0.0
        ),
        "total_original_tokens": total_orig,
        "total_compressed_tokens": total_comp,
        "overall_savings_pct": overall_savings,
    }


@app.get("/tools/codebook")
async def codebook():
    return {
        "entries": len(CODEBOOK),
        "codebook": CODEBOOK,
        "reverse": REVERSE_CODEBOOK,
    }


@app.get("/tools/history")
async def history(limit: int = 20):
    items = list(_history)
    return {
        "count": len(items),
        "items": items[-limit:],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8100)
