from app.celery_app import celery_app
from app.services.email_service import email_service


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_verification_email(email: str, token: str):
    email_service.send_verification_email(
        email,
        token,
    )

    return {
        "status": "sent",
        "email": email,
    }


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_password_reset_email(email: str, token: str):
    email_service.send_password_reset_email(
        email,
        token,
    )

    return {
        "status": "sent",
        "email": email,
    }
