# Against The Kitchen Floor — Lyric Visualizer

An animated lyric visualizer synchronized to the final section of **Against The Kitchen Floor**.

The project combines music playback, animated lyric cards, vintage paper aesthetics, and cinematic transitions to create a visual storytelling experience inspired by the emotional progression of the song.

---

## Features

* MP3 synchronized playback
* Timestamp-based lyric system
* Animated lyric cards
* Paper-themed visual design
* Smooth transitions between verses
* Configurable color palettes
* Custom asset support
* Easily editable lyrics and timing

---

## Project Structure

```text
assets/
audio/
data/
src/

audio/
└── against_the_kitchen_floor.mp3

data/
└── lyrics.json

src/
└── main.py
```

---

## Lyrics Format

Lyrics are loaded dynamically from a JSON file.

Example:

```json
[
  {
    "time": 0.0,
    "text": "Example lyric"
  }
]
```

All timestamps are relative to the selected starting point of the song.

---

## Visual Style

The visual experience focuses on:

* Vintage paper textures
* Soft lighting
* Cinematic transitions
* Layered composition
* Animated typography
* Emotional progression synchronized to the music

The color palette is inspired by the warm tones and visual identity associated with Will Wood's work, particularly the aesthetic direction of *In Case I Make It*.

---

## Configuration

The project can be customized through configuration files:

* Colors
* Animation speed
* Card duration
* Font selection
* Transition styles
* Asset folders

---

## Future Features

* Multiple visual themes
* Camera movement system
* Particle effects
* Automatic lyric synchronization
* Full-song support
* Export to video

---

## Disclaimer

This project is a fan-made visualizer created for educational and artistic purposes.

Music rights belong to their respective owners.
