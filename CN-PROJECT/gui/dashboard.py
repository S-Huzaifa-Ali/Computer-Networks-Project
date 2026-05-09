import customtkinter as ctk
import threading
import time
import json
from gui.theme import *
from gui.inbox_frame import InboxFrame
from gui.sent_frame import SentFrame
from gui.compose_frame import ComposeFrame
from client.retrieval_client import RetrievalClient


class Dashboard(ctk.CTkFrame):
    """Main dashboard with sidebar navigation and swappable content panels."""

    def __init__(self, parent, user_email, password, host, smtp_port):
        super().__init__(parent, fg_color=BG_DARK)

        self.user_email = user_email
        self.password = password
        self.host = host
        self.smtp_port = smtp_port
        self.retrieval_port = smtp_port + 1  

        self.current_view = None
        self.sidebar_buttons = {}

        self._build_ui()
        self._show_inbox()  

    def _build_ui(self):
        # top bar
        topbar = ctk.CTkFrame(self, fg_color=BG_CARD, height=48, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkLabel(topbar, text="  SMTP Mail Server", font=("Segoe UI", 15, "bold"),
                      text_color=ACCENT_BLUE).pack(side="left", padx=12)

        user_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=12)

        ctk.CTkLabel(user_frame, text=self.user_email, font=FONT_SMALL,
                      text_color=TEXT_SECONDARY).pack(side="left", padx=(0, 8))

        self.status_dot = ctk.CTkLabel(user_frame, text="●", font=("Segoe UI", 10),
                                        text_color=ACCENT_GREEN)
        self.status_dot.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(user_frame, text="Connected", font=("Segoe UI", 10),
                      text_color=TEXT_MUTED).pack(side="left")

        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(main_area, fg_color=BG_SIDEBAR, width=SIDEBAR_WIDTH, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        nav_items = [
            ("  Inbox", self._show_inbox),
            ("  Compose", self._show_compose),
            ("  Sent", self._show_sent),
            ("  Server Status", self._show_status),
            ("  Queue Monitor", self._show_queue),
            ("  Logs", self._show_logs),
        ]

        ctk.CTkLabel(sidebar, text="NAVIGATION", font=("Segoe UI", 10, "bold"),
                      text_color=TEXT_MUTED).pack(padx=16, pady=(16, 8), anchor="w")

        for label, cmd in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w", height=38,
                fg_color="transparent", hover_color=BG_HOVER,
                text_color=TEXT_SECONDARY, font=FONT_SIDEBAR,
                corner_radius=6, command=cmd
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.sidebar_buttons[label] = btn

        ctk.CTkButton(
            sidebar, text="  Logout", anchor="w", height=36,
            fg_color="transparent", hover_color=ACCENT_RED,
            text_color=TEXT_MUTED, font=FONT_SMALL,
            corner_radius=6, command=self._logout
        ).pack(side="bottom", fill="x", padx=8, pady=12)

        self.content_area = ctk.CTkFrame(main_area, fg_color=BG_DARK)
        self.content_area.pack(side="left", fill="both", expand=True)

    def _set_active_btn(self, label):
        """Highlight the active sidebar button."""
        for btn_label, btn in self.sidebar_buttons.items():
            if btn_label == label:
                btn.configure(fg_color=BG_HOVER, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

    def _clear_content(self):
        """Remove current view from content area."""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def _show_inbox(self):
        self._clear_content()
        self._set_active_btn("  Inbox")
        self.current_view = InboxFrame(
            self.content_area, self.user_email, self.password,
            self.host, self.retrieval_port,
            on_reply=self._handle_reply
        )
        self.current_view.pack(fill="both", expand=True)

    def _handle_reply(self, reply_to, reply_subject, reply_body):
        self._clear_content()
        self._set_active_btn("  Compose")
        self.current_view = ComposeFrame(
            self.content_area, self.user_email, self.password,
            self.host, self.smtp_port,
            reply_to=reply_to,
            reply_subject=reply_subject,
            reply_body=reply_body
        )
        self.current_view.pack(fill="both", expand=True)

    def _show_compose(self):
        self._clear_content()
        self._set_active_btn("  Compose")
        self.current_view = ComposeFrame(
            self.content_area, self.user_email, self.password,
            self.host, self.smtp_port
        )
        self.current_view.pack(fill="both", expand=True)

    def _show_sent(self):
        self._clear_content()
        self._set_active_btn("  Sent")
        self.current_view = SentFrame(
            self.content_area, self.user_email, self.password,
            self.host, self.retrieval_port
        )
        self.current_view.pack(fill="both", expand=True)

    def _show_status(self):
        self._clear_content()
        self._set_active_btn("  Server Status")
        self.current_view = ServerStatusPanel(
            self.content_area, self.host, self.smtp_port, self.retrieval_port
        )
        self.current_view.pack(fill="both", expand=True)

    def _show_queue(self):
        self._clear_content()
        self._set_active_btn("  Queue Monitor")
        self.current_view = QueueMonitorPanel(
            self.content_area, self.host, self.smtp_port
        )
        self.current_view.pack(fill="both", expand=True)

    def _show_logs(self):
        self._clear_content()
        self._set_active_btn("  Logs")
        self.current_view = LogViewerPanel(self.content_area)
        self.current_view.pack(fill="both", expand=True)

    def _logout(self):
        """Return to the login screen."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Logout")
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        dialog.configure(fg_color=BG_CARD)
        
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        app = self.winfo_toplevel()
        app.update_idletasks()
        x = app.winfo_x() + (app.winfo_width() // 2) - 175
        y = app.winfo_y() + (app.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Are you sure you want to log out?", 
                     font=FONT_SUBHEADING, text_color=TEXT_PRIMARY).pack(pady=(40, 30))
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()
        
        def confirm():
            dialog.grab_release()
            dialog.destroy()
            if hasattr(app, "show_login"):
                app.show_login()
                
        def cancel():
            dialog.grab_release()
            dialog.destroy()
            
        ctk.CTkButton(btn_frame, text="Yes, Log Out", width=110, height=36,
                      fg_color=ACCENT_RED, hover_color="#d73a49", 
                      text_color="white", font=FONT_BUTTON,
                      command=confirm).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", width=110, height=36,
                      fg_color=BG_HOVER, hover_color=BORDER_COLOR, 
                      text_color=TEXT_PRIMARY, font=FONT_BUTTON,
                      command=cancel).pack(side="left", padx=10)


class ServerStatusPanel(ctk.CTkFrame):
    """Shows server connection details and domain info."""

    def __init__(self, parent, host, smtp_port, retrieval_port):
        super().__init__(parent, fg_color=BG_DARK)

        ctk.CTkLabel(self, text="  Server Status", font=FONT_HEADING,
                      text_color=TEXT_PRIMARY).pack(padx=PADDING, pady=(PADDING, 8), anchor="w")

        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        card.pack(fill="x", padx=PADDING, pady=(0, 8))

        info_items = [
            ("Server Host", host),
            ("SMTP Port", str(smtp_port)),
            ("Retrieval Port", str(retrieval_port)),
            ("Status", "Running"),
            ("TLS", "Enabled (self-signed)"),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=label, font=FONT_BODY, text_color=TEXT_SECONDARY, width=140, anchor="w").pack(side="left")
            color = ACCENT_GREEN if value == "Running" else TEXT_PRIMARY
            ctk.CTkLabel(row, text=value, font=FONT_BODY, text_color=color, anchor="w").pack(side="left")

        ctk.CTkLabel(self, text="  Registered Domains", font=FONT_SUBHEADING,
                      text_color=TEXT_PRIMARY).pack(padx=PADDING, pady=(16, 8), anchor="w")

        domains_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        domains_card.pack(fill="x", padx=PADDING)

        domains = ["nu.edu.pk", "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        for d in domains:
            row = ctk.CTkFrame(domains_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text="●", font=("Segoe UI", 8), text_color=ACCENT_GREEN).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=d, font=FONT_BODY, text_color=TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(row, text="Active", font=FONT_SMALL, text_color=ACCENT_GREEN).pack(side="right")


class QueueMonitorPanel(ctk.CTkFrame):
    """Displays mail queue status and recent items."""

    def __init__(self, parent, host, smtp_port):
        super().__init__(parent, fg_color=BG_DARK)
        self.host = host

        ctk.CTkLabel(self, text="  Queue Monitor", font=FONT_HEADING,
                      text_color=TEXT_PRIMARY).pack(padx=PADDING, pady=(PADDING, 8), anchor="w")

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=PADDING, pady=(0, 12))

        statuses = [
            ("Pending", "0", ACCENT_ORANGE),
            ("Delivered", "0", ACCENT_GREEN),
            ("Failed", "0", ACCENT_RED),
        ]

        for label, count, color in statuses:
            card = ctk.CTkFrame(cards_frame, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ctk.CTkLabel(card, text=count, font=("Segoe UI", 28, "bold"), text_color=color).pack(pady=(12, 0))
            ctk.CTkLabel(card, text=label, font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(pady=(0, 12))

        info = ctk.CTkLabel(self, text="Queue processes messages automatically with retry logic (max 3 attempts)",
                             font=FONT_SMALL, text_color=TEXT_MUTED)
        info.pack(padx=PADDING, anchor="w")


class LogViewerPanel(ctk.CTkFrame):
    """Real-time log viewer that reads from the log file."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_DARK)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PADDING, pady=(PADDING, 8))

        ctk.CTkLabel(header, text="  Server Logs", font=FONT_HEADING,
                      text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(header, text="Refresh", width=80, height=30, fg_color=BG_HOVER,
                       hover_color=BORDER_COLOR, text_color=TEXT_SECONDARY, font=FONT_SMALL,
                       corner_radius=6, command=self._load_logs).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            self, fg_color=BG_CARD, text_color=ACCENT_GREEN,
            font=FONT_MONO, corner_radius=CORNER_RADIUS
        )
        self.log_box.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        self._load_logs()

    def _load_logs(self):
        """Load the latest log entries from the log file."""
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")

        try:
            with open("logs/server.log", "r") as f:
                lines = f.readlines()
                recent = lines[-200:] if len(lines) > 200 else lines
                for line in recent:
                    self.log_box.insert("end", line)
        except FileNotFoundError:
            self.log_box.insert("1.0", "No log file found. Start the server first.\n")
        except Exception as e:
            self.log_box.insert("1.0", f"Error reading logs: {e}\n")

        self.log_box.configure(state="disabled")
        self.log_box.see("end")
