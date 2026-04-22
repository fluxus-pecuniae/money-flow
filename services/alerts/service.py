"""Alert service placeholder."""

from core.interfaces.services import AlertService


class DefaultAlertService(AlertService):
    async def send_alert(self, event_type: str, message: str, severity: str) -> None:
        raise NotImplementedError("Alerts delivery is deferred.")

