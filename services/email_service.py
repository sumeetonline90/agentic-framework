from typing import Dict, List


class EmailService:
    """Thin email service abstraction (placeholder)."""

    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config

    async def send(self, sender: str, recipients: List[str], subject: str, body: str) -> bool:
        # In the future, use a real implementation or reuse EmailAgent internals
        return False


