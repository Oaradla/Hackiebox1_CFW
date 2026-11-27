"""Flow diagrams of the CFW manual as SVG, one file per diagram and language:
python3 diagrams.py OUTDIR  ->  OUTDIR/{en,de}/<name>.svg"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape

C = {  # fill, stroke
    "box": ("#e8f0fe", "#3b6fd8"),
    "srv": ("#e6f6ee", "#2f9a5f"),
    "ui": ("#fff4e0", "#d08a14"),
    "sd": ("#f1ecfb", "#7b55c7"),
    "bad": ("#fde9e9", "#c94040"),
    "ok": ("#e6f6ee", "#2f9a5f"),
    "plain": ("#f4f5f7", "#7a8290"),
}
FONT = "font-family='Segoe UI, Helvetica, Arial, sans-serif'"


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.parts = w, h, []
        self.parts.append(f"<rect width='{w}' height='{h}' rx='12' fill='#ffffff'/>")
        self.parts.append(f"<text x='24' y='38' {FONT} font-size='20' font-weight='600' fill='#1f2430'>{escape(title)}</text>")

    def node(self, x, y, w, h, lines, kind="plain", bold_first=True):
        fill, stroke = C[kind]
        self.parts.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{fill}' stroke='{stroke}' stroke-width='2'/>")
        lines = lines if isinstance(lines, list) else [lines]
        top = y + h / 2 - (len(lines) - 1) * 9 + 5
        for i, line in enumerate(lines):
            weight = "600" if i == 0 and bold_first else "400"
            size = 15 if i == 0 else 13
            self.parts.append(f"<text x='{x + w / 2}' y='{top + i * 18}' text-anchor='middle' {FONT} font-size='{size}' font-weight='{weight}' fill='#1f2430'>{escape(line)}</text>")

    def arrow(self, pts, label=None, lx=None, ly=None, color="#4a5060", dashed=False, anchor="middle"):
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        dash = " stroke-dasharray='6 5'" if dashed else ""
        self.parts.append(f"<path d='{d}' fill='none' stroke='{color}' stroke-width='2'{dash} marker-end='url(#a{color[1:]})'/>")
        self.markers = getattr(self, "markers", set()) | {color}
        if label:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            lx = lx if lx is not None else (x1 + x2) / 2
            ly = ly if ly is not None else (y1 + y2) / 2 - 8
            for i, line in enumerate(label if isinstance(label, list) else [label]):
                self.parts.append(f"<text x='{lx}' y='{ly + i * 16}' text-anchor='{anchor}' {FONT} font-size='13' fill='#3a4050'>{escape(line)}</text>")

    def text(self, x, y, s, size=13, anchor="start", color="#3a4050", weight="400"):
        self.parts.append(f"<text x='{x}' y='{y}' text-anchor='{anchor}' {FONT} font-size='{size}' font-weight='{weight}' fill='{color}'>{escape(s)}</text>")

    def raw(self, s):
        self.parts.append(s)

    def save(self, path):
        defs = "".join(
            f"<marker id='a{c[1:]}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='8' markerHeight='8' orient='auto-start-reverse'>"
            f"<path d='M0,0 L10,5 L0,10 z' fill='{c}'/></marker>" for c in sorted(getattr(self, "markers", set())))
        body = "\n".join(self.parts)
        path.write_text(f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.w}' height='{self.h}' viewBox='0 0 {self.w} {self.h}'>"
                        f"<defs>{defs}</defs>\n{body}\n</svg>\n", encoding="utf-8")


T = {
    "overview": {
        "en": ["How the parts work together", "Toniebox", "custom firmware", "settings on the SD card", "teddyCloud", "with CFW support",
               "settings, update library", "Web browser", "teddyCloud web UI", "settings, remote control,", "box update",
               "freshness check: settings files", "log connection: status, battery,", "commands of the remote control", "update check: firmware image", "you change it here"],
        "de": ["So greifen die Teile ineinander", "Toniebox", "Custom-Firmware", "Einstellungen auf der SD-Karte", "teddyCloud", "mit CFW-Unterstützung",
               "Einstellungen, Update-Bibliothek", "Webbrowser", "teddyCloud-Oberfläche", "Einstellungen, Fernbedienung,", "Box Update",
               "Freshness-Check: Einstellungsdateien", "Log-Verbindung: Zustand, Akku,", "Befehle der Fernbedienung", "Update-Prüfung: Firmware-Image", "hier stellst du ein"],
    },
    "boot": {
        "en": ["How a CC3200 box starts", "Preloader", "in the flash (/sys/mcuimg.bin)", "SD bootloader", "HackieboxNG with trial start", "reads ngCfg.json + ngstate.bin",
               "slot cfw1 / cfw2", "Custom firmware", "/revvox/boot/ng-cfw1.bin or -cfw2.bin", "slot ofw1 (no stateFile)", "Original firmware", "stays unchanged in the flash",
               "new build: one trial start", "trial start fails:", "back to the previous build", "the box reports the result in its hello"],
        "de": ["So startet eine CC3200-Box", "Preloader", "im Flash (/sys/mcuimg.bin)", "SD-Bootloader", "HackieboxNG mit Probestart", "liest ngCfg.json + ngstate.bin",
               "Slot cfw1 / cfw2", "Custom-Firmware", "/revvox/boot/ng-cfw1.bin oder -cfw2.bin", "Slot ofw1 (ohne stateFile)", "Original-Firmware", "bleibt unverändert im Flash",
               "neuer Build: ein Probestart", "Probestart scheitert:", "zurück zum vorigen Build", "die Box meldet das Ergebnis im Hello"],
    },
    "update": {
        "en": ["Firmware update through teddyCloud", "1  Image into the library", "upload or GitHub download", "channel release / beta / alpha",
               "2  Which box gets what", "manual: assigned image", "automatic: newest of its channel", "3  The box asks", "at its start, or at once", "with \"Now\" (remote control)",
               "4  Download", "into the free slot", "5  Trial start", "of the new build", "starts and reports", "Confirmed", "the build stays", "does not come up", "Rolled back",
               "previous build runs again;", "not offered again"],
        "de": ["Firmware-Update über teddyCloud", "1  Image in die Bibliothek", "Upload oder GitHub-Download", "Kanal Release / Beta / Alpha",
               "2  Welche Box was bekommt", "Manuell: zugewiesenes Image", "Automatisch: neuestes des Kanals", "3  Die Box fragt", "beim Start oder sofort", "mit „Jetzt“ (Fernbedienung)",
               "4  Download", "in den freien Slot", "5  Probestart", "des neuen Builds", "startet und meldet sich", "Bestätigt", "der Build bleibt", "kommt nicht hoch", "Zurückgerollt",
               "voriger Build läuft wieder;", "wird nicht erneut angeboten"],
    },
    "event": {
        "en": ["What an event tag does", "Place the event tag", "plays nothing", "LED blinks turquoise once", "Applies to: next figure",
               "within 60 s", "Place a figure", "it takes the actions", "and keeps them", "Applies to: whole box", "at once", "Box settings change",
               "locks, switch-off, times;", "optionally only until switch-off", "Confirmation", "5 blinks per action, tones:", "turquoise + rising = on",
               "lilac + falling = off", "\"Set with the ears\": while the tag lies on the box, the ears set the volume limit or the LED; the value counts when the tag is taken off."],
        "de": ["Was ein Event-Tag macht", "Event-Tag auflegen", "spielt nichts ab", "LED blinkt einmal türkis", "Gilt für: nächste Figur",
               "innerhalb 60 s", "Figur auflegen", "sie übernimmt die Aktionen", "und behält sie", "Gilt für: ganze Box", "sofort", "Box-Einstellungen ändern sich",
               "Sperren, Ausschalten, Zeiten;", "wahlweise nur bis zum Ausschalten", "Bestätigung", "5× Blinken je Aktion, Töne:", "türkis + steigend = ein",
               "lila + fallend = aus", "„Mit den Ohren einstellen“: Solange der Tag aufliegt, stellen die Ohren Lautstärke-Limit oder LED ein; der Wert gilt beim Abnehmen."],
    },
    "resume": {
        "en": ["Global resume: one tonie, several boxes", "Box A", "the tonie plays", "until 12:40", "teddyCloud", "keeps the position", "per tonie",
               "position", "Box B", "the tonie is placed", "asks for the position", "continues at 12:40", "both boxes played offline:", "two positions",
               "choose one in the", "tonie's edit dialog", "until then each box", "keeps its own"],
        "de": ["Globales Fortsetzen: ein Tonie, mehrere Boxen", "Box A", "der Tonie spielt", "bis 12:40", "teddyCloud", "merkt sich die Position", "pro Tonie",
               "Position", "Box B", "der Tonie wird aufgelegt", "fragt nach der Position", "spielt ab 12:40 weiter", "beide Boxen spielten offline:", "zwei Positionen",
               "im Bearbeiten-Dialog", "des Tonies eine wählen", "bis dahin behält jede", "Box ihre eigene"],
    },
    "settings": {
        "en": ["Where a setting goes", "Web UI", "box, tonie or", "event tag settings", "teddyCloud", "stores them,", "builds settings files",
               "Box", "gets them at its", "freshness check", "SD card", "works offline", "changed on the box", "(ears, event tag):", "reported back, the UI shows it",
               "A tonie's own setting wins over the box's, in both directions."],
        "de": ["Wohin eine Einstellung geht", "Weboberfläche", "Einstellungen von Box,", "Tonie oder Event-Tag", "teddyCloud", "speichert sie,", "baut Einstellungsdateien",
               "Box", "holt sie beim", "Freshness-Check", "SD-Karte", "wirkt auch offline", "an der Box geändert", "(Ohren, Event-Tag):", "zurückgemeldet, die Oberfläche zeigt es",
               "Die Einstellung eines Tonies gewinnt in beide Richtungen gegen die der Box."],
    },
    "gestures": {
        "en": ["Gestures only the custom firmware has", "Slap upside down", "ears down, slap the side:", "back to the very beginning,", "Both ears briefly",
               "press together, let go", "within 2 s: switch off", "Event tag + ears", "the ears set the limit", "or the LED level", "LED lilac once", "with shuffle: shuffled anew"],
        "de": ["Gesten, die nur die Custom-Firmware kennt", "Kopfüber klopfen", "Ohren nach unten, seitlich", "klopfen: ganz von vorn,", "Beide Ohren kurz",
               "zusammen drücken, innerhalb", "2 s loslassen: ausschalten", "Event-Tag + Ohren", "die Ohren stellen Limit", "oder LED-Stufe ein", "LED einmal lila", "mit Zufall: neu gemischt"],
    },
}


def overview(t):
    s = Svg(1100, 330, t[0])
    s.node(30, 90, 250, 150, [t[1], t[2], t[3]], "box")
    s.node(560, 90, 250, 150, [t[4], t[5], t[6]], "srv")
    s.node(880, 90, 200, 150, [t[7], t[8], t[9], t[10]], "ui")
    s.arrow([(560, 120), (280, 120)], t[11], ly=112)
    s.arrow([(280, 168), (560, 168)], [t[12], t[13]], ly=142)
    s.arrow([(560, 176), (280, 176)])
    s.arrow([(560, 220), (280, 220)], t[14], ly=212)
    s.arrow([(880, 150), (810, 150)])
    s.arrow([(810, 180), (880, 180)])
    s.text(845, 270, t[15], anchor="middle")
    return s


def boot(t):
    s = Svg(1000, 400, t[0])
    s.node(30, 150, 200, 80, [t[1], t[2]], "box")
    s.node(290, 140, 250, 100, [t[3], t[4], t[5]], "sd")
    s.node(680, 60, 300, 100, [t[7], t[8], t[12]], "ok")
    s.node(680, 250, 300, 80, [t[10], t[11]], "plain")
    s.arrow([(230, 190), (290, 190)])
    s.arrow([(540, 170), (610, 170), (610, 110), (680, 110)], t[6], lx=610, ly=50)
    s.arrow([(540, 210), (610, 210), (610, 290), (680, 290)], t[9], lx=610, ly=360)
    s.arrow([(700, 160), (700, 200), (548, 200)], color="#c94040", dashed=True)
    s.text(290, 275, t[13], color="#c94040", weight="600")
    s.text(290, 293, t[14], color="#c94040")
    s.text(290, 311, t[15], color="#c94040")
    return s


def update(t):
    s = Svg(1090, 480, t[0])
    xs = (30, 295, 560, 825)
    s.node(xs[0], 80, 240, 90, [t[1], t[2], t[3]], "srv")
    s.node(xs[1], 80, 240, 90, [t[4], t[5], t[6]], "srv")
    s.node(xs[2], 80, 240, 90, [t[7], t[8], t[9]], "box")
    s.node(xs[3], 80, 240, 90, [t[10], t[11]], "box")
    s.node(xs[3], 220, 240, 80, [t[12], t[13]], "sd")
    s.node(470, 370, 240, 80, [t[15], t[16]], "ok")
    s.node(825, 370, 240, 90, [t[18], t[19], t[20]], "bad")
    for a in range(3):
        s.arrow([(xs[a] + 240, 125), (xs[a + 1], 125)])
    s.arrow([(945, 170), (945, 220)])
    s.arrow([(860, 300), (860, 335), (590, 335), (590, 370)], t[14], lx=720, ly=327)
    s.arrow([(1030, 300), (1030, 370)], t[17], lx=1022, ly=340, anchor="end", color="#c94040")
    return s


def event(t):
    s = Svg(1160, 440, t[0])
    s.node(30, 150, 220, 90, [t[1], t[2], t[3]], "plain")
    s.node(310, 70, 190, 70, [t[4]], "ui", bold_first=False)
    s.node(620, 60, 270, 90, [t[6], t[7], t[8]], "box")
    s.node(310, 250, 190, 70, [t[9]], "ui", bold_first=False)
    s.node(620, 240, 270, 90, [t[11], t[12], t[13]], "box")
    s.node(930, 140, 210, 110, [t[14], t[15], t[16], t[17]], "ok")
    s.arrow([(250, 180), (280, 180), (280, 105), (310, 105)])
    s.arrow([(250, 210), (280, 210), (280, 285), (310, 285)])
    s.arrow([(500, 105), (620, 105)], t[5], ly=95)
    s.arrow([(500, 285), (620, 285)], t[10], ly=275)
    s.arrow([(890, 105), (1035, 105), (1035, 140)])
    s.arrow([(890, 285), (1035, 285), (1035, 250)])
    s.text(30, 400, t[18], size=13)
    return s


def resume(t):
    s = Svg(980, 400, t[0])
    s.node(30, 90, 220, 90, [t[1], t[2], t[3]], "box")
    s.node(380, 90, 220, 90, [t[4], t[5], t[6]], "srv")
    s.node(730, 90, 220, 90, [t[8], t[9], t[10], t[11]], "box")
    s.arrow([(250, 135), (380, 135)], t[7], ly=127)
    s.arrow([(730, 120), (600, 120)])
    s.arrow([(600, 150), (730, 150)], t[7], ly=170)
    s.node(330, 250, 320, 110, [t[12], t[13], t[14] + " " + t[15], t[16] + " " + t[17]], "bad")
    s.arrow([(490, 180), (490, 250)], dashed=True, color="#c94040")
    return s


def settings(t):
    s = Svg(980, 360, t[0])
    s.node(30, 90, 200, 90, [t[1], t[2], t[3]], "ui")
    s.node(290, 90, 200, 90, [t[4], t[5], t[6]], "srv")
    s.node(550, 90, 180, 90, [t[7], t[8], t[9]], "box")
    s.node(790, 90, 160, 90, [t[10], t[11]], "sd")
    s.arrow([(230, 135), (290, 135)])
    s.arrow([(490, 135), (550, 135)])
    s.arrow([(730, 135), (790, 135)])
    s.arrow([(640, 180), (640, 250), (390, 250), (390, 180)], dashed=True)
    s.text(515, 270, t[12] + " " + t[13], anchor="middle")
    s.text(515, 287, t[14], anchor="middle")
    s.text(30, 335, t[15], weight="600")
    return s


def box_icon(s, x, y, flip=False, ears_pressed=False):
    """a small box pictogram at x,y (top left, 120x110)"""
    g = f"<g transform='translate({x},{y}){' rotate(180 60 55)' if flip else ''}'>"
    ear = "#c94040" if ears_pressed else "#2f5fbf"
    g += (f"<rect x='10' y='30' width='100' height='80' rx='14' fill='#5b8def' stroke='#2f5fbf' stroke-width='3'/>"
          f"<path d='M16 34 Q12 4 32 8 Q44 12 40 32Z' fill='{ear}'/><path d='M104 34 Q108 4 88 8 Q76 12 80 32Z' fill='{ear}'/>"
          f"<circle cx='60' cy='52' r='5' fill='#b5f5c8'/></g>")
    s.raw(g)


def gestures(t):
    s = Svg(980, 330, t[0])
    box_icon(s, 70, 80, flip=True)
    s.raw("<path d='M215 120 l40 -14 M215 135 l44 0 M215 150 l40 14' stroke='#d08a14' stroke-width='4' stroke-linecap='round'/>")
    s.text(160, 240, t[1], size=15, anchor="middle", weight="600")
    s.text(160, 260, t[2], anchor="middle")
    s.text(160, 277, t[3], anchor="middle")
    s.text(160, 294, t[11], anchor="middle")
    box_icon(s, 430, 80, ears_pressed=True)
    s.raw("<path d='M450 70 l10 18 M570 70 l-10 18' stroke='#c94040' stroke-width='4' stroke-linecap='round'/>")
    s.raw("<circle cx='490' cy='132' r='9' fill='#b388eb'/>")
    s.text(490, 240, t[4], size=15, anchor="middle", weight="600")
    s.text(490, 260, t[5], anchor="middle")
    s.text(490, 277, t[6], anchor="middle")
    s.text(490, 294, t[10], anchor="middle", color="#7b55c7")
    box_icon(s, 760, 80)
    s.raw("<circle cx='820' cy='100' r='22' fill='#13a89e'/><path d='M824 86 812 104h8l-3 12 11-18h-8z' fill='#fff'/>")
    s.raw("<path d='M772 70 l8 16 M868 70 l-8 16' stroke='#d08a14' stroke-width='4' stroke-linecap='round'/>")
    s.text(820, 240, t[7], size=15, anchor="middle", weight="600")
    s.text(820, 260, t[8], anchor="middle")
    s.text(820, 277, t[9], anchor="middle")
    return s


out = Path(sys.argv[1])
for lang in ("en", "de"):
    (out / lang).mkdir(parents=True, exist_ok=True)
    for name, fn in (("overview", overview), ("boot", boot), ("update", update), ("event", event),
                     ("resume", resume), ("settings", settings), ("gestures", gestures)):
        fn(T[name][lang]).save(out / lang / f"flow-{name}.svg")
print("ok")
