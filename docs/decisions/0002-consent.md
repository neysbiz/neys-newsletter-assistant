# ADR 0002 – Zustimmung und DOI

06.10.2026. `contacts` besitzt Kontaktidentität/Sperren, `consents` Newsletterzustand/Nachweise/DOI. Application-Services besitzen Transaktionen und Statuswechsel. Tracking ist ausschließlich `False`; keine Tracking-Endpunkte oder personalisierten Bildlinks.

E-Mail-Identität ist explizit case-insensitive; Eingabe wird erhalten, Vergleich über casefold. Plus-Tags/Punkte werden nicht verändert. Rate-Limit: maximal 3 Anforderungen/Adresse und 20/IP pro UTC-Stunde, 10 Minuten Cooldown. Buckets speichern zweckgebundene HMACs, keine Klartext-IP; Bereinigung per `prune_rate_limits`. Hinter Reverse-Proxy ist die konfigurierte Vertrauensgrenze vor Go-live festzulegen; ungeprüfte Forwarded-Header werden ignoriert.

DOI-Referenzen: Zufalls-UUID + zweckgebundene HMAC-Signatur, kein vollständiges Bearer-Token im DB-Record. Ablauf in DB 24 Stunden, GET ohne Mutation, bestätigender POST mit CSRF. Nachweise enthalten den angeforderten Text/Version; spätere Texte ersetzen bestehende Nachweise nicht. Wiederholungs-POST ist idempotent, nach Widerruf wird ein alter Link nicht erneut aktiv.

DOI-Aufträge werden in derselben DB-Transaktion angelegt. Beat/Managementcommand verarbeitet sie nach Commit. Unklarer SMTP-Ausgang/abgebrochener Claim wird sichtbar als `uncertain`; keine blinde Wiederholung. Ein erneutes Anfordern nach Cooldown erstellt einen neuen DOI-Auftrag.

Abmeldelinks sind separat signiert und benötigen keinen Login. GET zeigt Bestätigung, Browser-POST hat CSRF. Separater RFC-8058-Endpunkt verarbeitet ausschließlich `List-Unsubscribe=One-Click`; dafür ist CSRF gezielt deaktiviert. Header erzeugt erst M3/M4. HTTPS und gültige DKIM-Signatur einschließlich dieser Header werden vor realem Versand geprüft: https://www.rfc-editor.org/rfc/rfc8058.html . Nicht als produktiv bestätigte RFC-Konformität behaupten.

Der aktuelle Zustimmungswortlaut ist eine Entwicklungskennzeichnung. Vor Go-live sind Version/Text und Datenschutzhinweis/Betreiberangaben konkret festzulegen. Kein echtes Abonnentenimportieren, kein Kundenversand.
