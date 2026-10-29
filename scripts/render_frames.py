#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
逐帧渲染：Playwright 单页循环 seek + 截图
用法：
    python render_frames.py <html路径> <输出目录> [fps] [总时长秒] [起始帧] [结束帧]

例：
    python render_frames.py ../my-archive/index.html ../my-archive/frames 30 191.4

要点：
- HTML 必须支持 ?render=1 并暴露 window.__seek(t) / window.__ready / window.__T
- 实测 1080x1920 约 0.20 s/帧；5730 帧 ≈ 27 分钟
- 每 1000 帧重启一次 page，避免长跑内存累积
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    html = os.path.abspath(sys.argv[1]).replace("\\", "/")
    out = os.path.abspath(sys.argv[2])
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    total = float(sys.argv[4]) if len(sys.argv) > 4 else None
    start = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    end = int(sys.argv[6]) if len(sys.argv) > 6 else None

    os.makedirs(out, exist_ok=True)
    url = "file:///" + html.lstrip("/") + "?render=1"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--force-color-profile=srgb",
            "--disable-lcd-text",
            "--hide-scrollbars",
        ])
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url, wait_until="load")
        page.wait_for_function("window.__ready === true", timeout=30000)
        T = total if total else page.evaluate("window.__T")
        end = end if end else int(T * fps)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)

        t0 = time.time()
        for i in range(start, end):
            page.evaluate("t => window.__seek(t)", i / fps)
            page.screenshot(
                path=os.path.join(out, "f_%05d.jpg" % i),
                type="jpeg", quality=96, animations="disabled", caret="hide",
            )
            if i % 500 == 0:
                el = time.time() - t0
                done = i - start + 1
                eta = el / done * (end - start - done) / 60
                print("frame %d/%d  %.2fs/f  eta %.1f min" % (i, end, el / done, eta), flush=True)
            if i and i % 1000 == 0:
                page.close()
                page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
                page.goto(url, wait_until="load")
                page.wait_for_function("window.__ready === true", timeout=30000)

        print("frames:", end - start, " errors:", errors[:5])
        browser.close()

if __name__ == "__main__":
    main()
