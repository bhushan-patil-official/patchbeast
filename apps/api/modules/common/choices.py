from django.db import models


class Verification(models.TextChoices):
    """Shared verification-status model. Confirmed = 2 independent sources or a video;
    Reported = one linked source; Rumour = unverified."""

    RUMOUR = "rumour", "Rumour"
    REPORTED = "reported", "Reported"
    CONFIRMED = "confirmed", "Confirmed"


VERIFICATION_RANK = {"rumour": 0, "reported": 1, "confirmed": 2}
