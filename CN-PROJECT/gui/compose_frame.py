import customtkinter as ctk
from gui.theme import *


class ComposeFrame(ctk.CTkFrame):
    """Email composition form."""

    def __init__(self, parent, user_email, password, host, port,
                 reply_to=None, reply_subject=None, reply_body=None):
        super().__init__(parent, fg_color=BG_DARK)

        self.user_email = user_email
        self.password = password
        self.host = host
        self.port = port

        self.reply_to = reply_to
        self.reply_subject = reply_subject
        self.reply_body = reply_body

        self._build_ui()

    def _build_ui(self):
        title = "  Reply" if self.reply_to else "  Compose Email"
        header = ctk.CTkLabel(
            self, text=title,
            font=FONT_HEADING, text_color=TEXT_PRIMARY, anchor="w"
        )
        header.pack(fill="x", padx=PADDING, pady=(PADDING, 8))

        form = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        form.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        from_frame = ctk.CTkFrame(form, fg_color="transparent")
        from_frame.pack(fill="x", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            from_frame, text="From:", font=FONT_BODY,
            text_color=TEXT_SECONDARY, width=80, anchor="e"
        ).pack(side="left")

        ctk.CTkLabel(
            from_frame, text=self.user_email, font=FONT_BODY,
            text_color=ACCENT_BLUE
        ).pack(side="left", padx=(10, 0))

        to_frame = ctk.CTkFrame(form, fg_color="transparent")
        to_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(
            to_frame, text="To:", font=FONT_BODY,
            text_color=TEXT_SECONDARY, width=80, anchor="e"
        ).pack(side="left")

        self.to_entry = ctk.CTkEntry(
            to_frame, height=38,
            placeholder_text="recipient@gmail.com",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=FONT_BODY
        )
        self.to_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

        if self.reply_to:
            self.to_entry.insert(0, self.reply_to)

        subj_frame = ctk.CTkFrame(form, fg_color="transparent")
        subj_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(
            subj_frame, text="Subject:", font=FONT_BODY,
            text_color=TEXT_SECONDARY, width=80, anchor="e"
        ).pack(side="left")

        self.subject_entry = ctk.CTkEntry(
            subj_frame, height=38,
            placeholder_text="Email subject",
            fg_color=BG_INPUT, border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY, font=FONT_BODY
        )
        self.subject_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

        if self.reply_subject:
            prefix = "" if self.reply_subject.startswith("Re:") else "Re: "
            self.subject_entry.insert(0, f"{prefix}{self.reply_subject}")

        sep = ctk.CTkFrame(form, fg_color=BORDER_COLOR, height=1)
        sep.pack(fill="x", padx=20, pady=10)

        self.body_text = ctk.CTkTextbox(
            form, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            font=FONT_BODY, border_color=BORDER_COLOR,
            border_width=1, corner_radius=6, wrap="word"
        )
        self.body_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        if self.reply_body:
            quoted = "\n".join(f"> {line}" for line in self.reply_body.split("\n"))
            self.body_text.insert("1.0", f"\n\n--- Original Message ---\n{quoted}")
            self.body_text.mark_set("insert", "1.0")  
            
        bottom = ctk.CTkFrame(form, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 20))

        self.status_label = ctk.CTkLabel(
            bottom, text="", font=FONT_SMALL, text_color=TEXT_SECONDARY
        )
        self.status_label.pack(side="left")

        self.send_btn = ctk.CTkButton(
            bottom, text="Send Email", width=150, height=40,
            fg_color=ACCENT_BLUE_DIM, hover_color=ACCENT_BLUE,
            text_color="white", font=FONT_BUTTON,
            corner_radius=6, command=self._send_email
        )
        self.send_btn.pack(side="right")

        clear_btn = ctk.CTkButton(
            bottom, text="Clear", width=90, height=40,
            fg_color=BG_HOVER, hover_color=BORDER_COLOR,
            text_color=TEXT_SECONDARY, font=FONT_BODY,
            corner_radius=6, command=self._clear_form
        )
        clear_btn.pack(side="right", padx=(0, 10))

    def _send_email(self):
        """Send the composed email via SMTP client."""
        recipient = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", "end").strip()

        if not recipient:
            self._set_status("Please enter a recipient", ACCENT_RED)
            return
        if "@" not in recipient:
            self._set_status("Recipient must include domain (e.g. ahmed.raza@gmail.com)", ACCENT_RED)
            return
        if not subject:
            self._set_status("Please enter a subject", ACCENT_RED)
            return
        if not body:
            self._set_status("Please enter a message body", ACCENT_RED)
            return

        self.send_btn.configure(state="disabled", text="Sending...")
        self._set_status("Connecting to server...", TEXT_SECONDARY)
        self.update()

        from client.smtp_client import SmtpClient

        client = SmtpClient(host=self.host, port=self.port)
        try:
            if not client.connect():
                self._set_status("Could not connect to server", ACCENT_RED)
                return

            client.ehlo()
            auth_ok, auth_msg = client.authenticate(self.user_email, self.password)
            if not auth_ok:
                self._set_status("Authentication failed", ACCENT_RED)
                return

            success, msg = client.send_mail(self.user_email, recipient, subject, body)
            client.quit()

            if success:
                self._set_status("Email sent successfully!", ACCENT_GREEN)
                self._clear_form()
            else:
                self._set_status(f"Failed: {msg}", ACCENT_RED)

        except Exception as e:
            self._set_status(f"Error: {str(e)[:60]}", ACCENT_RED)
        finally:
            self.send_btn.configure(state="normal", text="Send Email")

    def _clear_form(self):
        """Reset all form fields."""
        self.to_entry.delete(0, "end")
        self.subject_entry.delete(0, "end")
        self.body_text.delete("1.0", "end")

    def _set_status(self, message, color=TEXT_SECONDARY):
        """Update the status label."""
        self.status_label.configure(text=message, text_color=color)
