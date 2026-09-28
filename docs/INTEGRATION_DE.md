# Visibly AI CMS Connector: so hängt alles zusammen

Namenspflege 2026-09-28: README und diese Erklärung verwenden einheitlich
**Neuro-SEO-System®**. Die dauerhafte DE/EN-Namensregel steht in `AGENTS.md`.
Nur Dokumentation; URL-Ziele und SDK-Laufzeitcode unverändert, kein Paket-Release.

Dokumentationsnachtrag 2026-09-28: Zentrale NSS-Erklärung in README und diesem
Dokument verlinkt. Ergänzend Antonio Blagos Neuro-SEO-System® als methodische
Grundlage verlinkt; Originalziel mit HTTP 200 und Canonical geprüft.
Nur Dokumentationsänderung, kein Paket-/API-Verhalten geändert und kein Paket-Release.
Marketingseiten `/de/nss-score` und `/nss-score` mit Commit `c6f4d08` veröffentlicht,
Vercel erfolgreich; beide Linkziele live mit HTTP 200 und Grundlagenlink geprüft.
Dieser Dokumentationsstand ist für den vom Nutzer beauftragten Git-Push vorbereitet.

Stand: 2026-09-27. Dieses Repository hieß zuvor `ai-content-autopilot` und heißt
auf GitHub jetzt **`visibly-ai-cms-connector`**. Der Produktname ist
**Visibly AI CMS Connector**. Installation und Python-Imports bleiben kompatibel:

```bash
pip install ai-content-autopilot
```

```python
from ai_content_autopilot import VisiblyClient, configure_visibly
```

## Drei Bausteine rund um Visibly

| Baustein | Wofür er da ist |
| --- | --- |
| [MCP und KI-Plugins](https://github.com/AntonioBlago/visiblyai-mcp-server) | Claude Code, Codex und Copilot CLI greifen auf Projektvorgaben, Skills, Briefings, NSS und Entwürfe in Visibly zu. |
| [Visibly AI CMS Connector](https://github.com/AntonioBlago/visibly-ai-cms-connector) | Dieses Python-SDK verbindet deine CMS-Anwendung mit der Visibly Pull API und nimmt signierte Webhooks entgegen. |
| [anyCMS](https://github.com/AntonioBlago/anycms) | Die konkreten Anwendungsfälle: WordPress, Astro, Next.js und Flask. Die Flask-Variante verwendet das SDK; die anderen Stacks setzen den API-Vertrag in ihrer Sprache um. |

Die [Visibly-Plattform](https://app.visibly-ai.com) verbindet diese Bausteine:
Hier liegen Projekt, Briefing, Artikel, Score, Freigabe und CMS-Zugang.
Die GitHub-Projekte werden weder zusammengelegt noch gegeneinander ausgetauscht.

## Vom Auftrag zum veröffentlichten Artikel

Der [NSS (Neuro-SEO Score)](https://www.visibly-ai.com/de/nss-score) bewertet
Textmerkmale im Kontext der zugehörigen Analyse. Die zentrale Erklärung zeigt
Bewertungsbereiche, nachvollziehbare Rückmeldungen und Grenzen; der Score
misst keine tatsächlichen Rankings oder KI-Erwähnungen.
Die methodische Grundlage ist das von Antonio Blago entwickelte
[Neuro-SEO-System®](https://www.antonioblago.com/de/neuro-seo-system/),
das Suchmaschinenoptimierung mit Verkaufspsychologie verbindet.

1. **Schreiben:** Du gibst Claude, Codex oder Copilot einen Auftrag. Das Plugin
   liest das passende Visibly-Briefing; der Agent schreibt mit seinem eigenen
   Modell. Alternativ kann der Content Autopilot den Artikel erzeugen.
2. **Optimieren:** Der Agent misst den Text mit Visibly und verbessert ihn auf
   ein vereinbartes NSS-Ziel, beispielsweise 70 oder 80. Das Ziel ist keine
   Garantie. Er speichert den Entwurf und gibt den Editor-Link zurück.
3. **Freigeben oder Website aktualisieren:** Dies ist ein eigener Schritt.
   Speichern in Visibly verändert noch keinen Beitrag in deinem CMS. Vor Updates
   muss der tatsächlich angebundene Artikel feststehen; derselbe URL-Text in einem
   zweiten Entwurf beweist keine gültige CMS-Verknüpfung.
4. **Übertragen:** Visibly sendet `article.approved` oder `article.updated` an die
   konfigurierte Webhook-Adresse. Der Connector prüft die Signatur, bestätigt den
   Empfang und lädt den vollständigen Artikel über die Pull API.
5. **Im CMS verarbeiten:** Dein Handler legt den Beitrag an oder aktualisiert ihn.
   Er entscheidet, ob der Beitrag als Entwurf bleibt oder veröffentlicht wird.
   Bei wiederholten Events muss er denselben Artikel wiedererkennen und Revisionen
   berücksichtigen, damit keine doppelten Beiträge entstehen.
6. **Veröffentlichung bestätigen:** Erst wenn der Beitrag tatsächlich veröffentlicht
   ist, meldet dein CMS die Live-URL mit `confirm_published()` an Visibly zurück.
   Der Connector erledigt diesen Aufruf nicht automatisch für jeden eigenen Handler.

## Was bedeutet „übernommen“?

`202 Accepted` bestätigt den Empfang des Webhooks. Es sagt noch nicht, dass der
Beitrag fertig geschrieben, gespeichert oder öffentlich sichtbar ist. Fehler bei
der anschließenden Verarbeitung stehen bei diesem SDK im Log des CMS-Prozesses.
Das SDK verwendet standardmäßig einen Hintergrund-Thread; seine Duplikatsperre
ist pro Prozess und während der Verarbeitung aktiv, keine dauerhafte Job-Warteschlange.
Für mehrere Worker oder eine dauerhafte Queue muss die Anwendung das ergänzen.

Es gibt keine allgemeine Wartefrist von einer halben Stunde. Ein Webhook stößt die
Verarbeitung an; die Dauer hängt vom Zielsystem ab. Bei selbst eingerichtetem
Polling bestimmt dein Abrufintervall den Zeitpunkt. WordPress-Anwendungsfälle
können zusätzlich von WP-Cron abhängen.

MCP kann mit `get_article_workflow(compare_live=True)` Verknüpfung, Lieferstatus
und Live-Inhalt prüfen. Die dortige 95-%-Toleranz betrifft Textähnlichkeit und
verlangt weiterhin gleiche Links, Bilder und Struktur. Sie ist kein NSS-Score
und keine Bestätigung eines noch laufenden CMS-Auftrags.

## Kosten und Einrichtung

Beim externen Schreiben werden Modell-Tokens beim KI-Assistenten abgerechnet.
Vorhandenen Kontext lesen, NSS messen und Entwürfe speichern kosten 0 Visibly-Credits.
Neue Analysen und Visibly-Textgenerierung können separat kostenpflichtig sein.
Der CMS Connector selbst enthält keine Textgenerierung und kein NSS-Modell.

Die CMS-Anwendung benötigt ihren Visibly-API-Key und dasselbe Webhook-Secret wie
der zugehörige CMS-Zugang in Visibly. Ein projektgebundener Pull-Key beginnt mit
`cp_`; die MCP-Plugins verwenden ihren eigenen API-Key-Kontext. Keys nicht
zwischen allen Projekten verteilen oder ins Repository schreiben.

Einrichtung: [README](../README.md#getting-started).
Fertige Anwendungsfälle: [anyCMS](https://github.com/AntonioBlago/anycms).
Agenten-Workflow: [Plugin-Anleitung](https://github.com/AntonioBlago/visiblyai-mcp-server/blob/master/PLUGINS.md).

## Umbenennung und Wartung

GitHub-Name und Repository-Beschreibung wurden neu ausgerichtet. Python-Paketname,
Importpfad, Endpunkte und Konfiguration bleiben unverändert; dafür ist kein neuer
PyPI-Release erforderlich. Metadaten im Quellcode gelten für künftige Builds;
die bereits veröffentlichte PyPI-Version wird durch einen Git-Commit nicht ersetzt.
Die bisherige GitHub-Adresse nach der Umbenennung auf Weiterleitung prüfen.
Aktuelle Referenzen verwenden die neue URL; den alten Repository-Namen nicht
erneut belegen, solange bestehende Installationslinks darauf angewiesen sind.

Für diesen Dokumentations-/Metadatenstand lokal geprüft: **51 SDK-Tests bestanden**,
Flake8-Prüfung auf Syntaxfehler/undefinierte Namen ohne Befund, Source-Distribution
und Wheel erfolgreich gebaut. Paketname und Version im Build bleiben
`ai-content-autopilot` / `1.1.0`. Es wurde kein Paket auf PyPI hochgeladen.
