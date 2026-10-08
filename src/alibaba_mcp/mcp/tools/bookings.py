"""Sandbox booking tools.

IMPORTANT: bookings in this project are ALWAYS simulated inside the server
process. No real reservation is made on Alibaba.ir or any other real system.
The tools are annotated as destructive on purpose: hosts that honor
annotations will ask the user for confirmation before calling them.
"""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from alibaba_mcp.domain.enums import BookingItemKind
from alibaba_mcp.domain.models import Booking
from alibaba_mcp.mcp.context import AppContext

_BOOKING_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=False,
)

_STATUS_ANNOTATIONS = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def register(mcp: MCPServer, ctx: AppContext) -> None:
    @mcp.tool(annotations=_BOOKING_ANNOTATIONS)
    async def create_sandbox_booking(
        item_kind: BookingItemKind, item_id: str, passengers: int = 1
    ) -> Booking:
        """Create a SIMULATED sandbox booking for a selected option.

        Use this only when the user explicitly confirms they want a booking
        demo. This is a sandbox: nothing is reserved on any real system, no
        payment happens, and the booking lives only in the current server
        process (it disappears on restart). The response is clearly marked
        simulated=true.

        Args:
            item_kind: What is being booked: 'flight', 'hotel', 'train',
                'bus' or 'tour'.
            item_id: Id of the option to book, exactly as returned by the
                matching search tool.
            passengers: Number of travelers (1-9).
        """
        return await ctx.call(
            "create_sandbox_booking",
            lambda: ctx.service.create_sandbox_booking(item_kind, item_id, passengers),
        )

    @mcp.tool(annotations=_STATUS_ANNOTATIONS)
    async def get_booking_status(booking_id: str) -> Booking:
        """Look up a SIMULATED sandbox booking by its reference.

        Bookings exist only inside the current server process; use the id
        returned by create_sandbox_booking. Read-only.

        Args:
            booking_id: Booking reference, e.g. 'BKG-...' from create_sandbox_booking.
        """
        return await ctx.call(
            "get_booking_status", lambda: ctx.service.get_booking(booking_id)
        )

    @mcp.tool(annotations=_BOOKING_ANNOTATIONS)
    async def cancel_sandbox_booking(booking_id: str) -> Booking:
        """Cancel a SIMULATED sandbox booking.

        Marks the booking as cancelled (no real refund occurs). Fails if the
        booking does not exist or is already cancelled. Sandbox only.

        Args:
            booking_id: Booking reference, e.g. 'BKG-...' from create_sandbox_booking.
        """
        return await ctx.call(
            "cancel_sandbox_booking", lambda: ctx.service.cancel_booking(booking_id)
        )
