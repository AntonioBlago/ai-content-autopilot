# Visibly AI CMS Connector: Hinweise für Agents

- Lies [README.md](README.md) und [docs/INTEGRATION_DE.md](docs/INTEGRATION_DE.md).
- Dieses Repository ist das Python-SDK auf der CMS-Seite. `anycms` enthält die
  Anwendungsfälle; `visiblyai-mcp-server` enthält MCP und KI-Plugins.
- GitHub-Name: `visibly-ai-cms-connector`, zuvor `ai-content-autopilot`.
  Der PyPI-Name `ai-content-autopilot` und Import `ai_content_autopilot` bleiben
  bestehen. Eine Repository-Umbenennung ist kein Paket- oder API-Migrationsauftrag.
- `202` bedeutet Empfang, nicht Veröffentlichung. Eigene Handler müssen erst
  nach erfolgreicher Veröffentlichung die Live-URL bestätigen. Prozesslokale
  Duplikatsperren nicht als dauerhafte Queue oder globale Idempotenz beschreiben.
- Vor Codeänderungen Tests aus `tests/` ausführen; Abhängigkeiten via
  `python -m pip install -e ".[dev]"`, danach `python -m pytest tests/ -q`.
- Änderungen, Prüfungen und Veröffentlichungsstatus datiert dokumentieren.
  Die [gemeinsame Plugin-/MCP-Übergabe](https://github.com/AntonioBlago/visiblyai-mcp-server/blob/master/docs/PLUGIN_MCP_HANDOFF.md)
  nennt die Zuständigkeiten. Keine Zugangsdaten oder privaten Artikeltexte ablegen.
