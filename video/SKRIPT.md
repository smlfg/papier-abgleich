# Voiceover-Skript (Deutsch, du-Form)

Sprechtempo etwa 130 Wörter pro Minute. Gesprochen sind rund 925 Wörter (≈ 7 min); die übrigen ≈ 3 min sind bewusst Bild-Pausen (Skizze, Seiten-Recording, Zahlen-Einblendungen). Szenennummern wie in `DREHBUCH.md`. Belege: `RECHERCHE.md`. In eckigen Klammern: Regieanweisungen, nicht sprechen.

---

**1 · Kalter Einstieg (25 s)**
Ich hatte einen Tag lang mit Coding-Agenten gearbeitet. Fünfundsiebzig Commits. Die Tests liefen. Und dann saß ich davor und konnte dir nicht sagen, was eigentlich passiert, wenn ich auf meinem Tablet eine Rechnung hinschreibe.

**2 · Titel (15 s)**
Das hier ist die Geschichte, wie ich mein eigenes Projekt zurückgeholt habe. Mit einem Stift.

**3 · Kontext (45 s)**
Das Projekt heißt inkpartner. Die Idee: Du schreibst auf dem reMarkable, einem E-Ink-Tablet, eine Matheaufgabe. Ein Agent liest mit und antwortet direkt auf dem Papier. Hier siehst du so eine Seite: Ich habe nach dem Pascal-Dreieck gefragt, und die farbige Schrift ist die Antwort vom Agenten. Hier schreibt er eine Rechenregel dazu. Klingt einfach. Ist es nicht. Lesen, verstehen, urteilen, zeichnen, auf das Gerät schreiben: jede dieser Stufen kann kaputtgehen.

**4 · Vorgeschichte (45 s)**
Davor lag schon eine Woche mit einer früheren Version. Ich habe sie danach von einem Agenten auswerten lassen, als Friedhof: fünfundzwanzig Versuche, dreiundsechzig dokumentierte Fehler, vierunddreißig Sackgassen. Die Definition of Done stand bei der Messung am einundzwanzigsten Oktober bei null von vierzehn. Ehrlicher geht es nicht. Und trotzdem habe ich weitergebaut.

**5 · Ein Tag Code (50 s)**
Am vierundzwanzigsten Oktober ging es kurz nach Mitternacht los, erst mit Codex und Claude Code. Regeln, Prompts, Messrunden in der Nacht. Am Nachmittag Live-Tests am Gerät: Wo ist die Seite, wie schnell schreibt der Stift, wie kalibriert sich der Agent selbst. Am Ende des Tages stehen fünfundsiebzig Commits im Repo. Jeder einzelne hat eine gute Nachricht. Zusammen ergeben sie ein System, das ich nicht mehr im Kopf hatte.

**6 · Bruch (15 s)**
Gegen acht Uhr abends kam der Punkt, an dem nichts mehr ging. Ein echter Frust-Moment. Mehr muss man dazu nicht sagen.

**7 · Die Cursor-Nacht (80 s)**
Danach habe ich auf Cursor gewechselt und mehrere Agenten-Sessions parallel aufgemacht. Sechs davon waren richtige Arbeits-Sessions, dazu kamen zwei kurze für Werkzeuge. Eine kümmerte sich um den Stift, eine um die Lese-Pipeline, eine um das Schreiben aufs Gerät.
Mein Testsatz war immer derselbe: drei plus drei gleich sieben, auf einer neuen Seite. Und die Antwort lautete oft: „Seit drei Minuten keine Reaktion.“
Dann kamen die Funde. Einer davon: Ein Stift-Event ist genau vierundzwanzig Byte groß. Das Programm, das sie aufs Tablet schickte, las in Blöcken von viertausendsechsundneunzig Byte. Wenn so eine Grenze mitten in ein Event fiel, blieb der Strich offen. Ein anderer: Der Aufruf ans lokale Modell durfte bis zu sechshundert Sekunden blockieren, und solange schaute niemand mehr auf die Seite.
Gute Funde. Aber jeder Fund machte das Bild in meinem Kopf noch ein Stück unschärfer.

**8 · Wendepunkt (50 s)**
Also habe ich etwas anderes gemacht. Ich habe kein weiteres Agenten-Summary gelesen. Ich habe das Tablet genommen und aus dem Kopf aufgezeichnet, wie ich glaube, dass das System funktioniert. Ohne in den Code zu schauen. Bild geht ans Sprachmodell. Der Agent klassifiziert das Fach. Pro Runde maximal vier Zeichen. Dort fängt validate an. Ich nenne das die Grillme-Skizze, weil ich mich damit selbst ausgefragt habe. Achtzehn Punkte, kreuz und quer, mit Pfeilen und einer Raute für ja oder nein.

**9 · Abgleich (60 s)**
Und dann habe ich den Spieß umgedreht. Normalerweise erklärt der Agent dir deinen Code. Hier hält der Agent den Code gegen meine Zeichnung. Für jeden Punkt der Skizze: Stimmt das noch? Hat sich das geändert? Funktioniert es anders? Jede Antwort mit einem Beleg und mit der echten Code-Stelle aus einem festen Commit. Nichts aus dem Gedächtnis, nichts geraten. Wo der Code keine Antwort hergibt, steht ehrlich: unklar.

**10 · Die Seite (80 s)**
Das Ergebnis ist eine Seite, die aussieht wie meine Skizze. Oben das Urteil: Von vierundzwanzig Knoten stimmen elf noch. Fünf wurden geändert, vier stimmen teilweise, zwei funktionieren anders, zwei sind unklar. Dazu neun offene Fragen.
Ich kann nach Status filtern. Hier, alles was sich geändert hat. Ich klicke auf „dort fängt validate an“ und sehe: Was der Schritt heute tut, warum er als geändert gilt, den Code dazu mit Zeilennummern und einen Link auf den Commit. Und im Verlauf: welche Session das angefasst hat. Das funktioniert auch auf dem Handy. Zum ersten Mal an diesem Tag hatte ich wieder eine Karte von meinem eigenen Projekt.

**11 · Werkzeug (45 s)**
Daraus habe ich ein kleines Werkzeug gemacht. Du beschreibst deine Skizze in einer Datei namens flow.json, ein Python-Skript baut daraus die Seite, als eine einzige HTML-Datei zum Verschicken. Jeder Fakt kann ein Zitat tragen und einen Marker: belegt im Code, auf dem Gerät beobachtet, nur offline getestet, oder Hypothese. So siehst du sofort, wie fest der Boden unter einer Aussage ist.

**12 · Versionen (30 s)**
Die Seite selbst hat drei Anläufe gebraucht. Version eins war meine Skizze als Hintergrundbild mit Markierungen. Version zwei ein echtes Flussdiagramm. Version drei sortiert alles in Stufen und gibt jedem Knoten ein Panel mit Fakt, Code und Verlauf.

**13 · Einsicht (40 s)**
Und jetzt der ehrliche Teil. Die eigentliche Aufgabe, mit dem Tablet lernen, ist immer noch nicht gelöst. Aber ich glaube, das war gar nicht die eigentliche Arbeit. Die eigentliche Arbeit war herauszufinden, wie ein Mensch mit mehreren Agenten zusammenarbeiten kann, ohne die Kontrolle über sein eigenes Projekt zu verlieren. Das ist angewandte Human-Agent-Interaction.

**14 · Abschluss (20 s)**
Meine Antwort darauf ist erstaunlich altmodisch: Papier. Zeichne, was du glaubst. Lass den Agenten dagegenhalten. Der Ablauf und das Werkzeug sind im Repo papier-abgleich. Link in der Beschreibung.
