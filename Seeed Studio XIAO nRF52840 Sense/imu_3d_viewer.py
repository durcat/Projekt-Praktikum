"""Wertet eine IMU-Messung des XIAO nRF52840 Sense aus (CSV von ble_empfang.py),
plottet die Rohdaten und spielt die Bewegung des Boards als 3D-Simulation ab.

    python imu_3d_viewer.py                      # nimmt testmessung1.csv
    python imu_3d_viewer.py messung2.csv
    python imu_3d_viewer.py messung2.csv --gyro-einheit deg
    python imu_3d_viewer.py --weg roh            # Position ohne Driftkorrektur

CSV-Spalten:
    t_s         Empfangszeit am PC in s (nicht die Messzeit am Board!)
    ax, ay, az  Beschleunigung im Board-Koordinatensystem in m/s^2
                (Ruhe, flach liegend: az ~ +9.81, misst also die Gegenkraft zur Schwerkraft)
    gx, gy, gz  Drehrate um die Board-Achsen in rad/s

Bedienung im 3D-Fenster:
    Leertaste       Play / Pause
    Pfeil links/rechts   einen Messpunkt zurück / vor
    r               rückwärts abspielen
    Pos1 / Ende     an den Anfang / ans Ende springen
    Maus            3D-Ansicht drehen / zoomen

Verlässlich ist vor allem die Lage (Orientierung). Die Position stammt aus
doppelter Integration der Beschleunigung und ist nur eine grobe Schätzung,
siehe entferne_drift().
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Button, CheckButtons, Slider
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.integrate import cumulative_trapezoid
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.transform import Rotation

STANDARD_CSV = Path(__file__).with_name("messungpe_1.csv")

# Abmessungen XIAO nRF52840 Sense in mm (Platine ohne Bauteile)
BOARD_L, BOARD_B, BOARD_H = 21.0, 17.5, 3.5

FARBE_X, FARBE_Y, FARBE_Z = "#d62728", "#2ca02c", "#1f77b4"


# ---------------------------------------------------------------------------
# Auswertung
# ---------------------------------------------------------------------------

def lade_messung(pfad, gyro_einheit="rad"):
    df = pd.read_csv(pfad)
    t = df["t_s"].to_numpy(float)
    acc = df[["ax", "ay", "az"]].to_numpy(float)
    gyr = df[["gx", "gy", "gz"]].to_numpy(float)
    if gyro_einheit == "deg":
        gyr = np.radians(gyr)

    # BLE liefert die Zeilen gebündelt (Verbindungsintervall ~30 ms), die
    # Empfangszeiten springen deshalb. Das Board misst aber gleichmäßig,
    # also wird die Zeitachse durch eine Ausgleichsgerade ersetzt.
    i = np.arange(len(t))
    steigung, achse = np.polyfit(i, t, 1)
    t_gleich = achse + steigung * i
    t_gleich -= t_gleich[0]
    return t, t_gleich, acc, gyr


def finde_ruhe(acc, gyr, fenster=7, a_std_max=0.25, w_max=0.15):
    """Ruhephasen: |a| schwankt kaum und das Board dreht sich (fast) nicht."""
    a_betrag = np.linalg.norm(acc, axis=1)
    mittel = uniform_filter1d(a_betrag, fenster, mode="nearest")
    std = np.sqrt(np.maximum(uniform_filter1d(a_betrag**2, fenster, mode="nearest") - mittel**2, 0))
    w_betrag = maximum_filter1d(np.linalg.norm(gyr, axis=1), fenster, mode="nearest")
    return (std < a_std_max) & (w_betrag < w_max)


def segmente(maske):
    """Liefert (start, ende)-Indexpaare zusammenhängender True-Bereiche."""
    rand = np.diff(np.concatenate([[0], maske.astype(int), [0]]))
    return list(zip(np.flatnonzero(rand == 1), np.flatnonzero(rand == -1) - 1))


def mahony_filter(t, acc, gyr, g_ref, ruhe, kp_bewegung=1.0, kp_ruhe=5.0):
    """Orientierung (Board -> Welt) aus Gyro, mit der Schwerkraft als Korrektur.

    Das Gyro allein driftet, der Beschleunigungssensor allein ist bei Bewegung
    verfälscht. Der Mahony-Filter integriert das Gyro und zieht die Lage
    langsam zur gemessenen Schwerkraftrichtung, umso stärker, je näher |a| an g ist.
    Die Drehung um die senkrechte Achse (Gier) ist ohne Magnetometer nicht
    korrigierbar und kann driften.
    """
    n = len(t)
    a0 = acc[ruhe][:5].mean(axis=0) if ruhe[:5].any() else acc[0]
    q, _ = Rotation.align_vectors([[0, 0, 1]], [a0 / np.linalg.norm(a0)])
    lagen = [q]
    for k in range(1, n):
        dt = t[k] - t[k - 1]
        a_betrag = np.linalg.norm(acc[k])
        w = 0.5 * (gyr[k] + gyr[k - 1])
        if a_betrag > 1e-6:
            gewicht = max(0.0, 1.0 - abs(a_betrag - g_ref) / (0.3 * g_ref))
            kp = kp_ruhe if ruhe[k] else kp_bewegung * gewicht
            oben_geschaetzt = q.inv().apply([0, 0, 1])
            w = w + kp * np.cross(acc[k] / a_betrag, oben_geschaetzt)
        q = q * Rotation.from_rotvec(w * dt)
        lagen.append(q)
    return Rotation.concatenate(lagen)


def integriere_weg(t, a_welt, ruhe):
    """Doppelintegration mit Nullgeschwindigkeits-Korrektur (ZUPT).

    In Ruhephasen ist v = 0. Zwischen zwei Ruhephasen wird die Geschwindigkeit
    linear so korrigiert, dass sie am Ende wieder 0 ist. Das entfernt den
    größten Teil der Drift, trotzdem ist der Weg nur eine grobe Schätzung.
    """
    v = np.zeros_like(a_welt)
    for s, e in segmente(~ruhe):
        s0 = max(s - 1, 0)
        v_seg = cumulative_trapezoid(a_welt[s0:e + 2], t[s0:e + 2], axis=0, initial=0)
        if e + 1 < len(t):  # Segment endet in Ruhe -> Drift abziehen
            anteil = (t[s0:e + 2] - t[s0]) / (t[min(e + 1, len(t) - 1)] - t[s0])
            v_seg -= anteil[:, None] * v_seg[-1]
        v[s0:e + 2] = v_seg
    v[ruhe] = 0
    return v, cumulative_trapezoid(v, t, axis=0, initial=0)


def entferne_drift(t, pos, ruhe, grenzfrequenz=0.4):
    """Hochpass auf die Position jedes Bewegungsabschnitts.

    Schon kleine Lagefehler (1° bei 3 g Schütteln = 0.5 m/s^2 Fehlbeschleunigung)
    lassen die Doppelintegration in Sekunden um Meter weglaufen. Übrig bleibt
    nur der schwingende Anteil (oberhalb der Grenzfrequenz), und jeder Abschnitt
    endet wieder am Startpunkt. Annahme: das Board bewegt sich hin und her,
    kommt aber nicht netto woanders an.
    """
    fs = (len(t) - 1) / (t[-1] - t[0])
    sos = butter(2, grenzfrequenz, "highpass", fs=fs, output="sos")
    korrigiert = np.zeros_like(pos)
    for s, e in segmente(~ruhe):
        s0, e1 = max(s - 1, 0), min(e + 2, len(t))
        if e1 - s0 < 16:  # zu kurz zum Filtern
            continue
        seg = sosfiltfilt(sos, pos[s0:e1], axis=0)
        seg -= np.linspace(seg[0], seg[-1], len(seg))
        korrigiert[s0:e1] = seg
    return korrigiert


def auswerten(pfad, gyro_einheit="rad", weg="hochpass"):
    t_empf, t, acc, gyr = lade_messung(pfad, gyro_einheit)
    ruhe = finde_ruhe(acc, gyr)
    if not ruhe.any():
        print("Warnung: keine Ruhephase gefunden, Gyro-Offset und g werden nicht kalibriert.")
        bias, g_ref = np.zeros(3), 9.81
    else:
        bias = gyr[ruhe].mean(axis=0)
        g_ref = np.linalg.norm(acc[ruhe], axis=1).mean()
    gyr_k = gyr - bias

    lagen = mahony_filter(t, acc, gyr_k, g_ref, ruhe)
    a_welt = lagen.apply(acc) - [0, 0, g_ref]
    a_welt[ruhe] = 0
    v, pos = integriere_weg(t, a_welt, ruhe)
    if weg == "hochpass":
        pos = entferne_drift(t, pos, ruhe)

    print(f"{len(t)} Messpunkte, {t[-1]:.2f} s, Abtastrate ~{(len(t) - 1) / t[-1]:.1f} Hz")
    print(f"Gyro-Offset: {np.round(bias, 4)} rad/s,  g gemessen: {g_ref:.3f} m/s^2")
    for s, e in segmente(~ruhe):
        print(f"Bewegung {t[s]:6.2f} s - {t[e]:6.2f} s")
    print(f"Weg-Ausdehnung: {np.ptp(pos, axis=0).round(3)} m (x, y, z)")

    return dict(t=t, t_empf=t_empf, acc=acc, gyr=gyr_k, ruhe=ruhe, lagen=lagen,
                euler=lagen.as_euler("xyz", degrees=True), a_welt=a_welt, v=v, pos=pos,
                g_ref=g_ref, name=Path(pfad).name)


# ---------------------------------------------------------------------------
# Übersichtsplot
# ---------------------------------------------------------------------------

def schattiere_ruhe(ax, t, ruhe):
    for s, e in segmente(ruhe):
        ax.axvspan(t[s], t[e], color="0.85", lw=0, zorder=0)


def uebersicht(d):
    t = d["t"]
    fig, axs = plt.subplots(5, 1, figsize=(11, 11), sharex=True, constrained_layout=True)
    fig.suptitle(f"{d['name']}  (grau = Ruhephase)")
    zeilen = [
        (d["acc"], "Beschleunigung\n(Board) [m/s²]", ["a_x", "a_y", "a_z"]),
        (d["gyr"], "Drehrate\n(Board) [rad/s]", ["ω_x", "ω_y", "ω_z"]),
        (d["euler"], "Lage [°]", ["Rollen (x)", "Nicken (y)", "Gieren (z)"]),
        (d["a_welt"], "Beschl. ohne g\n(Welt) [m/s²]", ["x", "y", "z"]),
        (d["pos"] * 100, "Position\n(geschätzt) [cm]", ["x", "y", "z"]),
    ]
    for ax, (werte, label, namen) in zip(axs, zeilen):
        schattiere_ruhe(ax, t, d["ruhe"])
        for j, farbe in enumerate([FARBE_X, FARBE_Y, FARBE_Z]):
            ax.plot(t, werte[:, j], color=farbe, lw=1.2, label=namen[j])
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=8, ncol=3, frameon=False)
    axs[0].plot(t, np.linalg.norm(d["acc"], axis=1), color="0.3", lw=0.8, ls="--", label="|a|")
    axs[0].legend(loc="upper right", fontsize=8, ncol=4, frameon=False)
    axs[-1].set_xlabel("Zeit [s]")
    return fig


# ---------------------------------------------------------------------------
# 3D-Viewer
# ---------------------------------------------------------------------------

def quader(l, b, h):
    """Ecken und Flächen eines Quaders um den Ursprung."""
    x, y, z = l / 2, b / 2, h / 2
    ecken = np.array([[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z],
                      [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]])
    flaechen = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
    return ecken, flaechen


class Viewer:
    BILD_MS = 33  # Timer-Intervall

    def __init__(self, d):
        self.d = d
        self.t = d["t"]
        self.n = len(self.t)
        self.k = 0
        self.zeit = 0.0
        self.richtung = 1
        self.laeuft = False
        self.zeige_weg = True
        self.zeige_spur = False
        self.mit_position = True
        self._slider_intern = False

        # Platz für Bewegung: Board-Größe an die Ausdehnung des Wegs anpassen (in cm)
        self.pos = d["pos"] * 100
        ausdehnung = max(np.ptp(self.pos, axis=0).max(), 5.0)
        self.massstab = 0.25 * ausdehnung / BOARD_L
        self.ecken, self.flaechen = quader(BOARD_L * self.massstab, BOARD_B * self.massstab,
                                           BOARD_H * self.massstab)
        usb_l = 4 * self.massstab
        self.usb_ecken, _ = quader(usb_l, 9 * self.massstab, 3 * self.massstab)
        self.usb_ecken += [BOARD_L * self.massstab / 2 - usb_l / 2 + usb_l * 0.4, 0,
                           BOARD_H * self.massstab]
        self.pfeil_l = 0.8 * BOARD_L * self.massstab
        # Spitze = Ende der Board-x-Achse (USB-Seite), zeigt wie das Board kippt
        self.spur = self.pos + d["lagen"].apply([self.pfeil_l, 0, 0])
        self.spur_ohne_pos = d["lagen"].apply([self.pfeil_l, 0, 0])

        self._baue_fenster()
        self._zeichne(0)

    # --- Aufbau -----------------------------------------------------------
    def _baue_fenster(self):
        d = self.d
        self.fig = plt.figure(figsize=(14, 8.5))
        self.fig.canvas.manager.set_window_title(f"IMU 3D – {d['name']}")
        self.ax3 = self.fig.add_axes([0.0, 0.17, 0.6, 0.8], projection="3d")

        self.board = Poly3DCollection([], facecolors="#2e7d32", edgecolors="k", linewidths=0.6, alpha=0.95)
        self.usb = Poly3DCollection([], facecolors="#9e9e9e", edgecolors="k", linewidths=0.5)
        self.ax3.add_collection3d(self.board)
        self.ax3.add_collection3d(self.usb)
        self.pfeile = [self.ax3.plot([], [], [], color=f, lw=2.5)[0] for f in (FARBE_X, FARBE_Y, FARBE_Z)]
        self.weg_linie, = self.ax3.plot([], [], [], color="#ff7f0e", lw=1.8, label="Weg (Mittelpunkt)")
        self.spur_linie, = self.ax3.plot([], [], [], color="#9467bd", lw=1.2, label="Spur der x-Spitze")
        self.punkt, = self.ax3.plot([], [], [], "o", color="#ff7f0e", ms=4)
        self.ax3.plot([], [], color=FARBE_X, lw=2.5, label="Board x (USB)")
        self.ax3.plot([], [], color=FARBE_Y, lw=2.5, label="Board y")
        self.ax3.plot([], [], color=FARBE_Z, lw=2.5, label="Board z")
        self.ax3.legend(loc="upper left", fontsize=8)
        self.ax3.set_xlabel("x [cm]")
        self.ax3.set_ylabel("y [cm]")
        self.ax3.set_zlabel("z [cm]")
        self._setze_grenzen()
        self.info = self.ax3.text2D(0.98, 0.98, "", transform=self.ax3.transAxes, ha="right", va="top",
                                    family="monospace", fontsize=9)

        # Zeitreihen rechts mit mitlaufendem Cursor
        t = self.t
        reihen = [(d["acc"], "a (Board) [m/s²]"), (d["gyr"], "ω (Board) [rad/s]"), (d["euler"], "Lage [°]"),
                  (self.pos, "Position [cm]")]
        self.cursor = []
        hoehe = 0.18
        for j, (werte, label) in enumerate(reihen):
            ax = self.fig.add_axes([0.66, 0.79 - j * (hoehe + 0.025), 0.32, hoehe])
            schattiere_ruhe(ax, t, d["ruhe"])
            for i, f in enumerate((FARBE_X, FARBE_Y, FARBE_Z)):
                ax.plot(t, werte[:, i], color=f, lw=1)
            ax.set_ylabel(label, fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
            ax.set_xlim(t[0], t[-1])
            if j < len(reihen) - 1:
                ax.tick_params(labelbottom=False)
            self.cursor.append(ax.axvline(0, color="k", lw=1))
        ax.set_xlabel("Zeit [s]", fontsize=8)

        # Bedienelemente
        self.slider = Slider(self.fig.add_axes([0.08, 0.1, 0.5, 0.03]), "Zeit [s]", t[0], t[-1], valinit=0)
        self.slider.on_changed(self._slider_bewegt)
        self.tempo = Slider(self.fig.add_axes([0.08, 0.055, 0.2, 0.025]), "Tempo", 0.1, 4.0, valinit=1.0)

        knoepfe = [("|◀", self._an_anfang), ("◀◀", self._rueckwaerts), ("◀|", lambda _: self._schritt(-1)),
                   ("▶ / ❚❚", self._play_pause), ("|▶", lambda _: self._schritt(1)), ("▶▶", self._vorwaerts),
                   ("▶|", self._ans_ende)]
        self.knoepfe = []
        for i, (text, aktion) in enumerate(knoepfe):
            b = Button(self.fig.add_axes([0.08 + i * 0.072, 0.01, 0.065, 0.035]), text)
            b.on_clicked(aktion)
            self.knoepfe.append(b)

        self.optionen = CheckButtons(self.fig.add_axes([0.33, 0.045, 0.27, 0.05]),
                                     ["Weg zeichnen", "Spur der Spitze", "Position verwenden"],
                                     [self.zeige_weg, self.zeige_spur, self.mit_position])
        self.optionen.on_clicked(self._option)
        for label in self.optionen.labels:
            label.set_fontsize(8)

        self.timer = self.fig.canvas.new_timer(interval=self.BILD_MS)
        self.timer.add_callback(self._tick)
        self.fig.canvas.mpl_connect("key_press_event", self._taste)

    def _setze_grenzen(self):
        punkte = np.vstack([self.pos, self.spur]) if self.mit_position else self.spur_ohne_pos
        mitte = (punkte.max(axis=0) + punkte.min(axis=0)) / 2
        r = max(np.ptp(punkte, axis=0).max() / 2, BOARD_L * self.massstab) * 1.15
        self.ax3.set_xlim(mitte[0] - r, mitte[0] + r)
        self.ax3.set_ylim(mitte[1] - r, mitte[1] + r)
        self.ax3.set_zlim(mitte[2] - r, mitte[2] + r)
        self.ax3.set_box_aspect((1, 1, 1))

    # --- Zeichnen ---------------------------------------------------------
    def _zeichne(self, k):
        self.k = k
        lage = self.d["lagen"][k]
        mitte = self.pos[k] if self.mit_position else np.zeros(3)
        ecken = lage.apply(self.ecken) + mitte
        usb = lage.apply(self.usb_ecken) + mitte
        self.board.set_verts([ecken[f] for f in self.flaechen])
        self.usb.set_verts([usb[f] for f in self.flaechen])
        for pfeil, achse in zip(self.pfeile, np.eye(3)):
            ende = mitte + lage.apply(achse * self.pfeil_l)
            pfeil.set_data_3d(*np.c_[mitte, ende])

        weg = self.pos[:k + 1] if self.mit_position else np.zeros((1, 3))
        self.weg_linie.set_data_3d(*weg.T)
        self.weg_linie.set_visible(self.zeige_weg)
        self.punkt.set_data_3d(*weg[-1:].T)
        self.punkt.set_visible(self.zeige_weg)
        spur = (self.spur if self.mit_position else self.spur_ohne_pos)[:k + 1]
        self.spur_linie.set_data_3d(*spur.T)
        self.spur_linie.set_visible(self.zeige_spur)

        tk = self.t[k]
        for c in self.cursor:
            c.set_xdata([tk, tk])
        r, p, y = self.d["euler"][k]
        zustand = "Ruhe" if self.d["ruhe"][k] else "Bewegung"
        modus = ("▶" if self.richtung > 0 else "◀") if self.laeuft else "❚❚"
        self.info.set_text(f"{modus}  t = {tk:6.2f} s   [{k + 1}/{self.n}]  {zustand}\n"
                           f"Rollen {r:7.1f}°  Nicken {p:7.1f}°  Gieren {y:7.1f}°\n"
                           f"Pos [cm] {self.pos[k][0]:6.1f} {self.pos[k][1]:6.1f} {self.pos[k][2]:6.1f}")

        self._slider_intern = True
        self.slider.set_val(tk)
        self._slider_intern = False
        self.fig.canvas.draw_idle()

    # --- Steuerung --------------------------------------------------------
    def _gehe_zu_zeit(self, zeit):
        self.zeit = float(np.clip(zeit, self.t[0], self.t[-1]))
        k = int(np.searchsorted(self.t, self.zeit, side="right") - 1)
        self._zeichne(int(np.clip(k, 0, self.n - 1)))

    def _tick(self):
        if not self.laeuft:
            return
        neu = self.zeit + self.richtung * self.tempo.val * self.BILD_MS / 1000
        if neu >= self.t[-1] or neu <= self.t[0]:
            self.laeuft = False
            self.timer.stop()
        self._gehe_zu_zeit(neu)

    def _starte(self, richtung):
        self.richtung = richtung
        if (richtung > 0 and self.k == self.n - 1) or (richtung < 0 and self.k == 0):
            self._gehe_zu_zeit(self.t[0] if richtung > 0 else self.t[-1])
        self.laeuft = True
        self.timer.start()

    def _anhalten(self):
        self.laeuft = False
        self.timer.stop()
        self._zeichne(self.k)

    def _play_pause(self, _=None):
        self._anhalten() if self.laeuft else self._starte(self.richtung)

    def _vorwaerts(self, _=None):
        self._starte(1)

    def _rueckwaerts(self, _=None):
        self._starte(-1)

    def _schritt(self, dk):
        self._anhalten()
        k = int(np.clip(self.k + dk, 0, self.n - 1))
        self.zeit = self.t[k]
        self._zeichne(k)

    def _an_anfang(self, _=None):
        self._anhalten()
        self._gehe_zu_zeit(self.t[0])

    def _ans_ende(self, _=None):
        self._anhalten()
        self._gehe_zu_zeit(self.t[-1])

    def _slider_bewegt(self, wert):
        if not self._slider_intern:
            self.zeit = wert
            k = int(np.clip(np.searchsorted(self.t, wert, side="right") - 1, 0, self.n - 1))
            self._slider_intern = True
            self._zeichne(k)
            self._slider_intern = False

    def _option(self, label):
        self.zeige_weg, self.zeige_spur, self.mit_position = self.optionen.get_status()
        if label == "Position verwenden":
            self._setze_grenzen()
        self._zeichne(self.k)

    def _taste(self, event):
        aktionen = {" ": self._play_pause, "right": lambda: self._schritt(1), "left": lambda: self._schritt(-1),
                    "r": self._rueckwaerts, "home": self._an_anfang, "end": self._ans_ende}
        if event.key in aktionen:
            aktionen[event.key]()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", nargs="?", default=STANDARD_CSV, help="Messdatei (Standard: testmessung1.csv)")
    parser.add_argument("--gyro-einheit", choices=["rad", "deg"], default="rad",
                        help="Einheit der Gyro-Spalten in der CSV (Standard: rad/s)")
    parser.add_argument("--weg", choices=["hochpass", "roh"], default="hochpass",
                        help="Position driftkorrigiert (Standard) oder rohe Doppelintegration")
    parser.add_argument("--speichern", action="store_true", help="Übersichtsplot zusätzlich als PNG speichern")
    args = parser.parse_args()

    d = auswerten(args.csv, args.gyro_einheit, args.weg)
    fig = uebersicht(d)
    if args.speichern:
        ziel = Path(args.csv).with_suffix(".png")
        fig.savefig(ziel, dpi=150)
        print(f"Übersicht gespeichert: {ziel}")
    viewer = Viewer(d)  # Referenz halten, sonst räumt Python Timer und Knöpfe weg
    plt.show()
    return viewer


if __name__ == "__main__":
    main()
