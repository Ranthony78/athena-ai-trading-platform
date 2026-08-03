from shared.repositories import BaseRepository

from ..models import Instrument


class MarketRepository(BaseRepository[Instrument]):
    """
    Legacy market repository — retained for backward compatibility.
    New code should use InstrumentRepository directly.
    """

    model = Instrument