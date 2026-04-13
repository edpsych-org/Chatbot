"""
Email utility for sending notifications via Brevo (Sendinblue) API.

Branded for The Ed Psych Practice — teal (#00acb6) chrome with red
(#e61844) call-to-action buttons. The phrasing adapts to the
recipient's relationship to the student:
    "Mother" / "Father" / "Guardian" → "your child {student}"
    "School" / school-role users      → "the student {student}"
    Anything else                     → "the student {student}"
"""

import os
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "The Ed Psych Practice")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@theedpsych.com")

# Default magic link expiry the rest of the codebase uses (config.MAGIC_LINK_EXPIRY_HOURS)
DEFAULT_LINK_EXPIRY_HOURS = 48

# Brand palette — match frontend tailwind tokens
COLOR_TEAL = "#00acb6"
COLOR_TEAL_DARK = "#0c888e"
COLOR_TEAL_TINT = "#e6f7f8"
COLOR_RED = "#e61844"
COLOR_RED_DARK = "#cf0627"
COLOR_INK = "#333333"
COLOR_MUTED = "#737373"
COLOR_HERO = "#eeeeee"
COLOR_BORDER = "#dedede"


# ---------------------------------------------------------------------------
# Phrasing helpers
# ---------------------------------------------------------------------------
_CHILD_RELATIONSHIPS = {"mother", "father", "parent", "guardian", "step-mother", "step-father", "stepmother", "stepfather", "carer", "caregiver"}


def _possessive_for(relationship_type: Optional[str]) -> str:
    """Return the right possessive phrase for the recipient's relationship."""
    rel = (relationship_type or "").strip().lower()
    if rel in _CHILD_RELATIONSHIPS:
        return "your child"
    if rel == "school":
        return "the student"
    # Guardian-ish but unknown — be neutral
    return "the student"


def _intro_line(relationship_type: Optional[str], student_name: str) -> str:
    """First line of the email body, adapted to the relationship."""
    return f"A new assessment has been assigned for {_possessive_for(relationship_type)} <strong>{student_name}</strong>."


# ---------------------------------------------------------------------------
# Email service
# ---------------------------------------------------------------------------
class EmailService:
    """Email service using Brevo (Sendinblue) API."""

    def __init__(self, **kwargs):
        pass

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send an email via Brevo API."""
        try:
            if not BREVO_API_KEY:
                logger.info(f"[EMAIL MODE: DEV] Would send email to {to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body:\n{text_body or html_body[:200]}")
                return True

            payload = {
                "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM_ADDRESS},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_body,
            }
            if text_body:
                payload["textContent"] = text_body

            resp = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=10,
            )

            if resp.status_code in (200, 201):
                logger.info(f"Email sent successfully to {to_email} via Brevo")
                return True
            logger.error(f"Brevo API error {resp.status_code}: {resp.text}")
            return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


# ---------------------------------------------------------------------------
# Assessment assignment email
# ---------------------------------------------------------------------------
def send_assessment_assignment_email(
    parent_email: str,
    parent_name: str,
    student_name: str,
    psychologist_name: str,
    assessment_link: str,
    due_date: Optional[str] = None,
    notes: Optional[str] = None,
    email_service: Optional[EmailService] = None,
    relationship_type: Optional[str] = None,
    expiry_hours: int = DEFAULT_LINK_EXPIRY_HOURS,
) -> bool:
    """Notify a guardian (parent or school) that an assessment has been assigned.

    `psychologist_name` is the name of the user who created the assignment
    (admin or psychologist). The variable name is kept for backwards
    compatibility with existing callers.
    """
    if email_service is None:
        email_service = EmailService()

    subject = f"Assessment invitation for {student_name}"

    intro = _intro_line(relationship_type, student_name)
    role_label = (relationship_type or "Guardian").strip() or "Guardian"
    contact_phrase = (
        f"If you have any questions, please contact {psychologist_name}."
        if psychologist_name
        else "If you have any questions, please contact The Ed Psych Practice."
    )

    due_html = (
        f'<p style="margin:6px 0;"><strong>Due:</strong> {due_date}</p>' if due_date else ""
    )
    notes_html = (
        f'<p style="margin:6px 0;"><strong>Notes:</strong> {notes}</p>' if notes else ""
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: {COLOR_INK}; max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; }}
            .header {{ background-color: {COLOR_TEAL}; color: #ffffff; padding: 24px; border-radius: 4px 4px 0 0; text-align: center; }}
            .header h1 {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 400; }}
            .header p   {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
            .content   {{ background-color: #ffffff; padding: 28px; border: 1px solid {COLOR_BORDER}; border-top: none; border-radius: 0 0 4px 4px; }}
            .info-box  {{ background-color: {COLOR_TEAL_TINT}; padding: 16px 18px; border-left: 3px solid {COLOR_TEAL}; margin: 18px 0; border-radius: 3px; }}
            .info-box h3 {{ margin: 0 0 6px; font-family: Georgia, serif; font-size: 16px; color: {COLOR_TEAL_DARK}; font-weight: 400; }}
            .button {{ display: inline-block; background-color: {COLOR_RED}; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 4px; margin: 18px 0; font-weight: 600; }}
            .footer {{ text-align: center; color: {COLOR_MUTED}; font-size: 11px; margin-top: 24px; padding-top: 16px; border-top: 1px solid {COLOR_BORDER}; }}
            .pill   {{ display: inline-block; padding: 2px 10px; background: {COLOR_TEAL_TINT}; color: {COLOR_TEAL_DARK}; border-radius: 12px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
            .expiry {{ background: #fff8e6; border-left: 3px solid #d4a017; padding: 10px 14px; margin: 16px 0; font-size: 13px; color: #6b5012; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>The Ed Psych Practice</h1>
            <p>Assessment invitation</p>
        </div>
        <div class="content">
            <p>Dear {parent_name},</p>

            <p>{intro}</p>

            <div class="info-box">
                <h3>Assessment details</h3>
                <p style="margin:6px 0;"><strong>Student:</strong> {student_name}</p>
                <p style="margin:6px 0;"><strong>You're invited as:</strong> <span class="pill">{role_label}</span></p>
                <p style="margin:6px 0;"><strong>Assigned by:</strong> {psychologist_name}</p>
                {due_html}
                {notes_html}
            </div>

            <p>Click the button below to begin:</p>

            <div style="text-align: center;">
                <a href="{assessment_link}" class="button" style="display:inline-block;background-color:{COLOR_RED};color:#ffffff;padding:12px 28px;text-decoration:none;border-radius:4px;font-weight:600;">Start assessment</a>
            </div>

            <p style="font-size: 13px; color: {COLOR_MUTED};">
                Or copy this link into your browser:<br>
                <a href="{assessment_link}" style="color:{COLOR_TEAL_DARK}; word-break: break-all;">{assessment_link}</a>
            </p>

            <p style="font-size: 13px; color: {COLOR_MUTED}; margin-top: 14px;">
                <strong>First time using the platform?</strong> You'll be asked to set a password when you click the link.<br>
                <strong>Returning?</strong> You'll be signed in automatically.
            </p>

            <div class="expiry">
                ⏰ This invitation link expires in {expiry_hours} hours. If it expires, ask whoever assigned the assessment to send a new one.
            </div>

            <p>{contact_phrase}</p>

            <p>Best regards,<br>The Ed Psych Practice</p>
        </div>
        <div class="footer">
            <p>This is an automated message from The Ed Psych Practice.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_intro = (
        f"A new assessment has been assigned for {_possessive_for(relationship_type)} {student_name}"
    )
    text_body = f"""
The Ed Psych Practice — Assessment invitation

Dear {parent_name},

{text_intro} by {psychologist_name}.

Assessment details:
- Student: {student_name}
- You're invited as: {role_label}
- Assigned by: {psychologist_name}
{f'- Due: {due_date}' if due_date else ''}
{f'- Notes: {notes}' if notes else ''}

Begin the assessment here:
{assessment_link}

First time? You'll be asked to set a password when you open the link.
Returning? You'll be signed in automatically.

Note: this link expires in {expiry_hours} hours. If it expires, ask {psychologist_name} for a new one.

{contact_phrase}

Best regards,
The Ed Psych Practice

---
This is an automated message from The Ed Psych Practice. Please do not reply to this email.
    """.strip()

    return email_service.send_email(
        to_email=parent_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )


# ---------------------------------------------------------------------------
# Parent invitation email (used by /student-guardians/invite-parent)
# ---------------------------------------------------------------------------
def send_parent_invitation_email(
    parent_email: str,
    parent_name: str,
    student_name: str,
    psychologist_name: str,
    magic_link: str,
    email_service: Optional[EmailService] = None,
    relationship_type: Optional[str] = None,
    expiry_hours: int = DEFAULT_LINK_EXPIRY_HOURS,
) -> bool:
    """Welcome a newly-linked guardian with a magic link login."""
    if email_service is None:
        email_service = EmailService()

    subject = f"Welcome to The Ed Psych Practice — {student_name}"
    role_label = (relationship_type or "Guardian").strip() or "Guardian"
    possessive = _possessive_for(relationship_type)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: {COLOR_INK}; max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff; }}
            .header {{ background-color: {COLOR_TEAL}; color: #ffffff; padding: 28px 24px; border-radius: 4px 4px 0 0; text-align: center; }}
            .header h1 {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 400; }}
            .header p  {{ margin: 8px 0 0; font-size: 14px; opacity: 0.92; }}
            .content {{ background-color: #ffffff; padding: 28px; border: 1px solid {COLOR_BORDER}; border-top: none; border-radius: 0 0 4px 4px; }}
            .welcome-box {{ background-color: {COLOR_TEAL_TINT}; padding: 20px; border-radius: 4px; margin: 18px 0; border-left: 3px solid {COLOR_TEAL}; }}
            .welcome-box h3 {{ margin-top: 0; color: {COLOR_TEAL_DARK}; font-family: Georgia, serif; font-weight: 400; font-size: 17px; }}
            .button {{ display: inline-block; background-color: {COLOR_RED}; color: #ffffff; padding: 14px 36px; text-decoration: none; border-radius: 4px; margin: 18px 0; font-weight: 600; font-size: 15px; }}
            .info-item {{ padding: 8px 0; border-bottom: 1px solid {COLOR_BORDER}; font-size: 14px; }}
            .info-item:last-child {{ border-bottom: none; }}
            .footer {{ text-align: center; color: {COLOR_MUTED}; font-size: 11px; margin-top: 24px; padding-top: 16px; border-top: 1px solid {COLOR_BORDER}; }}
            .tip {{ background-color: #fff8e6; border-left: 3px solid #d4a017; padding: 10px 14px; margin: 18px 0; font-size: 13px; color: #6b5012; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to The Ed Psych Practice</h1>
            <p>Your secure access to {possessive} {student_name}'s assessment portal</p>
        </div>
        <div class="content">
            <p style="font-size: 15px;"><strong>Dear {parent_name},</strong></p>

            <p>You've been invited to access the Educational Psychology Assessment Portal for <strong>{student_name}</strong>.</p>

            <div class="welcome-box">
                <h3>Get started — no password needed</h3>
                <p>Click the button below to sign in instantly:</p>

                <div style="text-align: center;">
                    <a href="{magic_link}" class="button" style="display:inline-block;background-color:{COLOR_RED};color:#ffffff;padding:14px 36px;text-decoration:none;border-radius:4px;font-weight:600;">Access my account</a>
                </div>

                <p style="font-size: 13px; color: {COLOR_MUTED}; margin-top: 14px;">
                    The link is secure and signs you in automatically. It is valid for {expiry_hours} hours.
                </p>
            </div>

            <div style="margin: 18px 0;">
                <p style="margin: 0 0 6px; font-weight: 600; color: {COLOR_INK};">What you can do here:</p>
                <ul style="margin: 6px 0; padding-left: 22px; color: {COLOR_INK};">
                    <li>Complete assessments for {student_name}</li>
                    <li>Track assessment progress</li>
                    <li>View finalised reports once they're ready</li>
                </ul>
            </div>

            <div class="welcome-box" style="background:#ffffff; border-left-color:{COLOR_BORDER};">
                <h3 style="color:{COLOR_INK};">Account information</h3>
                <div class="info-item"><strong>Your email:</strong> {parent_email}</div>
                <div class="info-item"><strong>Student:</strong> {student_name}</div>
                <div class="info-item"><strong>You're linked as:</strong> {role_label}</div>
                <div class="info-item"><strong>Invited by:</strong> {psychologist_name}</div>
            </div>

            <div class="tip">
                💡 You'll receive a fresh secure link each time you need to sign in — no password to remember.
            </div>

            <p>If you didn't expect this invitation, please contact {psychologist_name}.</p>

            <p style="margin-top: 24px;">Best regards,<br><strong>The Ed Psych Practice</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message from The Ed Psych Practice.</p>
            <p>The login link expires in {expiry_hours} hours for your security.</p>
            <p style="margin-top: 8px;">© The Ed Psych Practice</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
The Ed Psych Practice — Welcome

Dear {parent_name},

You've been invited to access the Educational Psychology Assessment Portal for {student_name}.

GET STARTED — NO PASSWORD NEEDED
Click this secure link to sign in instantly:
{magic_link}

The link is valid for {expiry_hours} hours.

WHAT YOU CAN DO:
- Complete assessments for {student_name}
- Track assessment progress
- View finalised reports once they're ready

ACCOUNT INFORMATION:
- Your email: {parent_email}
- Student: {student_name}
- You're linked as: {role_label}
- Invited by: {psychologist_name}

You'll receive a fresh secure link each time you need to sign in — no password to remember.

If you didn't expect this invitation, please contact {psychologist_name}.

Best regards,
The Ed Psych Practice

---
This is an automated message. Please do not reply to this email.
The login link expires in {expiry_hours} hours for your security.
© The Ed Psych Practice
    """.strip()

    return email_service.send_email(
        to_email=parent_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
