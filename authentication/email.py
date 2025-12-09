import os
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from dotenv import load_dotenv
from authentication.token import create_verification_token

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: EmailStr, user_name: str):
    token = create_verification_token(email)
    
    domain = os.getenv("DOMAIN", "localhost:8000")
    verification_link = f"http://{domain}/verify?token={token}"
    print(f"DEBUG: Generated verification link: {verification_link}")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                padding: 10px 0;
                border-bottom: 1px solid #eeeeee;
            }}
            .header h2 {{
                color: #333333;
                margin: 0;
            }}
            .content {{
                padding: 20px;
                text-align: center;
                color: #555555;
            }}
            .content p {{
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #0275d8;
                color: #ffffff;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }}
            .btn:hover {{
                background-color: #025aa5;
            }}
            .footer {{
                text-align: center;
                padding-top: 20px;
                font-size: 12px;
                color: #999999;
                border-top: 1px solid #eeeeee;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>File Management System</h2>
            </div>
            <div class="content">
                <h3>Account Verification</h3>
                <p>Hi {user_name},</p>
                <p>Thanks for choosing File Management System. To complete your registration, please verify your email address by clicking the link below:</p>
                <a href="{verification_link}" class="btn">Click Link</a>
                <p style="margin-top: 20px; font-size: 14px;">If the button above doesn't work, copy and paste the following link into your browser:</p>
                <p style="font-size: 12px; color: #0275d8; word-break: break-all;">{verification_link}</p>
            </div>
            <div class="footer">
                <p>Please ignore this email if you did not register for File Management System.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="FileManagementSystem Account Verification Email",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
