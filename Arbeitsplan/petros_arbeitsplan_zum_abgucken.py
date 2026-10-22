"""
Zeitplan Projektpraktikum als druckbares PDF und als Abbildung fürs Planungsdokument.
Daten: labor/zeitplan.csv (in VS Code bearbeiten).
Seite 1: Balkenplan (A4 quer) · Seite 2: chronologische Liste mit Häkchen „erledigt“.

Ausführen: .venv/bin/python labor/zeitplan.py  (VS-Code-Task „Projektpraktikum: Zeitplan aktualisieren“)
  → labor/Zeitplan.pdf, plots/zeitplan.pdf (Seite 1 allein, für kapitel/03_zeitplanung.tex)
"""
import csv
import locale
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

try:                                    # deutsche Monatsnamen auf der Zeitachse
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    pass

HIER = Path(__file__).resolve().parent
PLOTS = HIER.parent / "plots"
FARBE = {"Petros": "#5983b0", "Tobi": "#ff860d", "Beide": "#47d45a", "Anmeldung": "#a02b93", "Pause": "#ffe74c"}
WT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def datum(t):
    return datetime.strptime(t.strip(), "%d.%m.%Y").date()


with open(HIER / "zeitplan.csv", encoding="utf-8") as fh:
    zeilen_csv = list(csv.DictReader(z for z in fh if z.strip() and not z.startswith("#")))
PHASEN, MEILENSTEINE, PAUSEN, ERLEDIGT = [], [], [], set()
for z in zeilen_csv:
    art, name, wer = z["art"].strip(), z["aufgabe"].strip(), z["wer"].strip()
    if z.get("erledigt", "").strip().lower() in ("ja", "x", "1"):
        ERLEDIGT.add(name)
    if art == "phase":
        PHASEN.append((name, wer, datum(z["von"]), datum(z["bis"])))
    elif art == "abgabe":
        MEILENSTEINE.append((name, datum(z["von"]), wer))
    elif art == "pause":
        PAUSEN.append((datum(z["von"]), datum(z["bis"])))
alle = [p[2] for p in PHASEN] + [p[3] for p in PHASEN] + [m[1] for m in MEILENSTEINE]
START, ENDE = min(alle) - timedelta(3), max(alle) + timedelta(16)


def tg(d):
    return f"{WT[d.weekday()]} {d.day:02d}.{d.month:02d}.{str(d.year)[2:]}"


def kopf(fig, titel):
    fig.text(0.04, 0.955, titel, fontsize=15, weight="bold", va="center")
    fig.text(0.04, 0.925, "Projektpraktikum WS 26/27 · Sonnenflecken / Zeeman · Petros Kotsamanis & Tobias Vetter",
             fontsize=8.5, color="0.35", va="center")
    fig.text(0.96, 0.955, f"Stand {date.today():%d.%m.%Y}", fontsize=8, color="0.35", ha="right", va="center")


with PdfPages(HIER / "Zeitplan.pdf") as pdf:
    # ─── Seite 1: Balkenplan ─────────────────────────────────────────
    fig = plt.figure(figsize=(297 / 25.4, 210 / 25.4))
    kopf(fig, "Zeitplan")
    ax = fig.add_axes([0.25, 0.10, 0.72, 0.78])
    zeilen = [(p[0], "phase", p) for p in PHASEN] + [(m[0], "ms", m) for m in MEILENSTEINE]
    n = len(zeilen)
    num = mdates.date2num
    for p0, p1 in PAUSEN:
        ax.axvspan(num(p0), num(p1 + timedelta(1)), color=FARBE["Pause"], alpha=0.35, lw=0)
        ax.text(num(p0 + (p1 - p0) / 2), -0.9, "Winterpause", ha="center", fontsize=8, weight="bold")
    # Praktikumstage (donnerstags) als feine Linien
    d = START
    while d <= ENDE:
        if d.weekday() == 3:
            ax.axvline(num(d), color="0.88", lw=0.6, zorder=0)
        d += timedelta(1)
    ax.axhline(len(PHASEN) - 0.5, color="0.5", lw=0.6)
    for i, (name, art, z) in enumerate(zeilen):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="0.97", lw=0, zorder=0)
        if art == "phase":
            _, wer, a, b = z
            ax.barh(i, num(b + timedelta(1)) - num(a), left=num(a), height=0.62, color=FARBE[wer], ec="k", lw=0.4, zorder=3)
            ax.text(num(b + timedelta(1)) + 1, i, f"{a:%d.%m.} – {b:%d.%m.}", va="center", fontsize=6.3, color="0.3")
        else:
            _, t, wer = z
            ax.plot(num(t) + 0.5, i, marker="D", ms=7, color=FARBE[wer], mec="k", mew=0.5, zorder=4)
            ax.text(num(t) + 3, i, tg(t), va="center", fontsize=6.5, weight="bold")
    ax.set_yticks(range(n), [z[0] for z in zeilen], fontsize=8)
    ax.set_ylim(n - 0.5, -1.5)
    ax.set_xlim(num(START), num(ENDE))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.TH))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d."))
    ax.tick_params(axis="x", which="minor", labelsize=6, colors="0.4")
    ax.tick_params(axis="x", which="major", pad=12, labelsize=9)
    for g in [ax.xaxis]:
        g.grid(True, which="major", color="0.6", lw=0.8)
    ax.set_axisbelow(True)
    heute = date.today()
    if START <= heute <= ENDE:
        ax.axvline(num(heute), color="#c0392b", lw=1.2, ls="--", zorder=5)
        ax.text(num(heute), -1.2, "heute", color="#c0392b", fontsize=7, ha="center")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(-0.33, len(PHASEN) / 2 - 0.5, "Arbeitsphasen", transform=ax.get_yaxis_transform(), rotation=90,
            va="center", ha="center", fontsize=9, weight="bold", color="0.4")
    ax.text(-0.33, len(PHASEN) + len(MEILENSTEINE) / 2 - 0.5, "Abgaben / Meilensteine", transform=ax.get_yaxis_transform(),
            rotation=90, va="center", ha="center", fontsize=9, weight="bold", color="0.4")
    fig.legend(handles=[Patch(fc=FARBE["Petros"], ec="k", lw=0.4, label="Petros"),
                        Patch(fc=FARBE["Tobi"], ec="k", lw=0.4, label="Tobi"),
                        Patch(fc=FARBE["Beide"], ec="k", lw=0.4, label="Beide"),
                        Line2D([], [], marker="D", ls="", color=FARBE["Anmeldung"], mec="k", label="Anmeldung (Hochschulportal)"),
                        Line2D([], [], color="0.88", lw=2, label="Praktikumstag (Do 10–16 Uhr)")],
               loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.6, 0.0))
    pdf.savefig(fig)
    PLOTS.mkdir(exist_ok=True)
    fig.savefig(PLOTS / "zeitplan.pdf", facecolor="none")
    plt.close(fig)

    # ─── Seite 2: chronologische Liste ───────────────────────────────
    fig = plt.figure(figsize=(297 / 25.4, 210 / 25.4))
    kopf(fig, "Zeitplan – Termine der Reihe nach")
    eintraege = [(a, f"{tg(a)} – {tg(b)}", name, wer) for name, wer, a, b in PHASEN]
    eintraege += [(t, tg(t), "◆ " + name, wer) for name, t, wer in MEILENSTEINE]
    eintraege += [(p0, f"{tg(p0)} – {tg(p1)}", "Winterpause", "Pause") for p0, p1 in PAUSEN]
    eintraege.sort(key=lambda e: (e[0], not e[2].startswith("◆")))
    ax = fig.add_axes([0.04, 0.05, 0.92, 0.84])
    ax.axis("off")
    h = 1 / (len(eintraege) + 1)
    for x, t in ((0.0, "Zeitraum / Datum"), (0.33, "Aufgabe / Abgabe"), (0.78, "Wer"), (0.9, "erledigt")):
        ax.text(x, 1 - h / 2, t, fontsize=9, weight="bold", va="center")
    ax.axhline(1 - h, color="k", lw=0.8)
    for k, (_, wann, was, wer) in enumerate(eintraege):
        y = 1 - (k + 1.5) * h
        if k % 2 == 0:
            ax.axhspan(y - h / 2, y + h / 2, color="0.95", lw=0, zorder=0)
        ms = was.startswith("◆")
        ax.text(0.0, y, wann, fontsize=8.5, va="center", weight="bold" if ms else "normal")
        ax.text(0.33, y, was, fontsize=8.5, va="center", weight="bold" if ms else "normal")
        ax.add_patch(plt.Rectangle((0.758, y - h * 0.3), 0.012, h * 0.6, color=FARBE[wer], transform=ax.transAxes))
        ax.text(0.78, y, {"Pause": "–", "Anmeldung": "jeder selbst"}.get(wer, wer), fontsize=8.5, va="center")
        ax.add_patch(plt.Rectangle((0.915, y - h * 0.3), 0.012, h * 0.6, fill=False, ec="k", lw=0.6, transform=ax.transAxes))
        if was.lstrip("◆ ") in ERLEDIGT:
            ax.text(0.921, y, "✓", fontsize=10, ha="center", va="center", color="#2e7d32", weight="bold")
    ax.set_ylim(0, 1)
    pdf.savefig(fig)
    plt.close(fig)

print("✓ labor/Zeitplan.pdf, plots/zeitplan.pdf")