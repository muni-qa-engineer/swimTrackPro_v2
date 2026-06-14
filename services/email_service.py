

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
    # api_key = os.getenv("BREVO_API_KEY")
    # sender_email = os.getenv("BREVO_SENDER_EMAIL")
    # sender_name = os.getenv("BREVO_SENDER_NAME", "SwimTrackPro")
    # default_recipient = os.getenv("ADMIN_ALERT_EMAIL")
    api_key = BREVO_API_KEY
    sender_email = BREVO_SENDER_EMAIL
    sender_name = BREVO_SENDER_NAME
    default_recipient = ADMIN_ALERT_EMAIL

    # print("DEBUG API KEY:", bool(api_key))
    # print("DEBUG SENDER:", sender_email)
    # print("DEBUG ADMIN:", default_recipient)

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


def send_booking_notification(booking):
    """Send a booking alert email using Brevo."""
    try:
        subject = f"🏊 New Booking Alert - {booking.get('booking_code', '')}"

        html_content = f"""
        <h2>🏊 New Booking Alert</h2>
        <p><strong>Booking ID:</strong> {booking.get('booking_code', '')}</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><td><strong>Swimmer</strong></td><td>{booking.get('student', '')}</td></tr>
            <tr><td><strong>Package</strong></td><td>{booking.get('package', '')}</td></tr>
            <tr><td><strong>Start Date</strong></td><td>{booking.get('start_date', '')}</td></tr>
            <tr><td><strong>End Date</strong></td><td>{booking.get('end_date', '')}</td></tr>
            <tr><td><strong>Time</strong></td><td>{booking.get('time', '')}</td></tr>
            <tr><td><strong>Persons</strong></td><td>{booking.get('persons', '')}</td></tr>
            <tr><td><strong>Fee</strong></td><td>₹{booking.get('fee', 0)}</td></tr>
            <tr><td><strong>Payment Status</strong></td><td>{booking.get('payment_request', '')}</td></tr>
            <tr><td><strong>Location</strong></td><td>{booking.get('location', '')}</td></tr>
            <tr><td><strong>Email</strong></td><td>{booking.get('email', '')}</td></tr>
            <tr><td><strong>Booked By</strong></td><td>{booking.get('owner_name', '')}</td></tr>
            <tr><td><strong>Phone</strong></td><td>{booking.get('owner_phone', '')}</td></tr>
        </table>
        """

        success = send_email(
            subject=subject,
            html_content=html_content
        )

        if not success:
            print("Booking notification email was not sent.")

    except Exception as exc:
        print(f"Email notification failed: {exc}")

# --- Booking Confirmation Email to Swimmer ---
def send_booking_confirmation_email(booking):
    """Send booking confirmation email to swimmer."""

    try:
        email = (booking.get('email') or '').strip()

        if not email:
            return

        subject = f"🏊 Booking Confirmed - {booking.get('booking_code', 'SwimTrackPro')}"

        html_content = f"""
        <h2>🏊 Booking Confirmation</h2>

        <p>Hello {booking.get('owner_name', 'Swimmer')},</p>

        <p>Your booking for <strong>{booking.get('student', '')}</strong> has been successfully created.</p>

        <table border="0" cellpadding="4" cellspacing="0">
            <tr><td><strong>Booking ID</strong></td><td>: {booking.get('booking_code', '')}</td></tr>
            <tr><td><strong>Package</strong></td><td>: {booking.get('package', '')}</td></tr>
            <tr><td><strong>Start Date</strong></td><td>: {booking.get('start_date', '')}</td></tr>
            <tr><td><strong>Time</strong></td><td>: {booking.get('time', '')}</td></tr>
            <tr><td><strong>Fee</strong></td><td>: ₹{booking.get('fee', 0)}</td></tr>
            <tr><td><strong>Payment</strong></td><td>: {booking.get('payment_request', 'Not Paid')}</td></tr>
        </table>

        <br>

        <p>
        Track your booking:<br>
        <a href="https://swimtrackpro.onrender.com">https://swimtrackpro.onrender.com</a>
        </p>

        <p>Thank you for choosing SwimTrackPro 🏊</p>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=booking.get('owner_name', 'Swimmer')
        )

    except Exception as exc:
        print(f"Booking confirmation email failed: {exc}")


# --- Booking Updated Email to Swimmer ---
def send_booking_updated_email(booking, changes):
    """Send booking updated email to swimmer."""
    try:
        email = (booking.get('email') or '').strip()

        if not email:
            return

        changes_html = ""
        for change in changes:
            changes_html += f"<li><strong>{change['field']}</strong>: {change['old']} → {change['new']}</li>"

        subject = f"✏️ Booking Updated - {booking.get('booking_code', 'SwimTrackPro')}"

        html_content = f"""
        <h2>✏️ Booking Updated</h2>

        <p>Hello {booking.get('owner_name', 'Swimmer')},</p>

        <p>Your booking for <strong>{booking.get('student', '')}</strong> has been updated successfully.</p>

        <p><strong>Booking ID:</strong> {booking.get('booking_code', '')}</p>

        <p><strong>Changes Made:</strong></p>
        <ul>
        {changes_html}
        </ul>

        <p>
        Track your booking:<br>
        <a href="https://swimtrackpro.onrender.com">https://swimtrackpro.onrender.com</a>
        </p>

        <p>Thank you for choosing SwimTrackPro 🏊</p>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=booking.get('owner_name', 'Swimmer')
        )

    except Exception as exc:
        print(f"Booking updated email failed: {exc}")


# --- Booking Update Alert Email to Trainer/Admin ---
def send_booking_update_alert(booking, changes):
    """Send booking update alert email to trainer/admin."""
    try:
        changes_html = ""
        for change in changes:
            changes_html += f"<li><strong>{change['field']}</strong>: {change['old']} → {change['new']}</li>"

        subject = f"✏️ Booking Updated Alert - {booking.get('booking_code', '')}"

        html_content = f"""
        <h2>🏊 Booking Updated Alert</h2>

        <p><strong>Booking ID:</strong> {booking.get('booking_code', '')}</p>
        <p><strong>Swimmer:</strong> {booking.get('student', '')}</p>
        <p><strong>Owner:</strong> {booking.get('owner_name', '')}</p>

        <p><strong>Changes Made:</strong></p>
        <ul>
        {changes_html}
        </ul>
        """

        send_email(
            subject=subject,
            html_content=html_content
        )

    except Exception as exc:
        print(f"Booking update alert email failed: {exc}")


# --- Booking Deleted Email to Swimmer ---
def send_booking_deleted_email(booking):
    """Send booking deleted email to swimmer."""
    try:
        email = (booking.get('email') or '').strip()

        if not email:
            return

        subject = f"❌ Booking Cancelled - {booking.get('booking_code', 'SwimTrackPro')}"

        html_content = f"""
        <h2>❌ Booking Cancelled</h2>

        <p>Hello {booking.get('owner_name', 'Swimmer')},</p>

        <p>Your booking for <strong>{booking.get('student', '')}</strong> has been cancelled successfully.</p>

        <p><strong>Booking ID:</strong> {booking.get('booking_code', '')}</p>
        <p><strong>Package:</strong> {booking.get('package', '')}</p>
        <p><strong>Start Date:</strong> {booking.get('start_date', '')}</p>
        <p><strong>Time:</strong> {booking.get('time', '')}</p>

        <p>
        Book a new session:<br>
        <a href="https://swimtrackpro.onrender.com">https://swimtrackpro.onrender.com</a>
        </p>

        <p>Thank you for choosing SwimTrackPro 🏊</p>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=booking.get('owner_name', 'Swimmer')
        )

    except Exception as exc:
        print(f"Booking deleted email failed: {exc}")


# --- Booking Deleted Alert Email to Trainer/Admin ---
def send_booking_deleted_alert(booking):
    """Send booking deleted alert email to trainer/admin."""
    try:
        subject = f"❌ Booking Cancelled Alert - {booking.get('booking_code', '')}"

        html_content = f"""
        <h2>🏊 Booking Cancelled Alert</h2>

        <p><strong>Booking ID:</strong> {booking.get('booking_code', '')}</p>
        <p><strong>Swimmer:</strong> {booking.get('student', '')}</p>
        <p><strong>Owner:</strong> {booking.get('owner_name', '')}</p>
        <p><strong>Phone:</strong> {booking.get('owner_phone', '')}</p>
        <p><strong>Package:</strong> {booking.get('package', '')}</p>
        <p><strong>Start Date:</strong> {booking.get('start_date', '')}</p>
        <p><strong>Time:</strong> {booking.get('time', '')}</p>
        """

        send_email(
            subject=subject,
            html_content=html_content
        )

    except Exception as exc:
        print(f"Booking deleted alert email failed: {exc}")
