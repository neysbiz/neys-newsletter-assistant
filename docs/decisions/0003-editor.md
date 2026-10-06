# ADR 0003 – Editor und Rendering

06.10.2026. Serverseitiger Formset-Editor mit geordneten Text-/Bild-/Linkblöcken. Kein beliebiges HTML. Zentrale Servicevalidierung schützt auch Aufrufe außerhalb der UI. Nur HTTPS-Linkziele, keine Zugangsdaten/Steuerzeichen; HTML wird beim Rendern escaped. Personalisierung unterstützt ausschließlich `{{email}}`, unbekannte oder unvollständige Platzhalter werden abgewiesen.

Bilder: maximal 8 MB/20 MP, nur dekodierbare PNG/JPEG, anschließend neu kodiert mit zufälligem Dateinamen ohne Originalmetadaten. Öffentliche Medien enthalten keine personalisierten Referenzen. RevisionAsset schützt verwendete Bilder vor Löschen; keine Anwendungsschicht verändert vorhandene Bilddateien.

Freigabe erzeugt einen unveränderlichen Snapshot und startet keinen Kampagnenversand. Vorschau/Testmail verwenden dieselbe Revision/Renderfunktion, Abmeldeziel in Testmails ist explizit wirkungsloser Testlink. Produktive Empfängerlinks folgen im Versandpaket. Vor Versand sind Absender-/Betreiberangaben und produktive HTTPS-Medienauslieferung zu ergänzen.

Die neutrale Entwicklungsvorlage behauptet keine vollständig übernommene SimplyNeys-CI; deren aktuelle Originaldokumente müssen für den gestalterischen Abschluss separat gelesen werden. Praktische Prüfung in Outlook/Apple Mail/Gmail und mobile Ansichten offen. Kein Trackingpixel/Messredirect implementiert.
