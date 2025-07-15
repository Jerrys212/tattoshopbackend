import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "sandbox.smtp.mailtrap.io")
        self.smtp_port = int(os.getenv("SMTP_PORT", "2525"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "74784f667ac226")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.app_name = os.getenv("APP_NAME", "Tattoo Shop")
        self.frontend_url = os.getenv("FRONTEND_URL", "")

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Enviar email usando SMTP"""
        try:
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.app_name} <{self.from_email}>"
            message["To"] = to_email

            # Agregar contenido HTML
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            print(f"Email enviado exitosamente a {to_email}")
            return True

        except Exception as e:
            print(f"Error enviando email a {to_email}: {e}")
            return False

    def send_confirmation_email(
        self, to_email: str, username: str, confirmation_token: str
    ) -> bool:
        """Enviar email de confirmación de cuenta"""
        confirmation_url = (
            f"{self.frontend_url}/confirm-email?token={confirmation_token}"
        )

        # Template HTML para el email
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Confirma tu cuenta</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 30px; background: #f8f9fa; }
                .button { 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background: #28a745; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Bienvenido a {{ app_name }}!</h1>
                </div>
                <div class="content">
                    <h2>Hola {{ username }},</h2>
                    <p>Gracias por registrarte en nuestra plataforma. Para completar tu registro, por favor confirma tu dirección de email haciendo clic en el botón de abajo:</p>
                    
                    <p style="text-align: center;">
                        <a href="{{ confirmation_url }}" class="button">Confirmar mi cuenta</a>
                    </p>
                    
                    <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                    <p><a href="{{ confirmation_url }}">{{ confirmation_url }}</a></p>
                    
                    <p><strong>Importante:</strong> Este enlace expirará en 24 horas por motivos de seguridad.</p>
                    
                    <p>Si no te registraste en nuestra plataforma, puedes ignorar este email.</p>
                </div>
                <div class="footer">
                    <p>Este es un email automático, por favor no respondas a este mensaje.</p>
                    <p>&copy; 2025 {{ app_name }}. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = html_template.render(
            app_name=self.app_name, username=username, confirmation_url=confirmation_url
        )

        subject = f"Confirma tu cuenta en {self.app_name}"
        return self.send_email(to_email, subject, html_content)

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Enviar email de bienvenida después de confirmar cuenta"""
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>¡Cuenta confirmada!</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #28a745; color: white; padding: 20px; text-align: center; }
                .content { padding: 30px; background: #f8f9fa; }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Cuenta confirmada exitosamente!</h1>
                </div>
                <div class="content">
                    <h2>¡Hola {{ username }}!</h2>
                    <p>Tu cuenta ha sido confirmada exitosamente. Ya puedes acceder a todas las funcionalidades de nuestra plataforma.</p>
                    
                    <p>¿Qué puedes hacer ahora?</p>
                    <ul>
                        <li>Acceder a tu perfil personal</li>
                        <li>Actualizar tu información</li>
                        <li>Cambiar tu contraseña cuando lo necesites</li>
                        <li>Explorar todas nuestras funcionalidades</li>
                    </ul>
                    
                    <p>Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos.</p>
                    
                    <p>¡Bienvenido a bordo!</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 {{ app_name }}. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = html_template.render(app_name=self.app_name, username=username)

        subject = f"¡Bienvenido a {self.app_name}! - Cuenta confirmada"
        return self.send_email(to_email, subject, html_content)
