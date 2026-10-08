"""Travel policy knowledge base.

A small, static corpus of travel-policy documents (cancellation, refunds,
baggage, check-in...). It backs two surfaces:

* the ``alibaba://travel/policies`` and ``alibaba://travel/cancellation-policy``
  resources (context for the application to load), and
* the ``search_travel_policies`` tool (lightweight keyword retrieval so an
  agent can pull only the relevant snippet into the conversation).

This is a deliberately dependency-free retrieval layer ("poor man's RAG").
It is decoupled from the MCP server and from any provider; swapping in a
vector store later would not change the tool's contract.

The policy text is generic educational content written for this project.
It is NOT copied from Alibaba.ir and must not be presented as official
Alibaba.ir policy.
"""

import re

from pydantic import BaseModel, Field

_WORD = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


class PolicyEntry(BaseModel):
    """One retrievable policy document."""

    topic: str = Field(description="Stable topic slug, e.g. 'cancellation'.")
    title: str = Field(description="Human-readable policy title.")
    text: str = Field(description="Full policy text.")


POLICY_DOCUMENTS: list[PolicyEntry] = [
    PolicyEntry(
        topic="cancellation",
        title="Ticket cancellation rules",
        text=(
            "Cancellations are possible until a few hours before departure, depending on the "
            "transport type and the fare's refund rules. System (published-fare) flight tickets "
            "usually carry a cancellation penalty that grows as departure approaches; charter "
            "tickets are often non-refundable or carry a heavy penalty. Hotel bookings marked "
            "as free-cancellation can be cancelled without penalty before the property's cutoff "
            "(commonly 24-72 hours before check-in). Train and bus tickets can typically be "
            "cancelled up to a few hours before departure with a modest penalty. In this demo "
            "server, all cancellation behavior is simulated."
        ),
    ),
    PolicyEntry(
        topic="refund",
        title="Refund process and timing",
        text=(
            "Refunds are issued back to the original payment method after the cancellation is "
            "confirmed. Domestic refunds are usually processed within a few business days, "
            "but settlement by the bank can take longer. The refunded amount equals the fare "
            "minus any cancellation penalty applicable at the time of cancellation. Charter "
            "and promotional fares may be non-refundable even when the booking itself can be "
            "cancelled."
        ),
    ),
    PolicyEntry(
        topic="baggage",
        title="Baggage allowance",
        text=(
            "Checked baggage allowance depends on the airline, fare family and route: domestic "
            "economy fares commonly include 15-25 kg, business class more, and charter fares "
            "often as little as 15 kg. Excess baggage is charged per kilogram at check-in and "
            "can be substantially cheaper when pre-purchased. Hand luggage is typically limited "
            "to one piece up to 5-7 kg. Train passengers can carry personal luggage that fits "
            "the overhead racks; buses allow one suitcase in the hold."
        ),
    ),
    PolicyEntry(
        topic="check-in",
        title="Airport check-in guidance",
        text=(
            "Arrive at domestic terminals at least 90 minutes before departure and at "
            "international terminals at least 3 hours before. Online check-in is not widely "
            "available for domestic Iranian flights, so plan for counter check-in. A valid "
            "national ID card (for domestic flights) or passport (for international flights) "
            "in the passenger's own name is mandatory. Seat selection for domestic flights "
            "generally happens at check-in, not at booking time."
        ),
    ),
    PolicyEntry(
        topic="documents",
        title="Passenger documents and name rules",
        text=(
            "Each passenger must present valid identification matching the ticket name. "
            "Domestic flights accept the national ID card; international travel requires a "
            "valid passport and, where applicable, a visa. Name corrections after booking are "
            "usually not allowed on system tickets and may be possible only on some charter "
            "fares before payment. It is the traveler's responsibility to hold the correct "
            "visa and entry documents for the destination country."
        ),
    ),
    PolicyEntry(
        topic="children",
        title="Child and infant fares",
        text=(
            "Children aged 2 to 12 typically pay 50-100% of the adult fare depending on the "
            "fare class. Infants under 2 without their own seat are charged around 10% of the "
            "adult fare on flights and travel free on trains and buses when sharing a seat "
            "with an adult. Documentation proving the child's age may be requested at check-in."
        ),
    ),
    PolicyEntry(
        topic="payment",
        title="Payment methods",
        text=(
            "Iranian travel platforms accept domestic Shetab bank cards for online payment. "
            "Prices are displayed in Toman. Fares are not guaranteed until payment is "
            "completed: inventory and prices can change between search and checkout, "
            "especially close to departure. This demo server never processes any real payment."
        ),
    ),
    PolicyEntry(
        topic="charter-vs-system",
        title="Charter vs. system (published) tickets",
        text=(
            "System tickets are published fares with standard rules: they can usually be "
            "refunded with a penalty and baggage allowance follows the airline's rules. "
            "Charter tickets come from pre-purchased blocks, are often cheaper, but carry "
            "restrictions: low or no baggage, strict or no refunds, and limited name-change "
            "options. Agents should tell travelers which type of ticket they are about to "
            "book."
        ),
    ),
]

_BY_TOPIC = {entry.topic: entry for entry in POLICY_DOCUMENTS}


def get_policy(topic: str) -> PolicyEntry | None:
    """Return the policy entry for an exact topic slug, if present."""
    return _BY_TOPIC.get(topic.strip().lower())


def search_policies(query: str, limit: int = 3) -> list[PolicyEntry]:
    """Rank policy entries by keyword overlap with the query.

    A simple, deterministic, dependency-free scorer. It demonstrates the
    retrieval seam without pretending to be semantic search.
    """
    tokens = {t.lower() for t in _WORD.findall(query)}
    if not tokens:
        return POLICY_DOCUMENTS[:limit]
    scored = []
    for entry in POLICY_DOCUMENTS:
        haystack = f"{entry.topic} {entry.title} {entry.text}".lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda pair: (-pair[0], pair[1].topic))
    return [entry for _, entry in scored[:limit]]
