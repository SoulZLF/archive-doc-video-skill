#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
封面帧：从成片（或帧目录）按时间抽一帧，裁成各平台的封面比例。

用法：
    python make_cover.py <video|frames_dir> <time_sec> [--out 输出目录]
                         [--ratios 34,916,11] [--y 240] [--tag 第14集]

比例与裁切窗（视频为 1080x1920）：
    3:4   1080x1440   纵窗 y=240..1680   小红书 / 主用
    9:16  1080x1920   原帧               视频号 / 抖音
    1:1   1080x1080   纵窗 y=420..1500   公众号 / 部分信息流

安全区约束（这是硬规则，不是建议）：
    档案体的舞台在 280..980，标题块到 1500。
    3:4 的 1440 高要同时包住这两段，纵窗起点只能落在 60..280。
    默认 240 = 舞台顶留 40px 呼吸。越界工具会警告。
"""
import os, subprocess, sys, json

W, H = 1080, 1920
STAGE = (280, 980)      # 视觉舞台
TITLE_END = 1500        # 标题块底（含副标）
RATIOS = {
    '34':  (1080, 1440, 240),
    '916': (1080, 1920, 0),
    '11':  (1080, 1080, 420),
}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0:
        sys.exit('ffmpeg 失败：\n' + (p.stderr or '')[-1200:])
    return p


def grab(src, t, outdir):
    """取一帧原分辨率 PNG"""
    os.makedirs(outdir, exist_ok=True)
    raw = os.path.join(outdir, '_raw_%0.2f.png' % t)
    if os.path.isdir(src):
        # 帧目录：帧号 = 秒 * 30
        idx = int(round(t * 30))
        cand = os.path.join(src, 'f_%05d.jpg' % idx)
        if not os.path.exists(cand):
            sys.exit('找不到帧：%s' % cand)
        raw = cand
    else:
        # -ss 放在 -i 后面才是精确 seek（放前面会落到关键帧，最多差 2 秒）
        run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
             '-ss', '%.3f' % t, '-frames:v', '1', raw])
    return raw


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    src, t = sys.argv[1], float(sys.argv[2])
    outdir = 'cover'
    ratios = ['34', '916', '11']
    y34 = None
    tag = ''
    a = sys.argv[3:]
    i = 0
    while i < len(a):
        if a[i] == '--out': outdir = a[i + 1]; i += 2
        elif a[i] == '--ratios': ratios = a[i + 1].split(','); i += 2
        elif a[i] == '--y': y34 = int(a[i + 1]); i += 2
        elif a[i] == '--tag': tag = a[i + 1]; i += 2
        else: i += 1

    raw = grab(src, t, outdir)

    # 安全区检查
    y = y34 if y34 is not None else RATIOS['34'][2]
    top, bot = y, y + 1440
    warn = []
    if top > STAGE[0]:
        warn.append('3:4 上边界 %d 切掉舞台顶部 %d px' % (top, top - STAGE[0]))
    if bot < TITLE_END:
        warn.append('3:4 下边界 %d 切掉标题块底部 %d px' % (bot, TITLE_END - bot))
    if not (60 <= y <= 280):
        warn.append('纵窗起点 %d 不在 60..280 安全区' % y)

    made = []
    for r in ratios:
        if r not in RATIOS:
            print('跳过未知比例', r); continue
        w, h, dy = RATIOS[r]
        yy = y if r == '34' else dy
        if r == '916':
            out = os.path.join(outdir, '封面_1080x1920_9比16.jpg')
            run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', raw,
                 '-q:v', '2', out])
        else:
            out = os.path.join(outdir, '封面_%dx%d_%s.jpg' % (w, h, r.replace('34', '3比4').replace('916', '9比16').replace('11', '1比1')))
            run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', raw,
                 '-vf', 'crop=%d:%d:0:%d' % (w, h, yy), '-q:v', '2', out])
        made.append(out)

    print('时间点 %.2f s' % t)
    for o in made:
        from PIL import Image
        im = Image.open(o)
        print('  %-46s %dx%d  %.4f' % (os.path.basename(o), im.size[0], im.size[1],
                                       im.size[0] / im.size[1]))
    if warn:
        print('\n⚠ 安全区：')
        for w_ in warn:
            print('  -', w_)
    else:
        print('\n安全区 OK（%d..%d 覆盖舞台与标题块）' % (top, bot))

    if tag:
        meta = os.path.join(outdir, 'cover.json')
        json.dump({'tag': tag, 'time': t, 'y': y, 'files': [os.path.basename(m) for m in made]},
                  open(meta, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
