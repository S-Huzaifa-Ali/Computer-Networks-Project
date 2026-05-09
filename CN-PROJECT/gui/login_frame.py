import os
import json
import customtkinter as ctk
from gui.theme import *


class LoginFrame(ctk.CTkFrame):
    """Login screen with email, password, and domain selector."""

    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color=BG_DARK)

        self.on_login_success = on_login_success
        self.saved_email_file = "data/last_login.json"
        self._build_ui()

    def _build_ui(self):
        """Construct the login form layout."""
        center_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(
            center_frame, text="SMTP Mail Client",
            font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY
        )
        title.pack(pady=(35, 5), padx=60)

        subtitle = ctk.CTkLabel(
            center_frame, text="Sign in to your account",
            font=FONT_BODY, text_color=TEXT_SECONDARY
        )
        subtitle.pack(pady=(0, 25))

        email_label = ctk.CTkLabel(
            center_frame, text="Email Address",
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w"
        )
        email_label.pack(padx=35, anchor="w")

        self.email_entry = ctk.CTkEntry(
            center_frame, width=340, height=42,
            placeholder_text="e.g. huzaifa@nu.edu.pk",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=FONT_BODY
        )
        self.email_entry.pack(padx=35, pady=(4, 14))

        last_email = self._load_last_email()
        if last_email:
            self.email_entry.insert(0, last_email)

        pass_label = ctk.CTkLabel(
            center_frame, text="Password",
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w"
        )
        pass_label.pack(padx=35, anchor="w")

        self.password_entry = ctk.CTkEntry(
            center_frame, width=340, height=42,
            placeholder_text="Enter password", show="•",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=FONT_BODY
        )
        self.password_entry.pack(padx=35, pady=(4, 14))

        server_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        server_frame.pack(padx=35, fill="x", pady=(0, 10))

        host_label = ctk.CTkLabel(
            server_frame, text="Server:", font=FONT_SMALL,
            text_color=TEXT_MUTED
        )
        host_label.pack(side="left")

        self.host_entry = ctk.CTkEntry(
            server_frame, width=150, height=32,
            fg_color=BG_INPUT, border_color=BORDER_SUBTLE,
            text_color=TEXT_SECONDARY, font=FONT_SMALL
        )
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(side="left", padx=(8, 6))

        self.port_entry = ctk.CTkEntry(
            server_frame, width=70, height=32,
            fg_color=BG_INPUT, border_color=BORDER_SUBTLE,
            text_color=TEXT_SECONDARY, font=FONT_SMALL
        )
        self.port_entry.insert(0, "2525")
        self.port_entry.pack(side="left")

        self.error_label = ctk.CTkLabel(
            center_frame, text="", font=FONT_SMALL,
            text_color=ACCENT_RED
        )
        self.error_label.pack(padx=35)

        self.login_btn = ctk.CTkButton(
            center_frame, text="Sign In", width=340, height=44,
            fg_color=ACCENT_BLUE_DIM, hover_color=ACCENT_BLUE,
            text_color="white", font=FONT_BUTTON,
            corner_radius=8, command=self._do_login
        )
        self.login_btn.pack(padx=35, pady=(10, 12))

        domain_info = ctk.CTkLabel(
            center_frame,
            text="Domains: nu.edu.pk • gmail.com • yahoo.com • hotmail.com • outlook.com",
            font=("Segoe UI", 10), text_color=TEXT_MUTED
        )
        domain_info.pack(pady=(0, 25), padx=25)

        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        """Attempt to log in with the entered credentials."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        host = self.host_entry.get().strip()

        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            self._show_error("Invalid port number")
            return

        if not email or not password:
            self._show_error("Please enter email and password")
            return

        if "@" not in email:
            self._show_error("Email must include domain (e.g. huzaifa@nu.edu.pk)")
            return

        self.login_btn.configure(state="disabled", text="Connecting...")
        self.error_label.configure(text="")
        self.update()

        from client.smtp_client import SmtpClient

        client = SmtpClient(host=host, port=port)
        if not client.connect():
            self._show_error("Could not connect to server. Is it running?")
            self.login_btn.configure(state="normal", text="Sign In")
            return

        try:
            client.ehlo()
            success, message = client.authenticate(email, password)
            client.quit()

            if success:
                self._save_last_email(email)
                self.on_login_success(email, password, host, port)
            else:
                self._show_error("Invalid email or password")
        except Exception as e:
            self._show_error(f"Connection error: {str(e)[:50]}")
        finally:
            self.login_btn.configure(state="normal", text="Sign In")

    def _show_error(self, message):
        """Display an error message below the form."""
        self.error_label.configure(text=message)

    def _load_last_email(self):
        try:
            if os.path.exists(self.saved_email_file):
                with open(self.saved_email_file, "r") as f:
                    data = json.load(f)
                    return data.get("last_email", "")
        except Exception:
            pass
        return ""

    def _save_last_email(self, email):
        try:
            os.makedirs(os.path.dirname(self.saved_email_file), exist_ok=True)
            with open(self.saved_email_file, "w") as f:
                json.dump({"last_email": email}, f)
        except Exception:
            pass
