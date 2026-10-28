# Portfolio Kristijan Manevski – Projektpraktikum WS 2026/27 (Overleaf)

Projekt **Dynamik Keltischer Wackelsteine** (mit Janosch), Schwerpunkt
**Bewegungsgleichungen und numerische Simulation der Spin-Umkehr**.
Kopie von Moritz' Beispielportfolio, angepasst mit allen Angaben aus dem Projektordner.

Basiert 1:1 auf den offiziellen Gerüsten `pp-portfolio-geruest-2026-2027.tex` und
`pp-portfolio-geruest-einlage-2026-2027.tex` (Dokumentklasse, 12 pt, Ränder, Titelseiten,
Kopf-/Fußzeilen, Kapitel- und Abschnittstitel, Leitfragen, Längenvorgaben).
Jeder Text wird **einmal** geschrieben und landet automatisch in der Zwischenabgabe **und** in der Endabgabe.

## Was schon eingetragen ist
- `einstellungen.tex`: Name, Projekt, Schwerpunkt, Partner Janosch + dessen Schwerpunkt, Paper-Key,
  Vortragsdatum, Praktikumstermine (Kommentar). Jede Zwischenabgabe setzt ihr eigenes Abgabedatum.
- Einlage 1: echter Arbeitsplan (`anhaenge/arbeitsplan.pdf` = Export von `Arbeitsplan_Wackelstein.xlsx`)
  im Anhang; Stichpunkte für die Beschreibung; Hinweise auf Abhängigkeiten und logische Fehler im Plan
  für die Reflexion. Alternative als LaTeX-Gantt mit den Excel-Daten (`\iffalse`-Block).
- Einlage 2: Paper Kondo & Nakanishi, Phys. Rev. E 95, 062207 (2017) als Anhang
  (`anhaenge/paper_kondo_nakanishi_2017.pdf`) + Stichpunkte zur Physik.
- Einlagen 3–6, Einleitung, Gesamtreflexion: Stichpunkte und Gerüste mit Projektbezug
  (Inertialsensor, Glasplatte, Messreihen 1–3, Umkehrzeit, Wachstumsrate, Kandidaten für Einlage 6).
- `literatur.bib`: Kondo & Nakanishi 2017, Garcia & Hubbard 1988, Themenliste, eigener Arbeitsplan,
  Peer-Input von Petros, Laborjournal.

## Was noch fehlt (rot im PDF)
- Matrikelnummer, Studiengang, Uni-E-Mail, Janoschs Nachname (`einstellungen.tex`).
- Schwerpunkt und Paper-Zuordnung sind aus der Aufgabenverteilung im Arbeitsplan **abgeleitet** – prüfen
  und mit Janosch abgleichen (Janosch darf nicht dasselbe Paper nehmen; Alternative `GarciaHubbard1988`).
- Antworten des Motivationsformulars (Abgabe vom 21.10.2026) – liegen nicht im Projektordner.
- Alle Fließtexte (Beschreibungen, Diskussionen, Reflexionen) selbst formulieren: Die roten Platzhalter
  enthalten nur Stichpunkte. KI-formulierte Texte müssten laut Zitierregeln gekennzeichnet und zitiert werden.
- Laborbuch-Link, Protokolldatum, Messdaten, Folien, fremder Vortrag (später im Semester).

## Overleaf einrichten
1. Overleaf → *New Project* → *Upload Project* → ZIP hochladen.
2. Menü → *Main document* wählen, je nachdem was du gerade abgibst:

| Hauptdatei | Abgabe | Frist |
|---|---|---|
| `Manevski_Motivationsformular.tex` | Motivationsformular | 21.10.2026 |
| `Manevski_Arbeitsplan.tex` | Einlage 1 | 28.10.2026 |
| `Manevski_Wiss_Arbeit.tex` | Einlage 2 | 11.11.2026 |
| `Manevski_Protokoll.tex` | Einlage 3 | 09.12.2026 |
| `Manevski_Messergebnis.tex` | Einlage 4 | 20.01.2027 |
| `Manevski_Vortrag.tex` | Einlage 5 | 07.02.2027 (vorgeschlagen) |
| `Manevski_Aussage_anderer_Vortrag.tex` | Einlage 6 | 21.02.2027 (vorgeschlagen) |
| `Manevski_Portfolio_Endabgabe.tex` | alles | **15.03.2027** |

Compiler: pdfLaTeX (Standard), Literatur über biber (erkennt Overleaf automatisch).

## Wo trage ich was ein?
- `einstellungen.tex` – Name, Matrikelnr., Studiengang, Projekt, Schwerpunkt, Partner/in, Laborbuch-Link,
  bib-Keys, **Modus-Schalter**.
- `kapitel/` – Einleitung, Gesamtreflexion, Motivationsformular-Antworten.
- `einlagen/N_*.tex` – Beschreibung / Diskussion der Physik / Reflexion der Einlage N.
- `einlagen/N_*_anhang.tex` – die Einlage selbst (PDF einbinden mit `\anhangpdf`).
- `anhaenge/` – PDFs (Paper, Laborjournal-Export, Folien, Messdaten).
- `abbildungen/` – Grafiken für `\includegraphics`.
- `literatur.bib` – alle Quellen; `VORLAGE-...`-Einträge sind Muster (Artikel, Buch, Webseite, Datenblatt,
  Gespräch/Peer-Feedback, fremder Vortrag, Laborjournal, **KI-Nutzung**).

## Hilfsmittel der Vorlage
- `\platzhalter{...}` – roter Platzhalter; bleibt auch im Abgabemodus rot sichtbar + Warnung.
  Ersetze ihn durch deinen Text.
- `\begin{hinweise}...\end{hinweise}` – grüne offizielle Hilfen/Leitfragen; verschwinden im Abgabemodus.
- `\begin{umfang}{Name}{min}{max}...\end{umfang}` – misst die Länge des Textes in Seiten und zeigt sie im
  Entwurf an (grün = im Soll, rot = außerhalb). Abbildungen/Tabellen werden mitgemessen, zählen laut
  Regeln aber nicht – dann abziehen. Für realistische Werte `\Hinweisefalse` setzen.
- Kontrollseite (nur Entwurf): Längentabelle, offene Platzhalter, Fristen, Checkliste aller Formregeln.
- `\anhangpdf[pages={1-4}]{Titel}{label}{anhaenge/datei.pdf}` – PDF als Anhang mit durchgehenden
  Seitenzahlen (Pflicht laut Bewertungskriterien).

## Vor jeder Abgabe
1. `\Abgabetrue` in `einstellungen.tex` → alles Grüne wird schwarz bzw. entfernt (wie offizielle Zeile 15/16).
2. Kontrollieren: 0 rote Platzhalter, Deckblatt vollständig, Längen im Soll.
3. PDF herunterladen und als `Manevski_WelcheEinlage.pdf` in Moodle hochladen.
4. Danach wieder `\Abgabefalse` zum Weiterschreiben.
