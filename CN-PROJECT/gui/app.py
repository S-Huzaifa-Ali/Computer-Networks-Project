import customtkinter as ctk
from gui.theme import *
from gui.login_frame import LoginFrame
from gui.dashboard import Dashboard


class MailClientApp(ctk.CTk):
    """Root application window."""

    def __init__(self):
        super().__init__()

        self.title("SMTP Mail Client")
        self.geometry("1050x680")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=BG_DARK)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.current_frame = None
        self.show_login()

    def show_login(self):
        """Display the login screen."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = LoginFrame(self, on_login_success=self._on_login)
        self.current_frame.pack(fill="both", expand=True)

    def _on_login(self, email, password, host, port):
        """Called when login is successful - switch to dashboard."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = Dashboard(
            self, user_email=email, password=password,
            host=host, smtp_port=port
        )
        self.current_frame.pack(fill="both", expand=True)


def main():
    app = MailClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
