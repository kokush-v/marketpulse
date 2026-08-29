# Import SQLAlchemy models here for Alembic autogenerate discovery.
from app.features.ai_assistant.models import (  # noqa: F401
    AssistantConversation,
    AssistantMessage,
    AssistantPendingAction,
)
from app.features.alerts.models import AlertRule  # noqa: F401
from app.features.auth.models import User  # noqa: F401
from app.features.background_jobs.models import BackgroundJobCursor  # noqa: F401
from app.features.notifications.models import NotificationRecord  # noqa: F401
from app.features.telegram.models import (  # noqa: F401
    TelegramConnection,
    TelegramConnectionToken,
)
from app.features.watchlists.models import WatchlistAsset  # noqa: F401
