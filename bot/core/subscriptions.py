# bot/core/subscriptions.py
from twitchio import eventsub

def get_subscriptions(owner_id: str, bot_id: str) -> list[eventsub.SubscriptionPayload]:
    """
    Возвращает список подписок для EventSub.
    Важно: создаём экземпляры только когда есть реальные ID!
    """
    return [
        # Чат: читаем сообщения в канале owner_id от имени bot_id
        eventsub.ChatMessageSubscription(
            broadcaster_user_id=owner_id,
            user_id=bot_id
        ),
        # Стрим онлайн
        eventsub.StreamOnlineSubscription(
            broadcaster_user_id=owner_id
        ),
        # Стрим оффлайн
        eventsub.StreamOfflineSubscription(
            broadcaster_user_id=owner_id
        ),
    ]