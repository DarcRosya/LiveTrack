from pathlib import Path

from pydantic import EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from src.config.settings import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail.USERNAME,
    MAIL_PASSWORD=settings.mail.PASSWORD,
    MAIL_FROM=settings.mail.FROM,
    MAIL_PORT=465,
    MAIL_SERVER=settings.mail.SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=BASE_DIR / "src" / "templates",
)

async def send_verification_email(email: EmailStr, token: str):
    verification_link = f"{settings.run.CLIENT_BASE_URL}auth/verify?token={token}"

    template_data = {
        "verification_link": verification_link
    }

    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        template_body=template_data,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="emails/verify_email.html")
