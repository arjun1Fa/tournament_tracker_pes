"""Push notification service using Firebase Cloud Messaging (FCM).

Sends notifications to players when:
    - A match result needs verification
    - A match is disputed (notify admin)
    - A tournament starts
"""
import logging

from ..models.user import DeviceToken

logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization is deferred to avoid import errors
# when Firebase credentials aren't configured (e.g., in tests)
_firebase_initialized = False


def _ensure_firebase():
    """Initialize Firebase Admin SDK if not already done."""
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials
        import os

        creds_path = os.environ.get('FIREBASE_CREDENTIALS_JSON', '')
        if not creds_path or not os.path.exists(creds_path):
            logger.warning('Firebase credentials not found — push notifications disabled.')
            return False

        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info('Firebase Admin SDK initialized successfully.')
        return True
    except Exception as e:
        logger.error(f'Failed to initialize Firebase: {e}')
        return False


def send_verification_request(opponent_user_id, match_id):
    """Send a push notification asking the opponent to verify a match result.

    Args:
        opponent_user_id: User ID of the opponent to notify.
        match_id: ID of the match to verify.
    """
    if not _ensure_firebase():
        logger.info(f'Skipping notification for match {match_id} — Firebase not configured.')
        return

    tokens = _get_user_tokens(opponent_user_id)
    if not tokens:
        logger.info(f'No device tokens found for user {opponent_user_id}.')
        return

    _send_notification(
        tokens=tokens,
        title='Match Result Submitted',
        body='Your opponent has reported a match result. Tap to verify.',
        data={
            'type': 'match_verification',
            'match_id': str(match_id),
        },
    )


def send_dispute_notification(admin_user_id, match_id):
    """Notify admin that a match result has been disputed.

    Args:
        admin_user_id: User ID of the admin.
        match_id: ID of the disputed match.
    """
    if not _ensure_firebase():
        return

    tokens = _get_user_tokens(admin_user_id)
    if not tokens:
        return

    _send_notification(
        tokens=tokens,
        title='Match Disputed',
        body='A match result has been disputed and requires your review.',
        data={
            'type': 'match_dispute',
            'match_id': str(match_id),
        },
    )


def send_tournament_started(tournament_id, participant_user_ids):
    """Notify all participants that a tournament has started.

    Args:
        tournament_id: ID of the tournament.
        participant_user_ids: List of user IDs to notify.
    """
    if not _ensure_firebase():
        return

    for user_id in participant_user_ids:
        tokens = _get_user_tokens(user_id)
        if tokens:
            _send_notification(
                tokens=tokens,
                title='Tournament Started!',
                body='Fixtures have been generated. Check your upcoming matches.',
                data={
                    'type': 'tournament_started',
                    'tournament_id': str(tournament_id),
                },
            )


def _get_user_tokens(user_id):
    """Get all FCM tokens for a user.

    Returns:
        List of FCM token strings.
    """
    devices = DeviceToken.query.filter_by(user_id=user_id).all()
    return [d.fcm_token for d in devices]


def _send_notification(tokens, title, body, data=None):
    """Send a push notification to one or more device tokens.

    Args:
        tokens: List of FCM token strings.
        title: Notification title.
        body: Notification body text.
        data: Optional dict of custom data payload.
    """
    try:
        from firebase_admin import messaging

        for token in tokens:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        click_action='FLUTTER_NOTIFICATION_CLICK',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            try:
                messaging.send(message)
                logger.info(f'Notification sent to token: {token[:20]}...')
            except messaging.UnregisteredError:
                # Token is invalid, remove it
                DeviceToken.query.filter_by(fcm_token=token).delete()
                from ..extensions import db
                db.session.commit()
                logger.info(f'Removed invalid FCM token: {token[:20]}...')
            except Exception as e:
                logger.error(f'Failed to send notification: {e}')

    except ImportError:
        logger.warning('firebase_admin not available — skipping notification.')
    except Exception as e:
        logger.error(f'Notification error: {e}')
