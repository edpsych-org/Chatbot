"""
Email utility for sending notifications via Brevo (Sendinblue) API
"""

import os
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "The EdPsych Practice")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "akshaytoni99@gmail.com")


class EmailService:
    """Email service using Brevo (Sendinblue) API"""

    def __init__(self, **kwargs):
        pass

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send an email via Brevo API"""
        try:
            if not BREVO_API_KEY:
                logger.info(f"[EMAIL MODE: DEV] Would send email to {to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body:\n{text_body or html_body[:200]}")
                return True

            payload = {
                "sender": {
                    "name": EMAIL_FROM_NAME,
                    "email": EMAIL_FROM_ADDRESS,
                },
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
            else:
                logger.error(f"Brevo API error {resp.status_code}: {resp.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


def send_assessment_assignment_email(
    parent_email: str,
    parent_name: str,
    student_name: str,
    psychologist_name: str,
    assessment_link: str,
    due_date: Optional[str] = None,
    notes: Optional[str] = None,
    email_service: Optional[EmailService] = None
) -> bool:
    """
    Send assessment assignment notification to parent

    Args:
        parent_email: Parent's email address
        parent_name: Parent's full name
        student_name: Student's full name
        psychologist_name: Psychologist's full name
        assessment_link: Link to the assessment
        due_date: Due date (optional)
        notes: Additional notes from psychologist (optional)
        email_service: EmailService instance (optional, creates default if None)

    Returns:
        bool: True if email sent successfully
    """
    if email_service is None:
        email_service = EmailService()

    subject = f"Assessment Assignment for {student_name}"

    # Build HTML email
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #4F46E5;
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border: 1px solid #e5e7eb;
                border-top: none;
            }}
            .info-box {{
                background-color: white;
                padding: 15px;
                border-left: 4px solid #4F46E5;
                margin: 15px 0;
            }}
            .button {{
                display: inline-block;
                background-color: #4F46E5;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>You're Invited to Complete an Assessment</h1>
        </div>
        <div class="content">
            <p>Dear {parent_name},</p>

            <p>A new assessment has been assigned for your child <strong>{student_name}</strong> by {psychologist_name}.</p>

            <div class="info-box">
                <h3 style="margin-top: 0;">Assessment Details</h3>
                <p><strong>Student:</strong> {student_name}</p>
                <p><strong>Assigned by:</strong> {psychologist_name}</p>
                {f'<p><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
            </div>

            <p>Please click the button below to access the assessment:</p>

            <div style="text-align: center;">
                <a href="{assessment_link}" class="button" style="display:inline-block;background-color:#4F46E5;color:#ffffff;padding:12px 30px;text-decoration:none;border-radius:6px;font-weight:bold;">Start Assessment</a>
            </div>

            <p style="font-size: 14px; color: #6b7280;">
                Or copy and paste this link into your browser:<br>
                <a href="{assessment_link}">{assessment_link}</a>
            </p>

            <p style="font-size: 13px; color: #6b7280; margin-top: 15px;">
                <strong>First time?</strong> You'll be asked to set up a password when you click the link above.<br>
                <strong>Returning user?</strong> You'll be logged in automatically.
            </p>
            <p style="font-size: 13px; color: #F59E0B;">
                ⏰ This link expires in 48 hours. If it expires, contact your psychologist for a new one.
            </p>

            <p>If you have any questions or concerns, please contact {psychologist_name}.</p>

            <p>Best regards,<br>EdPsych Assessment Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message from the EdPsych Assessment Platform.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    # Plain text fallback
    text_body = f"""
New Assessment Assignment

Dear {parent_name},

A new assessment has been assigned for your child {student_name} by {psychologist_name}.

Assessment Details:
- Student: {student_name}
- Assigned by: {psychologist_name}
{f'- Due Date: {due_date}' if due_date else ''}
{f'- Notes: {notes}' if notes else ''}

Access the assessment here:
{assessment_link}

First time? You'll be asked to set up a password when you click the link above.
Returning user? You'll be logged in automatically.

Note: This link expires in 48 hours. If it expires, contact your psychologist for a new one.

If you have any questions or concerns, please contact {psychologist_name}.

Best regards,
EdPsych Assessment Team

---
This is an automated message from the EdPsych Assessment Platform.
Please do not reply to this email.
    """

    return email_service.send_email(
        to_email=parent_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body
    )


def send_parent_invitation_email(
    parent_email: str,
    parent_name: str,
    student_name: str,
    psychologist_name: str,
    magic_link: str,
    email_service: Optional[EmailService] = None
) -> bool:
    """
    Send parent invitation with magic link for easy access

    Args:
        parent_email: Parent's email address
        parent_name: Parent's full name
        student_name: Student's full name
        psychologist_name: Psychologist's full name
        magic_link: One-click login link
        email_service: EmailService instance (optional)

    Returns:
        bool: True if email sent successfully
    """
    if email_service is None:
        email_service = EmailService()

    subject = f"Welcome to EdPsych Assessment Platform - {student_name}"

    # Build HTML email with magic link
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #10B981;
                color: white;
                padding: 30px 20px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border: 1px solid #e5e7eb;
                border-top: none;
            }}
            .welcome-box {{
                background-color: white;
                padding: 20px;
                border-radius: 6px;
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .button {{
                display: inline-block;
                background-color: #10B981;
                color: white;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
                font-weight: bold;
                font-size: 16px;
            }}
            .button:hover {{
                background-color: #059669;
            }}
            .info-item {{
                padding: 10px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .info-item:last-child {{
                border-bottom: none;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
            .highlight {{
                background-color: #DBEAFE;
                padding: 15px;
                border-left: 4px solid #3B82F6;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Welcome to EdPsych!</h1>
            <p style="margin: 0; font-size: 18px;">Access Your Child's Assessment Portal</p>
        </div>
        <div class="content">
            <p style="font-size: 16px;"><strong>Dear {parent_name},</strong></p>

            <p>You've been invited to access the Educational Psychology Assessment Platform for your child, <strong>{student_name}</strong>.</p>

            <div class="welcome-box">
                <h3 style="margin-top: 0; color: #10B981;">👋 Getting Started is Easy!</h3>
                <p>We've made it super simple - <strong>no password needed!</strong></p>
                <p>Just click the button below to instantly access your account:</p>

                <div style="text-align: center;">
                    <a href="{magic_link}" class="button">🔐 Access My Account</a>
                </div>

                <p style="font-size: 14px; color: #6b7280; margin-top: 20px;">
                    This link is secure and will log you in automatically. It's valid for 24 hours.
                </p>
            </div>

            <div class="highlight">
                <p style="margin: 0;"><strong>📱 What can you do?</strong></p>
                <ul style="margin: 10px 0;">
                    <li>View and complete assessments for {student_name}</li>
                    <li>Track assessment progress and results</li>
                    <li>Receive notifications about new assignments</li>
                    <li>Communicate with {psychologist_name}</li>
                </ul>
            </div>

            <div class="welcome-box">
                <h3 style="margin-top: 0;">📋 Account Information</h3>
                <div class="info-item">
                    <strong>Your Email:</strong> {parent_email}
                </div>
                <div class="info-item">
                    <strong>Student:</strong> {student_name}
                </div>
                <div class="info-item">
                    <strong>Assigned Psychologist:</strong> {psychologist_name}
                </div>
            </div>

            <p style="font-size: 14px; color: #6b7280; background-color: #FEF3C7; padding: 12px; border-radius: 4px; border-left: 4px solid #F59E0B;">
                <strong>💡 Tip:</strong> Bookmark the login page for easy access in the future. You'll receive a new secure link each time you need to log in.
            </p>

            <p>If you didn't expect this invitation or have any questions, please contact {psychologist_name}.</p>

            <p style="margin-top: 30px;">Best regards,<br><strong>EdPsych Assessment Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message from the EdPsych Assessment Platform.</p>
            <p>The login link expires in 24 hours for your security.</p>
            <p style="margin-top: 10px;">© 2026 EdPsych Assessment Platform</p>
        </div>
    </body>
    </html>
    """

    # Plain text fallback
    text_body = f"""
Welcome to EdPsych Assessment Platform!

Dear {parent_name},

You've been invited to access the Educational Psychology Assessment Platform for your child, {student_name}.

GETTING STARTED - NO PASSWORD NEEDED!
Click this link to instantly access your account:
{magic_link}

This secure link will log you in automatically and is valid for 24 hours.

WHAT CAN YOU DO?
- View and complete assessments for {student_name}
- Track assessment progress and results
- Receive notifications about new assignments
- Communicate with {psychologist_name}

ACCOUNT INFORMATION:
- Your Email: {parent_email}
- Student: {student_name}
- Assigned Psychologist: {psychologist_name}

TIP: Bookmark the login page for easy access. You'll receive a new secure link each time you need to log in.

If you didn't expect this invitation or have questions, please contact {psychologist_name}.

Best regards,
EdPsych Assessment Team

---
This is an automated message from the EdPsych Assessment Platform.
The login link expires in 24 hours for your security.
© 2026 EdPsych Assessment Platform
    """

    return email_service.send_email(
        to_email=parent_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body
    )
