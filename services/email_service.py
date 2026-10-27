"""
Brevo & SMTP Email Service for SwimTrackPro
--------------------------------------------
Provides transactional email notifications for:
- Booking Confirmation (to Swimmer)
- New Booking Alert (to Admin)
- Booking Deleted / Cancelled (to Swimmer)
- Booking Deleted Alert (to Admin)
- Payment Reminder (to Swimmer)
- Package Completion (to Swimmer)

Supports:
1. Brevo REST API (direct HTTPS via urllib.request - no external SDK dependency)
2. Optional SMTP fallback (Gmail / Brevo relay)
"""

import os
import json
import smtplib
import threading
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from config import (
        BREVO_API_KEY as CFG_BREVO_KEY,
        BREVO_SENDER_EMAIL as CFG_SENDER_EMAIL,
        BREVO_SENDER_NAME as CFG_SENDER_NAME,
        ADMIN_ALERT_EMAIL as CFG_ADMIN_EMAIL,
        SMTP_EMAIL as CFG_SMTP_EMAIL,
        SMTP_PASSWORD as CFG_SMTP_PASSWORD,
    )
except ImportError:
    CFG_BREVO_KEY = ""
    CFG_SENDER_EMAIL = "swimtrackpro.updates@gmail.com"
    CFG_SENDER_NAME = "SwimTrackPro"
    CFG_ADMIN_EMAIL = "swimtrackpro.updates@gmail.com"
    CFG_SMTP_EMAIL = ""
    CFG_SMTP_PASSWORD = ""


def get_email_config():
    api_key = os.getenv("BREVO_API_KEY") or CFG_BREVO_KEY or ""
    sender_email = os.getenv("BREVO_SENDER_EMAIL") or CFG_SENDER_EMAIL or "swimtrackpro.updates@gmail.com"
    sender_name = os.getenv("BREVO_SENDER_NAME") or CFG_SENDER_NAME or "SwimTrackPro"
    admin_email = os.getenv("ADMIN_ALERT_EMAIL") or CFG_ADMIN_EMAIL or "swimtrackpro.updates@gmail.com"
    smtp_user = os.getenv("SMTP_EMAIL") or CFG_SMTP_EMAIL or ""
    smtp_pass = os.getenv("SMTP_PASSWORD") or CFG_SMTP_PASSWORD or ""
    return {
        "api_key": api_key.strip(),
        "sender_email": sender_email.strip(),
        "sender_name": sender_name.strip(),
        "admin_email": admin_email.strip(),
        "smtp_user": smtp_user.strip(),
        "smtp_pass": smtp_pass.strip()
    }


def send_email_sync(subject, html_content, to_email=None, to_name="Admin"):
    """
    Send transactional email synchronously.
    Tries Brevo REST API first; falls back to standard SMTP if configured.
    """
    cfg = get_email_config()
    recipient_email = (to_email or cfg["admin_email"]).strip()

    if not recipient_email:
        print("Email skipped: No recipient email specified.")
        return False

    # 1. Attempt Brevo REST API
    if cfg["api_key"]:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": cfg["api_key"],
            "content-type": "application/json",
            "User-Agent": "SwimTrackPro/2.0"
        }
        payload = {
            "sender": {
                "name": cfg["sender_name"],
                "email": cfg["sender_email"]
            },
            "to": [
                {
                    "email": recipient_email,
                    "name": to_name or "Recipient"
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as response:
                status_code = response.getcode()
                if 200 <= status_code < 300:
                    print(f"Brevo email sent successfully to {recipient_email} (Status {status_code}).")
                    return True
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")
            if "authorised_ips" in err_body or "unrecognised IP address" in err_body:
                print(f"Brevo API Error (401 - IP Whitelist Restriction): Brevo rejected IP address. Please visit https://app.brevo.com/security/authorised_ips to disable Authorized IP restrictions or add your IP.")
            else:
                print(f"Brevo API error (HTTP {exc.code}): {err_body}")
        except Exception as exc:
            print(f"Brevo REST connection error: {exc}")

    # 2. Fallback to SMTP if SMTP credentials are provided
    if cfg["smtp_user"] and cfg["smtp_pass"]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{cfg['sender_name']} <{cfg['smtp_user']}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html"))

            # Determine SMTP host: Brevo relay or Gmail
            if "brevo" in cfg["smtp_user"].lower():
                smtp_host = "smtp-relay.brevo.com"
                smtp_port = 587
            else:
                smtp_host = "smtp.gmail.com"
                smtp_port = 587

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(cfg["smtp_user"], cfg["smtp_pass"])
                server.sendmail(cfg["smtp_user"], [recipient_email], msg.as_string())
            print(f"SMTP email sent successfully to {recipient_email} via {smtp_host}.")
            return True
        except Exception as smtp_exc:
            print(f"SMTP fallback error: {smtp_exc}")

    if not cfg["api_key"] and not cfg["smtp_user"]:
        print("Email skipped: Neither BREVO_API_KEY nor SMTP credentials are configured.")
    return False


def send_email(subject, html_content, to_email=None, to_name="Admin"):
    """
    Send an email asynchronously in a background thread so web requests are not blocked.
    """
    thread = threading.Thread(
        target=send_email_sync,
        args=(subject, html_content, to_email, to_name)
    )
    thread.daemon = True
    thread.start()
    return True


# ==========================================
# Specialized Application Email Handlers
# ==========================================

def send_booking_confirmation_email(booking):
    """Send booking confirmation email to swimmer/owner."""
    try:
        email = (booking.get("email") or "").strip()
        if not email:
            print(f"Booking confirmation skipped: No email provided for {booking.get('student', 'swimmer')}.")
            return

        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name") or student or "Swimmer"
        start_date = booking.get("start_date") or booking.get("date", "")
        time_slot = booking.get("time", "")
        package = booking.get("package", "Standard")
        fee = booking.get("fee", 0)
        payment_status = booking.get("payment_request") or booking.get("status") or "Pending"

        subject = f"🏊 Booking Confirmed - {booking_code}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1e293b; line-height: 1.6;">
            <div style="background: linear-gradient(135deg, #06b6d4, #0284c7); padding: 24px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">🏊 Booking Confirmation</h1>
                <p style="color: #e0f2fe; margin: 6px 0 0 0; font-size: 14px;">Fear less. Swim more with SwimTrackPro.</p>
            </div>
            
            <div style="background: #ffffff; padding: 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                <p style="font-size: 16px;">Hello <strong>{owner_name}</strong>,</p>
                <p>Your swimming session booking for <strong>{student}</strong> has been successfully registered.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; width: 38%; color: #64748b;">Booking ID</td>
                        <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">{booking_code}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Swimmer</td>
                        <td style="padding: 10px 14px;">{student}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Package</td>
                        <td style="padding: 10px 14px;">{package}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Start Date</td>
                        <td style="padding: 10px 14px;">{start_date}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Time Slot</td>
                        <td style="padding: 10px 14px;">{time_slot}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Fee</td>
                        <td style="padding: 10px 14px; font-weight: bold;">₹{fee}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Payment Status</td>
                        <td style="padding: 10px 14px;">{payment_status}</td>
                    </tr>
                </table>

                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://swimtrackpro.onrender.com/my-bookings" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; display: inline-block;">
                        View My Bookings
                    </a>
                </div>

                <p style="color: #64748b; font-size: 13px; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                    Need assistance or have schedule changes? Contact your coach or reply to this email.<br>
                    <strong>SwimTrackPro Academy</strong>
                </p>
            </div>
        </div>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=owner_name
        )
    except Exception as exc:
        print(f"Booking confirmation email failed: {exc}")


def send_booking_alert_email(booking):
    """Send new booking alert email to administrator."""
    try:
        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name", "")
        phone = booking.get("owner_phone", "")
        start_date = booking.get("start_date") or booking.get("date", "")
        time_slot = booking.get("time", "")
        package = booking.get("package", "Standard")
        fee = booking.get("fee", 0)
        coach = booking.get("trainer_username") or "Unassigned"

        subject = f"🏊 New Booking Alert - {booking_code} ({student})"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            <h2 style="color: #0284c7;">🏊 New Booking Alert</h2>
            <p>A new session booking has been created on SwimTrackPro.</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #cbd5e1;">
                <tr><td style="width: 35%; background: #f1f5f9;"><strong>Booking Code</strong></td><td>{booking_code}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Swimmer</strong></td><td>{student}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Booked By</strong></td><td>{owner_name}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Phone</strong></td><td>{phone}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Package</strong></td><td>{package}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Start Date</strong></td><td>{start_date}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Time</strong></td><td>{time_slot}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Fee</strong></td><td>₹{fee}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Assigned Coach</strong></td><td>{coach}</td></tr>
            </table>
        </div>
        """

        send_email(subject=subject, html_content=html_content)
    except Exception as exc:
        print(f"Booking alert email failed: {exc}")


def send_booking_deleted_email(booking):
    """Send booking cancellation/deletion email to swimmer/owner."""
    try:
        email = (booking.get("email") or "").strip()
        if not email:
            print(f"Booking deleted email skipped: No email provided for {booking.get('student', 'swimmer')}.")
            return

        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name") or student or "Swimmer"
        start_date = booking.get("start_date") or booking.get("date", "")
        time_slot = booking.get("time", "")
        package = booking.get("package", "Standard")

        subject = f"❌ Booking Cancelled - {booking_code}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1e293b; line-height: 1.6;">
            <div style="background: linear-gradient(135deg, #ef4444, #b91c1c); padding: 24px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">❌ Booking Cancelled</h1>
                <p style="color: #fee2e2; margin: 6px 0 0 0; font-size: 14px;">SwimTrackPro Session Update</p>
            </div>
            
            <div style="background: #ffffff; padding: 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                <p style="font-size: 16px;">Hello <strong>{owner_name}</strong>,</p>
                <p>Your swimming session booking for <strong>{student}</strong> has been cancelled.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; width: 38%; color: #64748b;">Booking ID</td>
                        <td style="padding: 10px 14px; font-weight: bold; color: #ef4444;">{booking_code}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Swimmer</td>
                        <td style="padding: 10px 14px;">{student}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Package</td>
                        <td style="padding: 10px 14px;">{package}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Scheduled Date</td>
                        <td style="padding: 10px 14px;">{start_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; font-weight: bold; color: #64748b;">Time Slot</td>
                        <td style="padding: 10px 14px;">{time_slot}</td>
                    </tr>
                </table>

                <div style="text-align: center; margin: 25px 0;">
                    <a href="https://swimtrackpro.onrender.com" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Book a New Session
                    </a>
                </div>

                <p style="color: #64748b; font-size: 13px; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                    If this cancellation was unexpected, please contact your coach or reply directly to this email.<br>
                    <strong>SwimTrackPro Academy</strong>
                </p>
            </div>
        </div>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=owner_name
        )
    except Exception as exc:
        print(f"Booking deleted email failed: {exc}")


def send_booking_deleted_alert(booking):
    """Send booking deletion alert email to administrator."""
    try:
        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name", "")
        phone = booking.get("owner_phone", "")
        start_date = booking.get("start_date") or booking.get("date", "")
        time_slot = booking.get("time", "")
        package = booking.get("package", "Standard")

        subject = f"❌ Booking Cancelled Alert - {booking_code} ({student})"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            <h2 style="color: #ef4444;">❌ Booking Cancelled Alert</h2>
            <p>The following booking has been removed/cancelled from SwimTrackPro:</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #cbd5e1;">
                <tr><td style="width: 35%; background: #f1f5f9;"><strong>Booking Code</strong></td><td>{booking_code}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Swimmer</strong></td><td>{student}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Owner</strong></td><td>{owner_name}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Phone</strong></td><td>{phone}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Package</strong></td><td>{package}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Start Date</strong></td><td>{start_date}</td></tr>
                <tr><td style="background: #f1f5f9;"><strong>Time</strong></td><td>{time_slot}</td></tr>
            </table>
        </div>
        """

        send_email(subject=subject, html_content=html_content)
    except Exception as exc:
        print(f"Booking deleted alert email failed: {exc}")


def send_payment_reminder_email(booking):
    """Send payment reminder email when package is nearing completion."""
    try:
        email = (booking.get("email") or "").strip()
        if not email:
            return

        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name") or student or "Swimmer"
        package = booking.get("package", "")
        fee = booking.get("fee", 0)
        remaining = booking.get("remaining_classes", 0)

        subject = f"💰 Payment Reminder - {booking_code}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            <h2 style="color: #f59e0b;">💰 Payment Reminder</h2>
            <p>Hello {owner_name},</p>
            <p>Your swimming package for <strong>{student}</strong> is in progress and payment is pending.</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #cbd5e1;">
                <tr><td style="width: 40%; background: #f8fafc;"><strong>Booking ID</strong></td><td>{booking_code}</td></tr>
                <tr><td style="background: #f8fafc;"><strong>Package</strong></td><td>{package}</td></tr>
                <tr><td style="background: #f8fafc;"><strong>Remaining Sessions</strong></td><td>{remaining}</td></tr>
                <tr><td style="background: #f8fafc;"><strong>Amount Due</strong></td><td><strong>₹{fee}</strong></td></tr>
            </table>
            <br>
            <p><a href="https://swimtrackpro.onrender.com/my-bookings" style="background: #0284c7; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 6px;">Pay Now on SwimTrackPro</a></p>
        </div>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=owner_name
        )
    except Exception as exc:
        print(f"Payment reminder email failed: {exc}")


def send_package_completion_email(booking):
    """Send package completion email when all sessions are completed."""
    try:
        email = (booking.get("email") or "").strip()
        if not email:
            return

        booking_code = booking.get("booking_code") or booking.get("id", "")
        student = booking.get("student") or booking.get("student_name", "")
        owner_name = booking.get("owner_name") or student or "Swimmer"
        package = booking.get("package", "")
        total_classes = booking.get("total_classes", 0)

        subject = f"🎉 Package Completed - {booking_code}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            <h2 style="color: #10b981;">🎉 Package Completed!</h2>
            <p>Congratulations {owner_name}!</p>
            <p>The swimming package for <strong>{student}</strong> has been successfully completed ({total_classes} sessions).</p>
            <p>Ready for the next level? Continue your swimming journey:</p>
            <p><a href="https://swimtrackpro.onrender.com" style="background: #10b981; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 6px;">Book Your Next Package</a></p>
        </div>
        """

        send_email(
            subject=subject,
            html_content=html_content,
            to_email=email,
            to_name=owner_name
        )
    except Exception as exc:
        print(f"Package completion email failed: {exc}")
