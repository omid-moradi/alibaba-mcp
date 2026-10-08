"""Centralized endpoint definitions for the Alibaba.ir live provider.

IMPORTANT: none of the paths below are verified. Alibaba.ir publishes no
official public API; its internal endpoints are undocumented and protected.
All values are placeholders that exist only so that, IF an official API is
ever published or legitimately provided, every URL lives in exactly one
place instead of being scattered across the codebase.

Never add scraping, CAPTCHA-bypass, or session-spoofing logic here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlibabaEndpoints:
    """Endpoint map for a future official API. All fields are unverified."""

    base_url: str

    @property
    def airports(self) -> str:
        return f"{self.base_url}/airports"  # placeholder

    @property
    def flight_search(self) -> str:
        return f"{self.base_url}/flights/search"  # placeholder

    @property
    def hotel_search(self) -> str:
        return f"{self.base_url}/hotels/search"  # placeholder

    @property
    def train_search(self) -> str:
        return f"{self.base_url}/trains/search"  # placeholder

    @property
    def bus_search(self) -> str:
        return f"{self.base_url}/buses/search"  # placeholder
