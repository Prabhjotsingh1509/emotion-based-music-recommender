"""
Emotion-Based Music Recommender — GUI

A desktop application that detects the user's emotion
from text and recommends songs based on the predicted emotion.
"""
import tkinter as tk
from tkinter import font as tkfont
import webbrowser
import threading

from model import predict_emotion, recommend_music

# ──────────────────────────────────────────────
# COLOUR PALETTE
# ──────────────────────────────────────────────
BG_MAIN       = "#0d0d14"
BG_HEADER     = "#100f1f"
BG_CARD       = "#13131f"
BG_CARD_HOVER = "#1c1c2e"
BG_INPUT      = "#1a1a28"
BG_ENTRY      = "#0f0f1a"
ACCENT        = "#7c3aed"
ACCENT_LIGHT  = "#a78bfa"
BTN_ANALYZE   = "#7c3aed"
BTN_ANALYZE_H = "#5b21b6"
BTN_CLEAR     = "#dc2626"
BTN_CLEAR_H   = "#b91c1c"
TEXT_PRIMARY  = "#f1f0ff"
TEXT_MUTED    = "#6b7280"
DIVIDER       = "#1e1e2f"

EMOTION_META = {
    "happy":    {"emoji": "😄", "color": "#fbbf24", "desc": "You're radiating positivity!"},
    "sad":      {"emoji": "😢", "color": "#60a5fa", "desc": "It's okay to feel blue sometimes."},
    "angry":    {"emoji": "😡", "color": "#f87171", "desc": "Let music cool you down."},
    "stressed": {"emoji": "😫", "color": "#fb923c", "desc": "Take a breath. Music helps."},
    "neutral":  {"emoji": "😐", "color": "#9ca3af", "desc": "Steady and calm — nice."},
    "love":     {"emoji": "❤️",  "color": "#f472b6", "desc": "Love is in the air!"},
    "fear":     {"emoji": "😨", "color": "#a78bfa", "desc": "You're braver than you think."},
    "surprise": {"emoji": "😲", "color": "#34d399", "desc": "Something unexpected happened!"},
    "bored":    {"emoji": "🥱", "color": "#94a3b8", "desc": "Let music wake you up."},
}


# ──────────────────────────────────────────────
# LOADING DOTS ANIMATION
# ──────────────────────────────────────────────
class LoadingDots:
    def __init__(self, label):
        self.label = label
        self.running = False
        self._job = None

    def start(self, base="Analyzing"):
        self.running = True
        self.base = base
        self._tick(0)

    def _tick(self, n):
        if not self.running:
            return
        dots = "." * (n % 4)
        try:
            self.label.config(text=f"{self.base}{dots:<3}")
        except Exception:
            return
        self._job = self.label.after(400, lambda: self._tick(n + 1))

    def stop(self):
        self.running = False
        if self._job:
            try:
                self.label.after_cancel(self._job)
            except Exception:
                pass
        try:
            self.label.config(text="")
        except Exception:
            pass


# ──────────────────────────────────────────────
# SONG CARD
# ──────────────────────────────────────────────
class SongCard(tk.Frame):
    def __init__(self, master, index, song_name, link, **kwargs):
        super().__init__(master, bg=BG_CARD, **kwargs)
        self.link = link
        self.configure(cursor="hand2")

        # left accent bar
        accent_bar = tk.Frame(self, bg=ACCENT, width=4)
        accent_bar.pack(side="left", fill="y")

        # index badge
        badge = tk.Label(
            self,
            text=f" {index:02d} ",
            font=("Consolas", 9, "bold"),
            bg="#1e1030",
            fg=ACCENT_LIGHT,
            padx=4, pady=2,
        )
        badge.pack(side="left", padx=(10, 6), pady=12)

        # music emoji
        note = tk.Label(self, text="🎵", font=("Segoe UI Emoji", 13), bg=BG_CARD, fg=TEXT_PRIMARY)
        note.pack(side="left", padx=(0, 8))

        # song name
        name_lbl = tk.Label(
            self,
            text=song_name,
            font=("Segoe UI", 11),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=440,
        )
        name_lbl.pack(side="left", fill="x", expand=True, pady=12)

        # arrow
        arrow = tk.Label(self, text=" → ", font=("Segoe UI", 13, "bold"),
                         bg=BG_CARD, fg=ACCENT_LIGHT)
        arrow.pack(side="right", padx=12)

        for w in (self, accent_bar, badge, note, name_lbl, arrow):
            w.bind("<Button-1>", self._open_link)
            w.bind("<Enter>",    self._hover_on)
            w.bind("<Leave>",    self._hover_off)

    def _open_link(self, _=None):
        webbrowser.open(self.link)

    def _hover_on(self, _=None):
        self._set_bg(BG_CARD_HOVER)

    def _hover_off(self, _=None):
        self._set_bg(BG_CARD)

    def _set_bg(self, color):
        self.configure(bg=color)
        for child in self.winfo_children():
            try:
                if child.cget("bg") not in ("#1e1030", ACCENT):
                    child.configure(bg=color)
            except Exception:
                pass


# ──────────────────────────────────────────────
# ROUNDED BUTTON  (Canvas-drawn)
# ──────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, master, text, command, bg_color, hover_color,
                 width=160, height=38, radius=10, **kwargs):
        super().__init__(
            master, width=width, height=height,
            bg=master.cget("bg"),
            highlightthickness=0, cursor="hand2", **kwargs
        )
        self.command     = command
        self.bg_color    = bg_color
        self.hover_color = hover_color
        self.btn_text    = text
        self.width       = width
        self.height      = height
        self.radius      = radius
        self._enabled    = True
        self._draw(bg_color)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>",    self._hover_on)
        self.bind("<Leave>",    self._hover_off)

    def _draw(self, color):
        self.delete("all")
        r, w, h = self.radius, self.width, self.height
        self.create_polygon(
            r, 0,  w-r, 0,  w, r,  w, h-r,  w-r, h,  r, h,  0, h-r,  0, r,
            fill=color, outline=color, smooth=True
        )
        self.create_text(
            w//2, h//2, text=self.btn_text,
            fill=TEXT_PRIMARY if self._enabled else TEXT_MUTED,
            font=("Segoe UI", 11, "bold"),
        )

    def _click(self, _=None):
        if self._enabled and self.command:
            self.command()

    def _hover_on(self, _=None):
        if self._enabled:
            self._draw(self.hover_color)

    def _hover_off(self, _=None):
        self._draw(self.bg_color if self._enabled else "#333344")

    def set_enabled(self, val, text=None):
        self._enabled = val
        if text:
            self.btn_text = text
        self._draw(self.bg_color if val else "#333344")


# ──────────────────────────────────────────────
# MAIN APPLICATION
# ──────────────────────────────────────────────
class EmotionMusicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Emotion Music Recommender")
        self.geometry("720x700")
        self.minsize(600, 580)
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):

        # ── HEADER ────────────────────────────
        header = tk.Frame(self, bg=BG_HEADER)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🎧  Emotion Music Recommender",
            font=("Georgia", 20, "bold"),
            bg=BG_HEADER, fg=ACCENT_LIGHT,
        ).pack(pady=(16, 2))

        tk.Label(
            header,
            text="Tell me how you feel — I'll find the perfect soundtrack",
            font=("Georgia", 10, "italic"),
            bg=BG_HEADER, fg=TEXT_MUTED,
        ).pack(pady=(0, 12))

        # violet divider
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # ── INPUT CARD ────────────────────────
        input_card = tk.Frame(self, bg=BG_INPUT, pady=14)
        input_card.pack(fill="x", padx=22, pady=16)

        tk.Label(
            input_card,
            text="  How are you feeling right now?",
            font=("Segoe UI", 10),
            bg=BG_INPUT, fg=TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=8)

        # entry with accent border wrapper
        self.entry_border = tk.Frame(input_card, bg=ACCENT, padx=2, pady=2)
        self.entry_border.pack(fill="x", padx=10, pady=(4, 10))

        self.entry = tk.Entry(
            self.entry_border,
            font=("Consolas", 13),
            bg=BG_ENTRY, fg=TEXT_MUTED,
            insertbackground=ACCENT_LIGHT,
            relief="flat", bd=0,
        )
        self.entry.pack(fill="x", ipady=8, padx=1, pady=1)
        self.entry.bind("<Return>", lambda _: self._trigger_analyze())

        self._placeholder = "e.g. I feel lonely and tired today..."
        self.entry.insert(0, self._placeholder)
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        # buttons
        btn_row = tk.Frame(input_card, bg=BG_INPUT)
        btn_row.pack(pady=(0, 4))

        self.analyze_btn = RoundedButton(
            btn_row, text="✦  Analyze & Play",
            command=self._trigger_analyze,
            bg_color=BTN_ANALYZE, hover_color=BTN_ANALYZE_H,
            width=175, height=38,
        )
        self.analyze_btn.grid(row=0, column=0, padx=6)

        RoundedButton(
            btn_row, text="✕  Clear",
            command=self._clear,
            bg_color=BTN_CLEAR, hover_color=BTN_CLEAR_H,
            width=110, height=38,
        ).grid(row=0, column=1, padx=6)

        # ── EMOTION RESULT ROW ────────────────
        emotion_row = tk.Frame(self, bg=BG_MAIN)
        emotion_row.pack(fill="x", padx=26, pady=(0, 2))

        self.emoji_lbl = tk.Label(
            emotion_row, text="",
            font=("Segoe UI Emoji", 32),
            bg=BG_MAIN, fg=TEXT_PRIMARY,
        )
        self.emoji_lbl.pack(side="left", padx=(0, 10))

        emotion_text = tk.Frame(emotion_row, bg=BG_MAIN)
        emotion_text.pack(side="left", anchor="w")

        self.emotion_lbl = tk.Label(
            emotion_text, text="",
            font=("Georgia", 22, "bold"),
            bg=BG_MAIN, fg=ACCENT_LIGHT, anchor="w",
        )
        self.emotion_lbl.pack(anchor="w")

        self.desc_lbl = tk.Label(
            emotion_text, text="",
            font=("Georgia", 10, "italic"),
            bg=BG_MAIN, fg=TEXT_MUTED, anchor="w",
        )
        self.desc_lbl.pack(anchor="w")

        # loading label
        self.loading_lbl = tk.Label(
            self, text="", font=("Consolas", 11),
            bg=BG_MAIN, fg=ACCENT_LIGHT,
        )
        self.loading_lbl.pack()
        self._loader = LoadingDots(self.loading_lbl)

        # songs section header
        self.songs_hdr = tk.Label(
            self, text="",
            font=("Segoe UI", 11, "bold"),
            bg=BG_MAIN, fg=TEXT_MUTED, anchor="w",
        )
        self.songs_hdr.pack(fill="x", padx=26)

        # ── SCROLLABLE SONG LIST ──────────────
        scroll_container = tk.Frame(self, bg=BG_MAIN)
        scroll_container.pack(fill="both", expand=True, padx=18, pady=(4, 0))

        self.canvas = tk.Canvas(
            scroll_container, bg=BG_MAIN, highlightthickness=0, bd=0
        )
        scrollbar = tk.Scrollbar(
            scroll_container, orient="vertical",
            command=self.canvas.yview,
            bg=DIVIDER, troughcolor=BG_MAIN,
        )
        self.song_frame = tk.Frame(self.canvas, bg=BG_MAIN)
        self.song_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self._win_id = self.canvas.create_window((0, 0), window=self.song_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── FOOTER ────────────────────────────
        tk.Frame(self, bg=DIVIDER, height=1).pack(fill="x", pady=(4, 0))
        tk.Label(
            self,
            text="AI/ML Project  ·  Dataset-Based Emotion Detection  ·  Press Enter to Analyze",
            font=("Segoe UI", 9),
            bg=BG_MAIN, fg=TEXT_MUTED,
        ).pack(pady=6)

    # ── PLACEHOLDER ───────────────────────────
    def _on_focus_in(self, _):
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=TEXT_PRIMARY)

    def _on_focus_out(self, _):
        if not self.entry.get().strip():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=TEXT_MUTED)

    # ── CANVAS RESIZE ─────────────────────────
    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._win_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── ANALYZE ───────────────────────────────
    def _trigger_analyze(self):
        text = self.entry.get().strip()
        if not text or text == self._placeholder:
            self._flash_entry_border()
            return
        self.analyze_btn.set_enabled(False, "Analyzing…")
        self._clear_results()
        self._loader.start("Analyzing emotion")
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        try:
            emotion = predict_emotion(text)
            songs   = recommend_music(emotion)
            self.after(0, lambda: self._display(emotion, songs))
        except Exception as ex:
            self.after(0, lambda: self._show_error(str(ex)))

    def _display(self, emotion, songs):
        self._loader.stop()
        self.analyze_btn.set_enabled(True, "✦  Analyze & Play")

        meta = EMOTION_META.get(emotion, {"emoji": "🙂", "color": ACCENT_LIGHT, "desc": ""})
        self.emoji_lbl.config(text=meta["emoji"])
        self.emotion_lbl.config(text=emotion.upper(), fg=meta["color"])
        self.desc_lbl.config(text=meta["desc"])
        self._pulse_emotion(meta["color"])

        self.songs_hdr.config(text=f"  🎶  Recommended Songs  ({len(songs)} tracks)")

        for i, (song, link) in enumerate(songs, start=1):
            card = SongCard(self.song_frame, index=i, song_name=song, link=link)
            card.pack_forget()
            self.after(i * 90, lambda c=card: c.pack(fill="x", pady=3, padx=2))

    def _pulse_emotion(self, color):
        seq = [ACCENT_LIGHT, color, ACCENT_LIGHT, color, ACCENT_LIGHT, color]
        def step(i=0):
            if i < len(seq):
                try:
                    self.emotion_lbl.config(fg=seq[i])
                    self.after(120, lambda: step(i + 1))
                except Exception:
                    pass
        step()

    def _clear(self):
        self.entry.delete(0, tk.END)
        self._on_focus_out(None)
        self._clear_results()

    def _clear_results(self):
        self.emoji_lbl.config(text="")
        self.emotion_lbl.config(text="")
        self.desc_lbl.config(text="")
        self.songs_hdr.config(text="")
        for w in self.song_frame.winfo_children():
            w.destroy()

    def _show_error(self, msg):
        self._loader.stop()
        self.analyze_btn.set_enabled(True, "✦  Analyze & Play")
        self.emotion_lbl.config(text=f"Error: {msg}", fg=BTN_CLEAR)

    def _flash_entry_border(self, n=0, colors=None):
        if colors is None:
            colors = [BTN_CLEAR, ACCENT, BTN_CLEAR, ACCENT, ACCENT]
        if n < len(colors):
            try:
                self.entry_border.config(bg=colors[n])
                self.after(120, lambda: self._flash_entry_border(n + 1, colors))
            except Exception:
                pass


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = EmotionMusicApp()
    app.mainloop()
