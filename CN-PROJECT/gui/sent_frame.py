import customtkinter as ctk
from gui.theme import *
from client.retrieval_client import RetrievalClient


class SentFrame(ctk.CTkFrame):
    """View for sent emails."""

    def __init__(self, parent, user_email, password, host, retrieval_port):
        super().__init__(parent, fg_color=BG_DARK)
        self.user_email = user_email
        self.password = password
        self.retrieval_client = RetrievalClient(host=host, port=retrieval_port)
        self.messages = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING, pady=(PADDING, 8))

        ctk.CTkLabel(header_frame, text="  Sent Items", font=FONT_HEADING, text_color=TEXT_PRIMARY).pack(side="left")
        self.count_label = ctk.CTkLabel(header_frame, text="", font=FONT_SMALL, text_color=TEXT_SECONDARY)
        self.count_label.pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            header_frame, text="Refresh", width=80, height=30, fg_color=BG_HOVER,
            hover_color=BORDER_COLOR, text_color=TEXT_SECONDARY, font=FONT_SMALL,
            corner_radius=6, command=self.refresh
        ).pack(side="right")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PADDING, pady=(0, PADDING))

        self.list_frame = ctk.CTkScrollableFrame(content, fg_color=BG_CARD, corner_radius=CORNER_RADIUS, width=340)
        self.list_frame.pack(side="left", fill="y", padx=(0, 8))

        self.detail_frame = ctk.CTkFrame(content, fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
        self.detail_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(self.detail_frame, text="Select a message to view",
                      font=FONT_BODY, text_color=TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")

    def refresh(self):
        try:
            self.messages = self.retrieval_client.get_sent(self.user_email, self.password)
            self.count_label.configure(text=f"({len(self.messages)} messages)")
            self._render_list()
        except Exception:
            self.count_label.configure(text="Error loading")

    def _render_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not self.messages:
            ctk.CTkLabel(self.list_frame, text="No sent messages", font=FONT_BODY, text_color=TEXT_MUTED).pack(pady=40)
            return
        for i, msg in enumerate(self.messages):
            self._create_row(i, msg)

    def _create_row(self, index, msg):
        row = ctk.CTkFrame(self.list_frame, fg_color="transparent", corner_radius=6, cursor="hand2")
        row.pack(fill="x", padx=4, pady=2)

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(fill="x", padx=8, pady=6)

        to_lbl = ctk.CTkLabel(text_frame, text=f"To: {msg.get('recipient', '')}", font=FONT_BODY,
                                text_color=TEXT_PRIMARY, anchor="w")
        to_lbl.pack(fill="x")

        subject = msg.get("subject", "(no subject)")
        if len(subject) > 38:
            subject = subject[:35] + "..."
        subj_lbl = ctk.CTkLabel(text_frame, text=subject, font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w")
        subj_lbl.pack(fill="x")

        time_lbl = ctk.CTkLabel(text_frame, text=msg.get("timestamp", ""), font=("Segoe UI", 9),
                                  text_color=TEXT_MUTED, anchor="w")
        time_lbl.pack(fill="x")

        for w in [row, text_frame, to_lbl, subj_lbl, time_lbl]:
            w.bind("<Button-1>", lambda e, idx=index: self._show_message(idx))

    def _show_message(self, index):
        msg = self.messages[index]
        for w in self.detail_frame.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(header, text=msg.get("subject", "(no subject)"), font=FONT_SUBHEADING,
                      text_color=TEXT_PRIMARY, anchor="w", wraplength=500).pack(fill="x")

        ctk.CTkLabel(header, text=f"To: {msg.get('recipient', '')}", font=FONT_BODY,
                      text_color=ACCENT_BLUE, anchor="w").pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(header, text=f"Date: {msg.get('timestamp', '')}", font=FONT_SMALL,
                      text_color=TEXT_MUTED, anchor="w").pack(fill="x")

        ctk.CTkFrame(self.detail_frame, fg_color=BORDER_COLOR, height=1).pack(fill="x", padx=16, pady=8)

        body_box = ctk.CTkTextbox(self.detail_frame, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                                   font=FONT_BODY, border_width=0, corner_radius=6, wrap="word")
        body_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body_box.insert("1.0", msg.get("body", ""))
        body_box.configure(state="disabled")
