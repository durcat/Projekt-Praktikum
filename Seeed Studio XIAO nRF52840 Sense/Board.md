Das Board was wir benutzen ist "Seeed Studio XIAO nRF52840 Sense"

Wir haben einen 3,7V 100mAh Akku 

die frage ist wie wir es schaffen das board mit dem 3,7V akku zu powern sodass Bluetooth live funktioniert und auch der 6 Achsen GIRO sensor auch. Außerdem brachen wir die Akkuladefunktion des baords, sodass wir den akku umstecken können um ihn nach nöten durch das board per USBc zu laden.

geht unser vorhaben und wenn ja wie machen wir das (der akku hat nur 1 plus und 1 minus)

---

## Antwort

### Kurz: Ja, das geht – und zwar genau so, wie das Board dafür gebaut ist

Der XIAO nRF52840 Sense hat **eine eingebaute Ladeschaltung für eine einzellige LiPo/Li-Ion-Zelle (3,7 V nominal, 4,2 V voll)** (Lade-IC BQ25101). Unser 3,7 V / 100 mAh Akku passt dazu. Dass der Akku nur Plus und Minus hat, ist normal und reicht aus. Mehr braucht das Board nicht.

Mit Akku läuft das komplette Board: Der Akku versorgt über den Spannungsregler den nRF52840 (also auch Bluetooth) und den 6-Achsen-IMU (LSM6DS3TR-C, Beschleunigung + Gyroskop). Wird USB-C eingesteckt, versorgt USB das Board und **lädt gleichzeitig den Akku**, ohne dass wir etwas umbauen müssen.

### Wie wir den Akku anschließen

1. **Auf der Rückseite des Boards gibt es zwei Lötpads: `BAT+` und `BAT-`.** Dort wird der Akku angelötet: Plus an `BAT+`, Minus an `BAT-`.
2. **Damit wir den Akku abstecken können:** Nicht den Akku direkt anlöten, sondern ein kurzes Kabel mit einem kleinen Stecker (z. B. JST-PH 2.0 mm oder JST-SH 1.0 mm, passend zum Stecker am Akku) an die Pads löten. Dann kann der Akku jederzeit ab- und wieder angesteckt werden.
3. **⚠️ Polarität vor dem ersten Einstecken mit dem Multimeter prüfen.** Die Kabelfarben bzw. die Belegung bei JST-Akkus sind nicht einheitlich. Ein verpolter Akku kann das Board sofort zerstören. Am besten vorher nachmessen und den Stecker markieren.
4. **Optional, aber empfehlenswert:** Einen kleinen Schiebeschalter in die Plus-Leitung (zwischen Akku und `BAT+`) setzen. Das Board hat keinen eigenen Ein/Aus-Schalter und zieht sonst dauerhaft Strom, bis der Akku leer ist.
5. Der Akku sollte eine **Schutzschaltung (PCM)** gegen Tiefentladung/Kurzschluss haben. Bei den meisten kleinen LiPos mit Kabel ist die als kleine Platine unter dem Schrumpfschlauch schon eingebaut, das sollten wir aber nachprüfen.

### Laden über USB-C

- Akku angeschlossen lassen und USB-C einstecken. Das Board lädt automatisch.
- Während des Ladens leuchtet die **rote LED neben dem USB-Anschluss**. Ist sie aus, ist der Akku voll.
- Das Board darf während des Ladens normal weiterlaufen (Bluetooth und IMU funktionieren weiter).
- **Ladestrom:** Standardmäßig lädt das Board mit **50 mA**. Für unseren 100 mAh Akku ist das ideal (0,5 C, schonend, voll in ca. 2–3 h). Man kann per Software auf 100 mA umschalten (Pin `P0.13` auf LOW), das wäre bei 100 mAh aber schon 1 C. **Empfehlung: bei 50 mA bleiben.**

### Akkuspannung im Code auslesen (optional, z. B. um den Ladestand per Bluetooth mitzuschicken)

- Die Akkuspannung liegt über einen Spannungsteiler an Pin `P0.31` (analog lesbar).
- Dafür muss Pin **`P0.14` (VBAT_ENABLE) auf LOW** gesetzt werden.
- **⚠️ Wichtig:** `P0.14` nicht auf HIGH setzen, solange ein Akku dranhängt (vor allem beim Laden). Laut Seeed-Wiki kann sonst eine zu hohe Spannung an `P0.31` anliegen und den Pin beschädigen. Einfach `P0.14` dauerhaft auf LOW lassen.

### Wie lange hält der Akku?

Grobe Schätzung, die wir messen sollten: Bluetooth-Verbindung plus IMU-Streaming braucht je nach Senderate und Software (mbed-Core vs. Adafruit-basierter Core) ungefähr **5–15 mA** im Schnitt. Das wären bei 100 mAh **etwa 6–20 Stunden**. Für einen Versuch/Messreihe reicht das. Wer länger braucht, kann die Senderate senken oder den Sleep-Modus nutzen.

### Software-Hinweis

- Für den IMU gibt es die Seeed-Bibliothek `Seeed_Arduino_LSM6DS3`, für Bluetooth `ArduinoBLE` (mit dem Boardpaket **„Seeed nRF52 mbed-enabled Boards“** in der Arduino IDE, Board „Seeed XIAO BLE Sense“).
- Der IMU wird von der Bibliothek selbst eingeschaltet. Dafür müssen wir nichts extra verkabeln.

### Checkliste

- [ ] Prüfen, ob der Akku eine Schutzschaltung hat
- [ ] Polarität des Akkusteckers mit dem Multimeter messen und markieren
- [ ] Gegenstück-Stecker an `BAT+` / `BAT-` (Rückseite) anlöten
- [ ] Optional: Schiebeschalter in die Plus-Leitung
- [ ] Testen: Board läuft nur mit Akku, Bluetooth + IMU senden
- [ ] Testen: USB-C rein → rote LED an → lädt
- [ ] Laufzeit einmal messen (Akku voll → bis Board ausgeht)

Quelle: Seeed Studio Wiki, „Getting Started with Seeed Studio XIAO nRF52840 (Sense)“, Abschnitt Battery Charging / Battery Voltage.