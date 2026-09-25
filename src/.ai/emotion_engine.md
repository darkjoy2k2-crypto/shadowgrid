# Entwicklungsplan: Jacks EmotionEngine & Persönlichkeits-Modell

> **Status:** Planungs- und Konzeptphase (Keine Code-Änderungen in `src/*.py` in diesem Schritt)  
> **Ziel:** Ein mathematisch fundiertes, KI-unterstütztes und narrativ tiefes Emotions- und Wahrnehmungssystem für Jack, die "2. Gedankenstimme" des Spielers.

---

## 1. Vision & Narratives Konzept

### 1.1 Jacks Rolle als 2. Gedankenstimme
Jack ist nicht nur eine passive UI-Anzeige, sondern fungiert als die **zweite Gedankenstimme des Spielers**. 
* Er nimmt die Spielwelt synchron zum Spieler wahr.
* Er reflektiert, hinterfragt und kommentiert, was auf dem Bildschirm passiert.
* Sein Verhalten wirkt lebhaft, abwechslungsreich und emotional synchron mit den Aktionen des Spielers.

### 1.2 Wahrnehmung & Das Existenz-Log ("Truman-Show"-Effekt)
* **Session-basiertes Log:** Jede Anwendungs-Session (vom Start bis zum Schließen) zeichnet ein lückenloses Protokoll auf.
* **Filter auf Wahrnehmbares:** Logged wird ausschließlich, was der Spieler audiophil und visuell wahrnehmen kann (Sound-Events, Grafik-Veränderungen, UI-Gleiten, Mausbewegungen, Hover über Elemente) sowie direkte Spielereingaben. Versteckte Systemzustände (z. B. Unsichtbare Bedrohungs-Timer) werden ignoriert, solange keine Warnung/Alarm im Spiel zu sehen/hören ist.
* **Meta-Narrativ:** Das Log wird im Spielverzeichnis gespeichert. Findet der Spieler (oder Jack selbst) diese Logs früherer Leben, löst dies existenzielle Krisen, Entfremdung und Zweifel aus ("Bin ich real oder nur ein Skript?").

---

## 2. Mathematisches Zustandsmodell (3-Achsen Emotions-Synthesizer)

Um starres Event-Swapping zu vermeiden, wird Jacks innerer Zustand kontinuierlich durch einen 3D-Vektor im Zustandsraum gesteuert.

### 2.1 Die 3 kontinuierlichen Dimensionen
1. **Valenz ($V \in [-100, +100]$):** Grundstimmung.
   * $+100$: Triumphal, überlegen, hämisch grinsend.
   * $0$: Neutral, berechnend.
   * $-100$: Trauer, Niedergeschlagenheit, Verzweiflung.
2. **Arousal / Stress ($A \in [0, 100]$):** Erregung & Adrenalinlevel.
   * $0$: Gelassen, ruhig, fokussiert.
   * $100$: Schock, Panik, Rage, Hektik.
3. **Physische Integrität / HP ($H \in [0, 100]$):** Hardware-/Gesundheitszustand des Deckers.
   * Steuert zusätzlich Schmerz-, Verletzungs- und Todes-Overlays.

### 2.2 Dynamik: Vektor-Impulse & Decay (Dämpfung)
* **Spielreize als Vektoren:** Jedes relevante Ereignis sendet einen Impuls $\Delta \vec{E} = (\Delta V, \Delta A, \Delta H)$, der direkt auf den aktuellen Zustand addiert wird:
  $$\vec{S}_{t+1} = \vec{S}_t + \Delta \vec{E}$$
* **Decay (Dämpfung):** In jedem Bewertungs-Tick (mindestens $1 \times$ pro Sekunde) zieht ein Dämpfungsfaktor den Zustand sanft zu Jacks Basis-Persönlichkeit (z. B. leicht zynisch-neutral) zurück:
  $$V_{t+1} = V_t + \gamma \cdot (V_{\text{basis}} - V_t)$$

### 2.3 Beispiel-Reize im Gameplay
* **Herumlaufen / Exploration:** Erhöht Neugier (Arousal moderat, Valenz leicht positiv).
* **Zickzack / Hektische Richtungswechsel:** Erhöht Genervtheit / Stress ($A \uparrow$, $V \downarrow$).
* **Lange Laufwege (Pathfinding):** Steigert Unmut / Wut ($V \downarrow$).
* **Begegnung mit Civs / unbekannten Nodes:** Erzeugt Erstaunen & Fragezeichen ($A \uparrow$, $V$ neutral bis neugierig).

---

## 3. Visuelle Präsentation (Porträts & Spiegelung)

### 3.1 Porträt-Set (19 Zustände)
* **18 emotionale Ausdrücke:** Gezielte Nuancen von Neutral, Neugierig, Hämisch, Schockiert, Wütend, Traurig, Panisch etc.
* **1 Zustand Tod (19. Porträt):** Ein rein physischer Endzustand ($H = 0$), auf den Jack emotional keinen direkten Einfluss hat.

### 3.2 2-Stufen-Projektion & Spiegelung (Varianz-Maximierung)
1. **Zustands-Mapping:** Der 3D-Vektor $(V, A, H)$ wird über Schwellenwerte oder Nächste-Nachbar-Distanz (Euclidean Distance im Emotionsraum) auf eines der 18 Porträts abgebildet.
2. **Haltungs-Korrektur & Spiegelung (Horizontal Flip):**
   * **Standard-Haltung:** Der *neutrale Blick* bildet die primäre Ruhebasis.
   * **Horizontale Spiegelung:** Da viele Porträts eine geneigte Blickhaltung besitzen, werden diese dynamisch horizontal gespiegelt, um eine doppelte visuelle Varianz zu erzeugen und Monotonie zu verhindern.

---

## 4. Narratives Wende- & Erfahrungssystem

### 4.1 Erfahrungspools
Jack startet nicht als Allwissender ("Besserwisser"), sondern schaltet Erkenntnisse erst frei, wenn er durch Log-Analysen und Sessions ausreichend Erfahrung mit Objekten/Mechaniken gesammelt hat.

### 4.2 Beispielszenario einer emotionalen Wendung
1. **Phase 1 (Gier & Jagd):** Jack hält wandernde Nodes für bloße NPCs. Er lernt, sie zu bestehlen/auszunehmen. Das bringt Loot $\rightarrow$ Valenz positiv, Gier steigt.
2. **Phase 2 (Erkenntnis & Schock):** Jack schaltet durch Upgrade die Fähigkeit frei, Datafragments zu lesen und Stimmen zu hören. Er erkennt: Es sind echte Menschen (darunter Familien/Zivilisten).
3. **Phase 3 (Trauma & Panik):** Der Emotions-Synthesizer erfährt einen dauerhaften Verschiebungsimpuls. Zwingt der Spieler Jack fortan dazu, Civs zu bestehlen, reagiert Jack mit Panik ($A \uparrow \uparrow$), Verzweiflung ($V \downarrow \downarrow$) und ethischem Widerstand in seinen Gedanken.

---

## 5. KI- / ML-Architektur & Textgenerierung

### 5.1 Zwei getrennte Aufgabenbereiche
* **Aufgabe A: Emotions-Klassifikation & Vektor-Mapping (Porträt)**
* **Aufgabe B: Gedankentext-Generierung (Jacks Monologe)**

### 5.2 Technologischer Ansatz
```
[ Spiel-Events & Input ]
          │
          ▼
[ Session-Log / Feature Extraction ]
          │
          ▼
[ 3-Achsen Emotions-Synthesizer (V, A, H) ]
          │
    ┌─────┴───────────────────────────────┐
    ▼                                     ▼
[ Porträt-Klassifikator ]       [ Text-Generierung ]
  - Nächster Nachbar / Rules       - Ansatz A: Template-System (Schnell, robust)
  - LightGBM / ONNX Runtime        - Ansatz B: Fine-Tuned Small LLM (LoRA/ONNX)
    │                                     │
    ▼                                     ▼
[ UI: Porträt + Flip ]          [ UI: Gedankenblase / Text ]
```

* **Offline-Training & Runtime-Inferenz:** Python wird für Log-Auswertung, Feature-Extraction und Modell-Training genutzt. Das Modell wird als `.onnx` exportiert und kann direkt ressourcensparend in der Engine ausgeführt werden.

---

## 6. Feststehende Schritte & Refactoring-Strategie

1. **Clean Slate (Bereinigung):**
   * Alle veralteten/provisorischen Ansätze der `EmotionEngine` im Code werden entfernt und in `.ai/` archiviert.
   * Globale Variablen, die Entitäten direkt mit Emotionen verkoppeln, werden entfernt.
2. **Saubere Schnittstelle (Perception Interface):**
   * Aufbau des zentralen Wahrnehmungsspeichers (Session-Log).
   * Trennung von normalen Spiel-Debug-Logs und Jacks In-Game-Wahrnehmung.
3. **Engine-Implementierung:**
   * Entkoppelte `EmotionEngine`, die $1 \times$ pro Sekunde den Vektor evaluiert, den Dämpfungsfaktor anwendet und die UI (Porträt + Gedanken) aktualisiert.

---
*Dieser Plan dient als abgestimmte Architektur-Grundlage vor Beginn der ersten Python-Codeänderungen.*
