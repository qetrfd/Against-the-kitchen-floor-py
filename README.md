# Against the Kitchen Floor — lyric fragment

Una experiencia de lyric video surrealista inspirada en la estética de Will Wood,
con papel animado, texturas vintage y recortes dibujados a mano.

Aplicación de escritorio en Python que reproduce el MP3 desde **03:35 (215 s)**
hasta el final del archivo (**05:06.103**). Los versos aparecen en ventanas Tkinter
sin bordes, como recortes de papel, mientras `pygame` reproduce el audio.

## Preparación

Requiere Python 3.9 o posterior. El entorno `.venv` del proyecto ya quedó
preparado; si necesitas recrearlo, usa estos comandos:

```bash
cd "/Users/ioslabaulainclusiva/Desktop/ATKF"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Editar los versos

Abre `lyrics.json`. Cada `time` es relativo al inicio del fragmento, no al inicio
de la canción: `0` equivale a 03:35, `4.2` equivale a 03:39.2, etc.

```json
[
  { "time": 0, "text": "VERSO AQUI" },
  { "time": 4.2, "text": "OTRO VERSO" }
]
```

Los tiempos deben estar en orden. Los versos posteriores a la duración configurada
(91.103 s para este MP3) se conservan en el archivo pero la app los ignora.

## Ejecutar

```bash
python main.py --check
python main.py
```

Pulsa `Esc` o `Q` para salir. Para probar sin pantalla completa:

```bash
python main.py --windowed
```

## Personalizar

- `config.json`: segundo inicial, duración, fades, solapamiento, pantalla completa
  y toda la paleta.
- `lyrics.json`: tiempos y textos.
- `assets/paper_texture.png`: textura de fondo y tarjetas.
- `assets/*.png`: sol, luna, rosa y marco. Todos son opcionales; si faltan, la
  app sigue dibujando papel, grano, sombras y bordes con código.

El valor `random_seed` permite cambiar la distribución del grano y el carácter de
las animaciones manteniendo un resultado reproducible.

Cada `time` inicia el primer término del verso; como el formato no incluye tiempos
por palabra, las demás palabras se distribuyen automáticamente antes del verso
siguiente. La animación usa el reloj de reproducción de `pygame` para no acumular
desfase respecto al audio.
