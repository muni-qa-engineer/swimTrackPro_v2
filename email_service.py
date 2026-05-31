

"""
Brevo Email Service for SwimTrackPro
-----------------------------------
This module provides a reusable function to send email notifications
using the Brevo transactional email API.

Environment Variables Required:
- BREVO_API_KEY
- BREVO_SENDER_EMAIL
- BREVO_SENDER_NAME
- ADMIN_ALERT_EMAIL
"""

import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from config import (
    BREVO_API_KEY,
    BREVO_SENDER_EMAIL,
    BREVO_SENDER_NAME,
    ADMIN_ALERT_EMAIL,
)


def send_email(subject, html_content, to_email=None, to_name="Admin"):
    """
    Send an email using Brevo.

    Parameters:
        subject (str): Email subject.
        html_content (str): HTML body content.
        to_email (str, optional): Recipient email address.
            If not provided, ADMIN_ALERT_EMAIL will be used.
        to_name (str, optional): Recipient display name.

    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    api_key = BREVO_API_KEY
    sender_email = BREVO_SENDER_EMAIL
    sender_name = BREVO_SENDER_NAME or "SwimTrackPro"
    default_recipient = ADMIN_ALERT_EMAIL
    print(f"BREVO_API_KEY loaded: {'YES' if api_key else 'NO'}")

    # Validate required configuration.
    if not api_key:
        print("Brevo email skipped: BREVO_API_KEY is not configured.")
        return False

    if not sender_email:
        print("Brevo email skipped: BREVO_SENDER_EMAIL is not configured.")
        return False

    recipient_email = to_email or default_recipient
    if not recipient_email:
        print("Brevo email skipped: No recipient email configured.")
        return False

    try:
        # Configure Brevo API client.
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key

        api_client = sib_api_v3_sdk.ApiClient(configuration)
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

        # Construct email payload.
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[
                {
                    "email": recipient_email,
                    "name": to_name,
                }
            ],
            sender={
                "email": sender_email,
                "name": sender_name,
            },
            subject=subject,
            html_content=html_content,
        )

        # Send the email.
        api_instance.send_transac_email(send_smtp_email)
        print(f"Brevo email sent successfully to {recipient_email}.")
        return True

    except ApiException as exc:
        print(f"Brevo API error: {exc}")
        return False

    except Exception as exc:
        print(f"Unexpected email error: {exc}")
        return False