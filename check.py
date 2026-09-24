"""ITU OBS kontenjan izleyici: degisince ntfy ile telefona bildirim atar."""
import html, os, re, sys, time, urllib.request

URL = ("https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch"
       "?programSeviyeTipiAnahtari=LU&dersBransKoduId=3")
WATCH = [w.strip() for w in os.environ.get("WATCH", "12364,12359,15687").split(",")]
TOPIC = os.environ["NTFY_TOPIC"]
STATE = "state.txt"
ROUNDS = int(os.environ.get("ROUNDS", "4"))
INTERVAL = int(os.environ.get("INTERVAL", "60"))


def get_kont():
    req = urllib.request.Request(URL, headers={"X-Requested-With": "XMLHttpRequest",
                                               "User-Agent": "Mozilla/5.0"})
    t = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
    found = {}
    for r in re.findall(r"<tr.*?</tr>", t, re.S):
        c = [html.unescape(re.sub("<[^>]+>", " ", x)).strip()
             for x in re.findall(r"<t[dh].*?</t[dh]>", r, re.S)]
        if len(c) > 10 and c[0] in WATCH:
            found[c[0]] = "%s(%s)=%s/%s" % (c[1], c[0], c[9], c[10])
    if len(found) != len(WATCH):
        raise RuntimeError("dersler bulunamadi: %s" % found)
    return " | ".join(found[k] for k in WATCH)


def notify(msg, title="ITU kontenjan degisti", prio="urgent"):
    req = urllib.request.Request("https://ntfy.sh/" + TOPIC, data=msg.encode(),
                                 headers={"Title": title, "Priority": prio, "Tags": "rotating_light",
                                          "Click": "https://obs.itu.edu.tr/public/DersProgram"})
    urllib.request.urlopen(req, timeout=30)


if __name__ == "__main__":
    if "--test" in sys.argv:
        notify("Test: " + get_kont(), title="ITU izleyici test", prio="default")
        print("test bildirimi gonderildi"); sys.exit()
    old = open(STATE).read().strip() if os.path.exists(STATE) else ""
    for i in range(ROUNDS):
        if i:
            time.sleep(INTERVAL)
        try:
            new = get_kont()
        except Exception as e:
            print("cekilemedi:", e); continue
        print(time.strftime("%H:%M:%S"), new)
        if new != old:
            if old:
                notify("onceki: %s\nsimdi: %s" % (old, new))
            open(STATE, "w").write(new + "\n")
            old = new
