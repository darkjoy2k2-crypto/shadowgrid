# SHADOWGRID

> ### 🎮 [**PLAY SHADOWGRID IN YOUR BROWSER**](https://darkjoy2k2-crypto.github.io/shadowgrid/)

---

## 📸 Screenshots

| Start Screen | In-Game View |
| :---: | :---: |
| ![Start Screen](docs/screenshots/start_screen.png) | ![Gameplay](docs/screenshots/gameplay.png) |

---

## 🕹️ About the Game

**Shadowgrid** is a tactical cyberpunk network infiltration game. Operating from a custom cyberdeck interface, the player navigates complex neural grid topologies, hacks IoT devices, bypasses corporate Guardians, and steals valuable data fragments.

### Key Gameplay Mechanics

- **Grid Infiltration**: Navigate tile-based network nodes, plan pathways, and maneuver around civilian traffic and security scanners.
- **Cyberdeck & Drivers**: Equip and swap functional software drivers (`disp.drv`, `ucam.drv`, etc.) to expand vision, access node telemetry, and override security gates.
- **Threat & Alert Dynamics**: Security escalates as infiltration continues. High threat triggers security lockdowns and visual deck destabilization.
- **Terminal Feed**: Real-time cyberpunk terminal stream monitoring system events, threat metrics, and script execution.

---

## 🖥️ Visual & Audio Presentation

- **CRT Post-Processing**: CRT scanline rastering, corner vignette, and green phosphor glow (`#00E676`) around network traces and UI elements.
- **Dual-Layer Parallax**: Deep network backdrop layer and coarse grid layer anchored to the screen center for smooth zoom scaling.
- **Spatial Audio**: Dynamic 2D spatial sound with distance attenuation and panning.

---

## 🚀 How to Run Locally

### Requirements
- Python 3.10 or higher
- `pygame-ce`

### Quickstart

```bash
# Install dependencies
pip install pygame-ce numpy

# Start the game
python run.py
```

### Controls
- **Left Mouse Click**: Set target destination / interact with UI buttons
- **Scroll Wheel**: Zoom grid camera in / out
- **ESC**: Pause / Exit menu