# TRIQUI NEON

Juego de **Triqui (Tic Tac Toe)** con estética neón: compites contra la máquina en una ventana de escritorio, con animaciones, brillo, confeti y tres niveles de dificultad.

Hecho con **Python + Tkinter**. No requiere instalar ninguna librería.

## Características

- Ventana propia (no usa navegador ni localhost)
- Fichas que se dibujan con animación y efecto de brillo neón
- Línea ganadora animada y explosión de confeti
- Marcador de partidas (Tú / Empates / Máquina)
- Tres dificultades:
  - **Fácil**: la máquina juega al azar
  - **Medio**: gana si puede, bloquea y busca el centro
  - **Imposible**: algoritmo Minimax con poda alfa-beta (nunca pierde)
- Quien empieza se alterna en cada ronda

## Requisitos

- Python 3.8 o superior ([descargar](https://www.python.org/downloads/)). En Windows, marca **"Add Python to PATH"** al instalar.
- Tkinter (viene incluido con Python en Windows y macOS).

## Cómo ejecutarlo

### Desde VS Code
1. Abre la carpeta del proyecto (`File > Open Folder`).
2. Instala la extensión **Python** de Microsoft si no la tienes.
3. Abre `triqui.py` y pulsa el botón ▶ (arriba a la derecha) o presiona **F5**.

### Desde la terminal
```bash
python triqui.py
```
(En macOS/Linux puede ser `python3 triqui.py`.)

> En Linux, si falta Tkinter: `sudo apt install python3-tk`

## Controles

| Acción | Control |
|---|---|
| Jugar / elegir dificultad | Clic |
| Nueva partida | Clic al terminar o tecla `R` |
| Salir | `Esc` |

## Estructura

```
triqui/
├── triqui.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .gitattributes
└── .vscode/launch.json
```

## Licencia

MIT
