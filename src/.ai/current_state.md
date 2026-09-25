# Shadowgrid - Aktueller Entwicklungsstand (22.09.2026)

## Implementierte Features (Erfolgreich abgeschlossen)
1. **Pursuit Logik (P-Controller):**
   - Der Spieler folgt Zivilisten mit einem exakten Abstand von 1 Tile (65536 in Q16.16) plus 4 Pixel.
   - Geschwindigkeits-Sync verhindert jegliches Ruckeln.
   - Spieler stoppt automatisch, falls er physisch näher am A*-Zielknoten ist als der Zivilist (kein Überholen).

2. **Infiltrations-Minispiel:**
   - 9-Slice Cyberpunk UI Action Menu (`action_menu.py`), verschiebbar (Drag & Drop am Titel) und merkt sich die Position.
   - Optionen: `[INFILTRATE]` (implementiert) und `[HIJACK]` (ausstehend).
   - Infiltration dauert 3 Sekunden (100 % Balken). 
   - Zivilisten können Verdacht schöpfen (is_suspicious). Der Balken fällt dann langsam ab, wenn nicht pausiert wird. Pause blockiert den Alert, pausiert aber auch den Fortschritt.
   - Bei 100 % erhält der Zivilist das `is_robbed` Flag: Er wird grau `(100, 100, 100)` gerendert und komplett von allen Maus-Interaktionen (Hover/Click) ignoriert.

3. **Threat-Engine & Sentinels:**
   - Suspicion erhöht den globalen Threat-Level.
   - Ab 100 % Threat wird der Alert getriggert: Der Text blinkt und das reguläre Threat-Decay wird für exakt 10 Sekunden eingefroren (`alert_timer`).
   - Begegnungen mit Drohnen (`dist == 0`) sind **ausschließlich** während des aktiven Alarms (`alert_triggered`), bei 100 % Threat oder nach Entdeckung beim Infiltrieren tödlich.
   - Im Normalzustand erzeugen Sentinels in Reichweite dynamischen Threat-Anstieg: In 3–4 Tiles Entfernung steigt der Balken leicht (+5/s), beim direkten Vorbeigehen (<= 2 Tiles) deutlich schneller (+20/s). Zudem schlagen sie im Normalzustand ab 3 Tiles Entfernung die Richtung des Spielers ein; während einer aktiven Infiltration schlagen alle Drohnen im Umkreis einer halben Bildschirmlänge (~25 Tiles) sofort den Weg zum Spieler ein.

4. **Fake-3D Audio System (`SoundManager`):**
   - Lade-Routinen in `src/core/sound_manager.py` implementiert. 
   - Dynamisches Panning (Left/Right) und Entfernungs-Dämpfung.
   - Numpy-basiertes Anti-Audio-Fatigue (generiert beim Start 3 Pitch-Variationen pro Sound).
   - **Verdrahtung:**
     - `player.wav`: Kontinuierlich beim Laufen (300 ms Loop, 20 % Volume).
     - `set mark.wav`: Klick auf Map / Target-Set.
     - Zivilisten (30 % Vol): Erhalten bei Spawn zufällig `move 1` oder `move 2` und triggern diesen beim Laufen.
     - Guardians (40 % Vol): Triggern `guardian.wav` beim Patrouillieren.
     - `success.wav`: 100 % Infiltration abgeschlossen.
     - `alert.wav`: Threat Level erreicht 100 %.
     - `death.wav`: Game Over Event (Gefasst oder beim Hacken gesehen).
     - `alert_trigger`: "alert"
     - `game_over`: "death"
     - `action_cancel`: "fail"
     - `threat_pulse`: "thread" (Spielt stufenweise ab 10 % Threat; Frequenz & Lautstärke steigen mit Füllstand bis zu 0.1s bei 90 %)
     - `infiltrate_1` & `infiltrate_2`: Randomisierter Wechsel alle 0.4s während der laufenden Infiltration (stoppt bei Pause).

5. **In-Game Game Over Overlay (`GameOverMenu`):**
   - Das alte Game-Over-State wurde entfernt.
   - Ein In-Game Overlay im Cyberpunk-Stil blockiert bei Kollision/Erwischtwerden die Steuerung und zeigt den "RETRY"-Knopf.
   - Klick auf "RETRY" setzt den Zustand (`init()`) nahtlos zurück und behält `data_fragments` bei.

6. **Canvas Resolution Standard (640x360 Native Canvas):**
   - Offizieller Native Canvas Standard auf **640x360** (16:9 Widescreen) festgelegt.
   - Skaliert perfekt per Integer-Faktor (3x auf 1080p Full HD, 4x auf 1440p QHD, 6x auf 4K UHD).
   - HUD Anchors (Threat Meter oben rechts, Terminal-Log unten links), ActionMenu Drag & Drop, Hacking-Minispiel und GameOver-Menü vollständig auf 640x360 ausgerichtet.
   - Dynamische Maus-Koordinaten-Transformation (`int(mx * 640 / window_w)`, `int(my * 360 / window_h)`) implementiert.

7. **IoT Surveillance Nodes (Watcher, Listener, Scanner):**
   - **Watcher (`watcher.png`) & Listener (`listener.png`):** 16x16 px Sprites, gedockt an Wand-Knoten mit 1 Spurbreite Abstand zum Pfad. Ein Trace-Stub führt vom Pfad exakt an den Rand des Sprites. Werden per Klick anvisiert und vom angrenzenden Trassen-Tile aus infiltriert.
   - **Scanner (`scanner.png`):** 16x16 px Checkpoint mitten auf den Pfad-Trassen (`floor`). Reduziert die Geschwindigkeit von Spieler und Zivilisten um genau die Hälfte (50 % Tempo) und steigert das globale Threat-Level beim Betreten langsam (+6.0/s). Momentan nicht hackbar.

## Ausstehende Tasks (Für den Start der nächsten Session)
- **Action Menu [HIJACK]:**
  - Implementierung der letalen Tötungs-Mechanik.
  - Zuteilung des kompletten Loot-Pools.
  - Sofortige Eskalation des Threat-Levels auf 100 % (oder direkte Drohnen-Hatz).
