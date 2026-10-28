# Portfolio-Vorlage Projektpraktikum WS 2026/27 (Overleaf)

Basiert 1:1 auf den offiziellen Gerüsten `pp-portfolio-geruest-2026-2027.tex` und
`pp-portfolio-geruest-einlage-2026-2027.tex` (Dokumentklasse, 12 pt, Ränder, Titelseiten,
Kopf-/Fußzeilen, Kapitel- und Abschnittstitel, Leitfragen, Längenvorgaben).
Jeder Text wird **einmal** geschrieben und landet automatisch in der Zwischenabgabe **und** in der Endabgabe.

## Overleaf einrichten
1. Overleaf → *New Project* → *Upload Project* → ZIP hochladen.
2. Menü → *Main document* wählen, je nachdem was du gerade abgibst:

| Hauptdatei | Abgabe | Frist |
|---|---|---|
| `Kautzsch_Motivationsformular.tex` | Motivationsformular | 21.10.2026 |
| `Kautzsch_Arbeitsplan.tex` | Einlage 1 | 28.10.2026 |
| `Kautzsch_Wiss_Arbeit.tex` | Einlage 2 | 11.11.2026 |
| `Kautzsch_Protokoll.tex` | Einlage 3 | 09.12.2026 |
| `Kautzsch_Messergebnis.tex` | Einlage 4 | 20.01.2027 |
| `Kautzsch_Vortrag.tex` | Einlage 5 | 07.02.2027 (vorgeschlagen) |
| `Kautzsch_Aussage_anderer_Vortrag.tex` | Einlage 6 | 21.02.2027 (vorgeschlagen) |
| `Kautzsch_Portfolio_Endabgabe.tex` | alles | **15.03.2027** |

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
3. PDF herunterladen und als `Kautzsch_WelcheEinlage.pdf` in Moodle hochladen.
4. Danach wieder `\Abgabefalse` zum Weiterschreiben.
