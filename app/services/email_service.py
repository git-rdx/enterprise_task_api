import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> None:

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email

        message.set_content("Please use an HTML-compatible email client.")

        message.add_alternative(html_content, subtype="html")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()

            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.send_message(message)

    def send_verification_email(self, email: str, token: str) -> None:

        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        html = f"""
        <html>
            <body>
                <h2>Verify your email</h2>

                <p>
                    Welcome to Enterprise Task API.
                </p>

                <p>
                    Click the link below to verify your email:
                </p>

                <a href="{verification_url}">
                    Verify Email
                </a>

                <p>
                    This link will expire in
                    {settings.EMAIL_VERIFICATION_EXPIRE_MINUTES}
                    minutes.
                </p>
            </body>
        </html>
        """

        self._send_email(to_email=email, subject="Verify your email", html_content=html)

    def send_password_reset_email(
        self,
        email: str,
        token: str,
    ) -> None:

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        html = f"""
        <html>
            <body>
                <h2>Password Reset</h2>

                <p>
                    We received a request to reset your password.
                </p>

                <p>
                    Click the link below:
                </p>

                <a href="{reset_url}">
                    Reset Password
                </a>

                <p>
                    This link will expire in
                    {settings.PASSWORD_RESET_EXPIRE_MINUTES}
                    minutes.
                </p>

                <p>
                    If you did not request this,
                    you can safely ignore this email.
                </p>
            </body>
        </html>
        """

        self._send_email(
            to_email=email,
            subject="Reset your password",
            html_content=html,
        )


email_service = EmailService()
