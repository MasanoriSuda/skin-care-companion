from typing import Protocol

from app.models import Concern, ProductRecord


class Retriever(Protocol):
    def retrieve_products(
        self,
        query: str,
        concerns: list[Concern],
        budget_yen: int,
        limit: int = 8,
    ) -> list[ProductRecord]:
        """Return product records that exist in the local product DB."""

    def retrieve_memos(self, concerns: list[Concern], limit: int = 3) -> list[str]:
        """Return beautician memo snippets for the selected concerns."""

