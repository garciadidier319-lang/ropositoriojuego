# TANQUES NEON

Juego de tanques para **2 jugadores en el mismo teclado**, con estética neón. Las balas rebotan en las paredes (¡y también pueden darte a ti!). Gana el primero en llegar a **5 puntos**.

Hecho con **Python + Tkinter**. No requiere instalar ninguna librería.

## Controles

| | Jugador 1 (cian) | Jugador 2 (magenta) |
|---|---|---|
| Avanzar / retroceder | `W` / `S` | `↑` / `↓` |
| Girar | `A` / `D` | `←` / `→` |
| Disparar | `F` o `Espacio` | `Enter` o `Ctrl` derecho |

Otras teclas: `R` reinicia la partida · `Esc` sale.

## Cómo ejecutarlo

### Desde VS Code
1. Abre la carpeta del repositorio en VS Code.
2. Abre `tanques/tanques.py` y pulsa el botón ▶ (o F5).

### Desde la terminal
```bash
python tanques/tanques.py
```

Requiere Python 3.8 o superior. En Linux, si falta Tkinter: `sudo apt install python3-tk`.

## Características

- 3 mapas distintos que cambian en cada ronda
- Balas con rebote, estela de luz y explosiones con partículas
- Cuenta regresiva, marcador de rondas y pantalla de victoria
- Colisiones con paredes y entre tanques

> Consejo: algunos teclados no registran muchas teclas a la vez. Si un jugador no puede disparar mientras avanza, usen las teclas alternativas de disparo.
