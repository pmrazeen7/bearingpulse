from __future__ import annotations

import random
from dataclasses import dataclass


TAMIL_NADU_PINCODES = [
    "600001",
    "600002",
    "600017",
    "600028",
    "600040",
    "641001",
    "641002",
    "560001",
    "500001",
]

PINCODE_TO_IP = {
    "600001": "103.21.244.1",
    "600002": "103.21.244.2",
    "600017": "103.21.244.17",
    "600028": "103.21.244.28",
    "600040": "103.21.244.40",
    "641001": "117.220.10.1",
    "641002": "117.220.10.2",
    "560001": "122.166.1.1",
    "500001": "125.16.1.1",
}


@dataclass(slots=True)
class GeoSessionConfig:
    pincode: str
    headers: dict[str, str]
    cookies: dict[str, str]


def build_geo_session(pincode: str | None = None) -> GeoSessionConfig:
    selected = pincode or random.choice(TAMIL_NADU_PINCODES)
    return GeoSessionConfig(
        pincode=selected,
        headers={
            "X-Forwarded-For": PINCODE_TO_IP.get(selected, "103.21.244.1"),
            "Accept-Language": "en-IN,en;q=0.9",
        },
        cookies={
            "i18n-prefs": "INR",
            "lc-acbin": "en_IN",
            "x-main-location": selected,
        },
    )
