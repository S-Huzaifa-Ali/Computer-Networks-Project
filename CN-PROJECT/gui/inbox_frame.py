import customtkinter as ctk
from gui.theme import *
from client.retrieval_client import RetrievalClient


class InboxFrame(ctk.CTkFrame):
    """Inbox view showing received emails."""

    def __init__(self, parent, user_email, password, host, retrieval_port, on_reply=None):
        super().__init__(parent, fg_color=BG_DARK)
        self.user_email = user_email
        self.password = password
        self.retrieval_client = RetrievalClient(host=host, port=retrieval_port)
        self.on_reply = on_reply 
        self.messages = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING, pady=(PADDING, 8))

        ctk.CTkLabel(header_frame, text="  Inbox", font=FONT_HEADING, text_color=TEXT_PRIMARY).pack(side="left")
        self.count_label = ctk.CTkLabel(header_frame, text="", font=FONT_SMALL, text_color=TEXT_SECONDARY)
        self.count_label.pack(side="left", padx=(12, 0))

        ctk.CTkButton(
            header_frame, text="Refresh", width=90, height=34, fg_color=BG_HOVER,
            hover_color=BORDER_COLOR, text_color=TEXT_SECONDARY, font=FONT_SMALL,
            corner_radius=6, command=self.refresh
        ).pack(side="right")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        self.list_frame = ctk.CTkScrollableFrame(content, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, width=360)
        self.list_frame.pack(side="left", fill="y", padx=(0, 8))

        self.detail_frame = ctk.CTkFrame(content, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        self.detail_frame.pack(side="left", fill="both", expand=True)
        self._show_empty_detail()

    def refresh(self):
        try:
            self.messages = self.retrieval_client.get_inbox(self.user_email, self.password)
            self.count_label.configure(text=f"({len(self.messages)} messages)")
            self._render_list()
        except Exception as e:
            self.count_label.configure(text="Error loading")

    def _render_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not self.messages:
            ctk.CTkLabel(self.list_frame, text="No messages in inbox", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return
        for i, msg in enumerate(self.messages):
            self._create_row(i, msg)

    def _create_row(self, index, msg):
        is_unread = not msg.get("is_read", True)
        row = ctk.CTkFrame(self.list_frame, fg_color=BG_INPUT if is_unread else "transparent", corner_radius=6, cursor="hand2")
        row.pack(fill="x", padx=4, pady=2)

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        
        left_pad = 22 if is_unread else 10
        text_frame.pack(fill="x", padx=(left_pad, 10), pady=8)

        if is_unread:
            ctk.CTkLabel(row, text="●", font=("Segoe UI", 10), text_color=ACCENT_BLUE, width=14).place(x=6, y=10)

        sender_lbl = ctk.CTkLabel(text_frame, text=msg.get("sender", "Unknown"),
                                  font=("Segoe UI", 13, "bold") if is_unread else FONT_BODY,
                                  text_color=TEXT_PRIMARY, anchor="w")
        sender_lbl.pack(fill="x")

        subject = msg.get("subject", "(no subject)")
        if len(subject) > 36:
            subject = subject[:33] + "..."
        subj_lbl = ctk.CTkLabel(text_frame, text=subject, font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w")
        subj_lbl.pack(fill="x")

        time_lbl = ctk.CTkLabel(text_frame, text=msg.get("timestamp", ""), font=("Segoe UI", 10), text_color=TEXT_MUTED, anchor="w")
        time_lbl.pack(fill="x")

        for w in [row, text_frame, sender_lbl, subj_lbl, time_lbl]:
            w.bind("<Button-1>", lambda e, idx=index: self._show_message(idx))

    def _show_message(self, index):
        msg = self.messages[index]
        msg_id = msg.get("id")
        if msg_id and not msg.get("is_read", True):
            self.retrieval_client.mark_read(self.user_email, self.password, msg_id)
            msg["is_read"] = 1
            self._render_list()

        for w in self.detail_frame.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text=msg.get("subject", "(no subject)"), font=FONT_SUBHEADING,
                      text_color=TEXT_PRIMARY, anchor="w", wraplength=500).pack(fill="x")

        ctk.CTkLabel(header, text=f"From: {msg.get('sender', '')}", font=FONT_BODY,
                      text_color=ACCENT_BLUE, anchor="w").pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(header, text=f"To: {msg.get('recipient', '')}", font=FONT_SMALL,
                      text_color=TEXT_SECONDARY, anchor="w").pack(fill="x")
        ctk.CTkLabel(header, text=f"Date: {msg.get('timestamp', '')}", font=FONT_SMALL,
                      text_color=TEXT_MUTED, anchor="w").pack(fill="x")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        reply_btn = ctk.CTkButton(
            btn_row, text="  Reply", width=110, height=34,
            fg_color=ACCENT_BLUE_DIM, hover_color=ACCENT_BLUE,
            text_color="white", font=("Segoe UI", 13, "bold"),
            corner_radius=6,
            command=lambda: self._reply_to_message(msg)
        )
        reply_btn.pack(side="left")

        ctk.CTkFrame(self.detail_frame, fg_color=BORDER_COLOR, height=1).pack(fill="x", padx=20, pady=10)

        body_box = ctk.CTkTextbox(self.detail_frame, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                                   font=FONT_BODY, border_width=0, corner_radius=6, wrap="word")
        body_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body_box.insert("1.0", msg.get("body", ""))
        body_box.configure(state="disabled")

    def _reply_to_message(self, msg):
        """Trigger reply via the dashboard callback."""
        if self.on_reply:
            self.on_reply(
                reply_to=msg.get("sender", ""),
                reply_subject=msg.get("subject", ""),
                reply_body=msg.get("body", "")
            )

    def _show_empty_detail(self):
        ctk.CTkLabel(self.detail_frame, text="Select a message to read",
                      font=FONT_BODY, text_color=TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")
