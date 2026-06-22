from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Lyric:
    time: float
    text: str


@dataclass(frozen=True)
class Settings:
    project_dir: Path
    audio_file: Path
    lyrics_file: Path
    assets_dir: Path
    audio_start_seconds: float
    visual_duration_seconds: float
    fade_seconds: float
    overlap_seconds: float
    fullscreen: bool
    close_when_finished: bool
    random_seed: int
    palette: dict[str, str]


DEFAULT_PALETTE = {
    "ink": "#201a17",
    "soft_black": "#110f0e",
    "paper": "#e7d1aa",
    "cream": "#f1e3c7",
    "gold": "#b7863c",
    "coffee": "#5a3829",
    "wine": "#4d1720",
    "burnt_red": "#8e3828",
    "teal": "#496d67",
}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"No se encontró: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido en {path.name}: {exc}") from exc


def load_settings(project_dir: Path) -> Settings:
    project_dir = project_dir.resolve()
    raw = _read_json(project_dir / "config.json")
    palette = {**DEFAULT_PALETTE, **raw.get("palette", {})}

    settings = Settings(
        project_dir=project_dir,
        audio_file=project_dir / raw.get("audio_file", "against_the_kitchen_floor.mp3"),
        lyrics_file=project_dir / raw.get("lyrics_file", "lyrics.json"),
        assets_dir=project_dir / raw.get("assets_dir", "assets"),
        audio_start_seconds=float(raw.get("audio_start_seconds", 215)),
        visual_duration_seconds=float(raw.get("visual_duration_seconds", 40)),
        fade_seconds=float(raw.get("fade_seconds", 0.55)),
        overlap_seconds=float(raw.get("overlap_seconds", 0.25)),
        fullscreen=bool(raw.get("fullscreen", True)),
        close_when_finished=bool(raw.get("close_when_finished", True)),
        random_seed=int(raw.get("random_seed", 1945)),
        palette=palette,
    )
    if settings.audio_start_seconds < 0:
        raise ValueError("audio_start_seconds no puede ser negativo")
    if settings.visual_duration_seconds <= 0:
        raise ValueError("visual_duration_seconds debe ser mayor que cero")
    if settings.fade_seconds <= 0:
        raise ValueError("fade_seconds debe ser mayor que cero")
    return settings


def load_lyrics(path: Path, duration: float) -> list[Lyric]:
    raw = _read_json(path)
    if not isinstance(raw, list) or not raw:
        raise ValueError("lyrics.json debe ser una lista con al menos un verso")

    lyrics: list[Lyric] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict) or "time" not in item or "text" not in item:
            raise ValueError(f"Verso {index}: se requieren 'time' y 'text'")
        try:
            timestamp = float(item["time"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Verso {index}: 'time' debe ser un número") from exc
        text = str(item["text"]).strip()
        if timestamp < 0:
            raise ValueError(f"Verso {index}: 'time' no puede ser negativo")
        if not text:
            raise ValueError(f"Verso {index}: 'text' no puede estar vacío")
        lyrics.append(Lyric(timestamp, text))

    if any(a.time >= b.time for a, b in zip(lyrics, lyrics[1:])):
        raise ValueError("Los tiempos deben estar ordenados y no pueden repetirse")
    visible = [lyric for lyric in lyrics if lyric.time < duration]
    if not visible:
        raise ValueError(f"No hay versos dentro de los primeros {duration} segundos")
    return visible
