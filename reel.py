"""TrendTodi reel renderer: product dict + photo + per-slide voice -> 1080x1920 vertical reel."""
import os, subprocess, base64, random
from playwright.sync_api import sync_playwright

W, H, FPS = 1080, 1920, 30

CSS = """
*{margin:0;box-sizing:border-box} body{width:1080px;height:1920px;overflow:hidden;font-family:Poppins,sans-serif;color:#2a0a17;
background:#2a0a17}
.bg{position:absolute;inset:0;background-size:cover;background-position:center}
.blur{filter:blur(28px) brightness(.55);transform:scale(1.15)}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(40,0,20,.75) 0,rgba(40,0,20,.1) 38%,rgba(40,0,20,.1) 60%,rgba(40,0,20,.85) 100%)}
.pink{position:absolute;inset:0;background:radial-gradient(circle at 50% 30%,rgba(255,179,201,.35),rgba(194,24,91,.55))}
.brand{position:absolute;top:70px;left:0;right:0;text-align:center;font-weight:800;font-size:46px;letter-spacing:2px;color:#fff;
text-shadow:0 4px 18px rgba(0,0,0,.5)} .brand b{color:#ffd54a}
.big{position:absolute;left:60px;right:60px;text-align:center;font-weight:800;line-height:1.08;color:#fff;text-shadow:0 6px 26px rgba(0,0,0,.6)}
.card{position:absolute;left:70px;right:70px;background:#fff;border-radius:48px;box-shadow:0 30px 80px rgba(0,0,0,.5);overflow:hidden}
.pill{display:inline-block;background:#ffd54a;color:#2a0a17;font-weight:800;border-radius:60px;padding:14px 40px}
.off{position:absolute;top:30px;right:30px;background:#e91e63;color:#fff;font-weight:800;font-size:52px;border-radius:50%;
width:190px;height:190px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1;transform:rotate(12deg);
box-shadow:0 10px 30px rgba(0,0,0,.35)}
.feat{display:flex;align-items:center;gap:30px;background:rgba(255,255,255,.95);border-radius:36px;padding:34px 40px;margin-bottom:34px;
font-size:50px;font-weight:700;box-shadow:0 16px 40px rgba(0,0,0,.35)} .feat i{font-style:normal;font-size:64px}
.credit{position:absolute;bottom:22px;left:0;right:0;text-align:center;font-size:20px;color:rgba(255,255,255,.75)}
.thumb{position:absolute;border-radius:40px;background-size:cover;background-position:center;box-shadow:0 20px 50px rgba(0,0,0,.5);border:8px solid #fff}
"""
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">'


def slides(p, img):
    u = f"url('{img}')"
    brand = '<div class="brand">TREND<b>TODI</b></div>'
    credit = f'<div class="credit">{p.get("credit","")}</div>'
    s1 = f"""<div class="bg" style="background-image:{u}"></div><div class="shade"></div>{brand}
<div class="big" style="top:200px;font-size:112px">{p['hook1']}</div>
<div class="big" style="bottom:200px;font-size:92px;color:#ffd54a">{p['hook2']}</div>{credit}"""
    s2 = f"""<div class="bg blur" style="background-image:{u}"></div><div class="pink"></div>{brand}
<div class="card" style="top:190px;height:1230px">
<div style="position:absolute;top:0;left:0;right:0;height:850px;background:{u} center/cover"></div><div class="off">{p['off']}<br>OFF</div>
<div style="position:absolute;bottom:50px;left:40px;right:40px;text-align:center">
<div style="font-size:60px;font-weight:800;line-height:1.1">{p['name']}</div>
<div style="margin-top:22px;font-size:100px;font-weight:800;color:#c2185b">₹{p['price']}
<span style="font-size:56px;color:#999;text-decoration:line-through;font-weight:600">₹{p['mrp']}</span></div></div></div>
<div class="big" style="top:1500px;font-size:68px">{p['line2']}</div>{credit}"""
    feats = "".join(f'<div class="feat"><i>{e}</i>{t}</div>' for e, t in p["features"])
    s3 = f"""<div class="bg blur" style="background-image:{u}"></div><div class="pink"></div>{brand}
<div class="big" style="top:220px;font-size:96px">Kyun lena chahiye?</div>
<div style="position:absolute;top:500px;left:80px;right:80px">{feats}</div>
<div class="thumb" style="left:340px;top:1380px;width:400px;height:440px;background-image:{u}"></div>{credit}"""
    s4 = f"""<div class="bg blur" style="background-image:{u}"></div><div class="pink"></div>{brand}
<div class="big" style="top:330px;font-size:104px">Link chahiye? 👇</div>
<div style="position:absolute;top:660px;left:0;right:0;text-align:center"><span class="pill" style="font-size:80px">Comment karo "LINK"</span></div>
<div class="big" style="top:900px;font-size:60px">DM mein turant link aayega</div>
<div class="big" style="top:1080px;font-size:58px;color:#ffd54a">Roz naye loot deals 🔥<br>Follow @trendtodi</div>
<div class="thumb" style="left:340px;top:1380px;width:400px;height:440px;background-image:{u}"></div>{credit}"""
    return [s1, s2, s3, s4]


def render(p, image, out_dir, durations, audio=None):
    os.makedirs(out_dir, exist_ok=True)
    img = "data:image/jpeg;base64," + base64.b64encode(open(image, "rb").read()).decode()
    pngs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides(p, img)):
            pg.set_content(f"<html><head>{FONTS}<style>{CSS}</style></head><body>{s}</body></html>", wait_until="networkidle")
            pg.wait_for_timeout(500)
            f = os.path.join(out_dir, f"s{i}.png"); pg.screenshot(path=f); pngs.append(f)
        b.close()
    T = 0.35
    clips = []
    for i, (f, d) in enumerate(zip(pngs, durations)):
        d = d + (T if i < len(pngs) - 1 else 0)
        n = int(d * FPS); c = os.path.join(out_dir, f"c{i}.mp4")
        z = f"1+0.07*on/{n}" if i % 2 == 0 else f"1.07-0.07*on/{n}"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f, "-vf",
                        f"scale=2160:3840,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
                        "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", c], check=True)
        clips.append((c, d))
    inputs = sum((["-i", c] for c, _ in clips), []); fc = []; last = "[0:v]"; off = 0
    for i in range(1, len(clips)):
        off += clips[i - 1][1] - T
        fc.append(f"{last}[{i}:v]xfade=transition=slideup:duration={T}:offset={off:.2f}[v{i}]"); last = f"[v{i}]"
    total = sum(durations)
    out = os.path.join(out_dir, "reel.mp4")
    music = f"aevalsrc='0.05*sin(2*PI*220*t)*exp(-5*mod(t,0.5))+0.035*sin(2*PI*330*t)*exp(-5*mod(t+0.25,0.5))+0.02*sin(2*PI*110*t)':d={total:.2f}"
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-f", "lavfi", "-i", music]
    n = len(clips)
    if audio:
        cmd += ["-i", audio]
        fc.append(f"[{n}:a]volume=0.6[m];[{n+1}:a]volume=1.6[vo];[vo][m]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        fc.append(f"[{n}:a]anull[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", last, "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", out]
    subprocess.run(cmd, check=True)
    return out, pngs
