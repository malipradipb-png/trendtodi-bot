"""Make one TrendTodi reel from a product JSON: download photo, Hindi voice per slide, render, contact sheet."""
import sys, os, json, asyncio, subprocess, requests
import edge_tts
from PIL import Image
import reel

UA = {"User-Agent": "TrendTodiBot/1.0 (github.com/malipradipb-png)"}


def photo(p, out):
    if p.get("image_url"):
        url = p["image_url"]
    else:  # Wikimedia Commons file title
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
            "action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 1400,
            "titles": "File:" + p["commons_file"]}).json()
        url = list(r["query"]["pages"].values())[0]["imageinfo"][0]["thumburl"]
    open(out, "wb").write(requests.get(url, headers=UA, timeout=60).content)
    return out


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout)


async def voice(lines, work, v):
    files = []
    for i, t in enumerate(lines):
        f = os.path.join(work, f"v{i}.mp3")
        await edge_tts.Communicate(t, v, rate="+8%").save(f)
        files.append(f)
    return files


def main(cfg, out="out"):
    p = json.load(open(cfg))
    work = "work"; os.makedirs(work, exist_ok=True); os.makedirs(out, exist_ok=True)
    img = photo(p, os.path.join(work, "photo.jpg"))
    vs = asyncio.run(voice(p["voice"], work, p.get("tts_voice", "hi-IN-SwaraNeural")))
    durs = [max(2.5, dur(f) + 0.45) for f in vs]
    # one voice track with each line starting at its slide
    parts = []
    for f, d in zip(vs, durs):
        g = f[:-4] + "_pad.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f, "-af", f"apad=whole_dur={d}", "-ar", "44100", "-ac", "2", g], check=True)
        parts.append(g)
    lst = os.path.join(work, "a.txt"); open(lst, "w").writelines(f"file '{os.path.abspath(x)}'\n" for x in parts)
    va = os.path.join(work, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", va], check=True)
    mp4, pngs = reel.render(p, img, work, durs, va)
    os.replace(mp4, os.path.join(out, "reel.mp4"))
    ims = [Image.open(f).resize((360, 640)) for f in pngs]
    c = Image.new("RGB", (360 * 4 + 30, 640), "white")
    for i, im in enumerate(ims):
        c.paste(im, (i * 370, 0))
    c.save(os.path.join(out, "contact.png"))
    print("done", durs)


if __name__ == "__main__":
    main(sys.argv[1])
