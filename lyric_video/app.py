from __future__ import annotations

import argparse
import random
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from PIL import ImageTk

from .config import Lyric, Settings, load_lyrics, load_settings
from .visuals import ease_in_out, ease_out_cubic, render_background, render_card


class LyricCard:
    def __init__(
        self,
        root: tk.Tk,
        settings: Settings,
        lyric: Lyric,
        index: int,
        end_time: float,
    ) -> None:
        self.settings = settings
        self.lyric = lyric
        self.index = index
        self.end_time = end_time
        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()
        rng = random.Random(settings.random_seed + index * 211)

        self.width = min(680, max(430, int(self.screen_w * .42)))
        self.height = min(310, max(220, int(self.screen_h * .29)))
        positions = [
            (.08, .13), (.51, .15), (.13, .55), (.48, .54), (.29, .34),
            (.06, .36), (.56, .38),
        ]
        px, py = positions[index % len(positions)]
        self.target_x = int(min(self.screen_w - self.width - 35, self.screen_w * px))
        self.target_y = int(min(self.screen_h - self.height - 35, self.screen_h * py))
        self.slide_x = rng.choice([-1, 1]) * rng.randint(28, 54)
        self.slide_y = rng.randint(-12, 14)
        self.words = lyric.text.split()
        available = max(.45, end_time - lyric.time - settings.fade_seconds)
        # Las frases sostenidas (especialmente los "I swear") necesitan usar
        # también sus pausas largas; limitar el intervalo aceleraba las palabras.
        self.word_interval = max(.12, available / max(1, len(self.words)))
        self.visible_words = -1

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.transient(root)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=settings.palette["soft_black"])
        image = render_card(
            "", index + 1, (self.width, self.height), settings.assets_dir,
            settings.palette, settings.random_seed,
        )
        self.photo = ImageTk.PhotoImage(image, master=self.window)
        self.canvas = tk.Canvas(
            self.window, width=self.width, height=self.height, bd=0,
            highlightthickness=0, bg=settings.palette["paper"],
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        font_size = 46 if len(lyric.text) < 48 else 38 if len(lyric.text) < 85 else 32
        font_style = "italic" if index % 3 == 1 else "bold"
        self.text_item = self.canvas.create_text(
            self.width // 2, self.height // 2,
            text="", width=self.width - 92, justify="center",
            fill=settings.palette["ink"],
            font=("Baskerville", font_size, font_style),
        )
        self.window.geometry(f"{self.width}x{self.height}+{self.target_x + self.slide_x}+{self.target_y + self.slide_y}")
        try:
            self.window.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        self.window.deiconify()
        self.window.lift(root)

    def update(self, elapsed: float) -> bool:
        fade = self.settings.fade_seconds
        enter = ease_out_cubic((elapsed - self.lyric.time) / fade)
        exit_start = self.end_time - fade
        leaving = ease_in_out((elapsed - exit_start) / fade) if elapsed >= exit_start else 0.0
        opacity = max(0.0, min(1.0, enter * (1.0 - leaving)))

        # El JSON marca el inicio de cada verso. Sin tiempos por palabra, las
        # palabras se distribuyen uniformemente en el espacio hasta el siguiente.
        word_count = min(
            len(self.words),
            max(1, int((elapsed - self.lyric.time) / self.word_interval) + 1),
        )
        if word_count != self.visible_words:
            self.visible_words = word_count
            self.canvas.itemconfigure(self.text_item, text=" ".join(self.words[:word_count]))

        x = self.target_x + int(self.slide_x * (1.0 - enter))
        y = self.target_y + int(self.slide_y * (1.0 - enter) - 9 * leaving)
        # Tk no escala el contenido de un Toplevel de manera nativa. El pequeño
        # recorrido con easing produce la sensación de acercamiento sin recortar
        # las orillas de la tarjeta.
        self.window.geometry(f"{self.width}x{self.height}+{x}+{y}")
        try:
            self.window.attributes("-alpha", opacity)
        except tk.TclError:
            pass
        # Tk 8.6 en macOS puede bajar un Toplevel sin bordes al repintar el root.
        # Elevarlo en cada frame garantiza que el recorte permanezca al frente.
        self.window.lift()
        return elapsed < self.end_time

    def destroy(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()


class LyricVideoApp:
    FRAME_MS = 16

    def __init__(self, root: tk.Tk, settings: Settings, lyrics: list[Lyric], windowed: bool) -> None:
        self.root = root
        self.settings = settings
        self.lyrics = lyrics
        self.active: list[LyricCard] = []
        self.next_index = 0
        self.started_at: float | None = None
        self.finished = False
        self.pygame = None

        # Evita que macOS muestre el cascarón negro mientras Pillow prepara la
        # composición. La ventana se revela solo después del primer repintado.
        root.withdraw()
        root.title("Against the Kitchen Floor — lyric fragment")
        root.configure(bg=settings.palette["soft_black"])
        if settings.fullscreen and not windowed:
            root.attributes("-fullscreen", True)
        else:
            root.geometry("1200x760")
        root.bind("<Escape>", lambda _event: self.close())
        root.bind("q", lambda _event: self.close())
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.update_idletasks()

        width, height = root.winfo_width(), root.winfo_height()
        if width <= 1 or height <= 1:
            width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        bg = render_background((width, height), settings.assets_dir, settings.palette, settings.random_seed)
        self.background_photo = ImageTk.PhotoImage(bg, master=root)
        self.canvas = tk.Canvas(
            root, width=width, height=height, bd=0, highlightthickness=0,
            bg=settings.palette["soft_black"],
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.background_photo, anchor="nw")
        self.canvas.create_text(
            width // 2, height - 44, text="ESC  ·  salir", fill=settings.palette["gold"],
            font=("Times", 13, "italic"),
        )
        root.deiconify()
        root.lift()
        root.update_idletasks()
        root.update()
        root.after(600, self.start)

    def start(self) -> None:
        try:
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(str(self.settings.audio_file))
            pygame.mixer.music.play(loops=0, start=self.settings.audio_start_seconds)
            self.pygame = pygame
        except Exception as exc:
            messagebox.showerror("No se pudo reproducir el audio", str(exc), parent=self.root)
            self.close()
            return
        self.started_at = time.monotonic()
        self.tick()

    def playback_elapsed(self) -> float:
        """Reloj del audio; evita que la animación derive respecto a pygame."""
        if self.pygame:
            position_ms = self.pygame.mixer.music.get_pos()
            if position_ms >= 0:
                return position_ms / 1000.0
        return 0.0 if self.started_at is None else time.monotonic() - self.started_at

    def tick(self) -> None:
        if self.started_at is None or self.finished:
            return
        elapsed = self.playback_elapsed()

        while self.next_index < len(self.lyrics) and self.lyrics[self.next_index].time <= elapsed:
            index = self.next_index
            if index + 1 < len(self.lyrics):
                end_time = min(
                    self.settings.visual_duration_seconds,
                    self.lyrics[index + 1].time + self.settings.overlap_seconds,
                )
            else:
                end_time = self.settings.visual_duration_seconds
            self.active.append(LyricCard(self.root, self.settings, self.lyrics[index], index, end_time))
            self.next_index += 1

        survivors: list[LyricCard] = []
        for card in self.active:
            if card.update(elapsed):
                survivors.append(card)
            else:
                card.destroy()
        self.active = survivors

        if elapsed >= self.settings.visual_duration_seconds:
            self.finish()
            return
        self.root.after(self.FRAME_MS, self.tick)

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        if self.pygame:
            self.pygame.mixer.music.stop()
        for card in self.active:
            card.destroy()
        self.active.clear()
        if self.settings.close_when_finished:
            self.root.after(120, self.close)

    def close(self) -> None:
        self.finished = True
        if self.pygame:
            try:
                self.pygame.mixer.music.stop()
                self.pygame.mixer.quit()
            except Exception:
                pass
        for card in self.active:
            card.destroy()
        if self.root.winfo_exists():
            self.root.destroy()


def validate_project(project_dir: Path) -> tuple[Settings, list[Lyric]]:
    settings = load_settings(project_dir)
    lyrics = load_lyrics(settings.lyrics_file, settings.visual_duration_seconds)
    if not settings.audio_file.exists():
        raise ValueError(f"No se encontró el audio: {settings.audio_file}")
    return settings, lyrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lyric video teatral con Tkinter + pygame")
    parser.add_argument("--check", action="store_true", help="valida el proyecto sin abrir la app")
    parser.add_argument("--windowed", action="store_true", help="abre en ventana aunque config diga fullscreen")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_dir = Path(__file__).resolve().parent.parent
    try:
        settings, lyrics = validate_project(project_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        end = settings.audio_start_seconds + settings.visual_duration_seconds
        print(f"Proyecto válido: {len(lyrics)} versos · audio {settings.audio_start_seconds:.1f}s → {end:.1f}s")
        return 0

    root = tk.Tk()
    LyricVideoApp(root, settings, lyrics, windowed=args.windowed)
    root.mainloop()
    return 0
