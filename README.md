# archive-doc-video · 档案体竖屏思辨短视频流水线

一个 WorkBuddy / Claude 类 Agent 的 **Skill 包**。给一个选题，跑完整条流水线：

> 选题 → 25 镜分镜表 → 可播放 HTML 动效原型 → 海螺 TTS 口播稿 → 逐帧渲染 1080×1920 成片

核心特征：**档案/仪器视觉语言 + 逐帧程序化渲染（不用 AI 生视频）+ 口播气口驱动切点**。

---

## 安装

Skill 的安装位置是用户目录下的 `~/.workbuddy/skills/`，文件夹名必须是 `archive-doc-video`。

### 方式 A：git clone（推荐，能一键更新）

**Windows PowerShell：**
```powershell
git clone https://github.com/SoulZLF/archive-doc-video-skill.git "$env:USERPROFILE\.workbuddy\skills\archive-doc-video"
```

**macOS / Linux：**
```bash
git clone https://github.com/SoulZLF/archive-doc-video-skill.git ~/.workbuddy/skills/archive-doc-video
```

### 方式 B：下 zip 解压

1. 浏览器打开 https://github.com/SoulZLF/archive-doc-video-skill/archive/refs/heads/main.zip
2. 解压得到 `archive-doc-video-skill-main/`
3. 把整个文件夹改名成 `archive-doc-video`，放进：
   - Windows：`C:\Users\<你的用户名>\.workbuddy\skills\`
   - macOS / Linux：`~/.workbuddy/skills/`

最终必须是这样（`SKILL.md` 直接在 `archive-doc-video` 目录下一层）：

```
.workbuddy/skills/archive-doc-video/
├── SKILL.md
├── assets/motion-prototype.html
├── references/*.md
└── scripts/*.py, *.sh
```

### 更新

```bash
cd ~/.workbuddy/skills/archive-doc-video && git pull
```

装完重启对话 / 新开一个会话，技能才会被索引到。

---

## 环境依赖

只在**真正出片**的阶段需要，纯写剧本、写口播稿不需要。

| 依赖 | 用途 | 安装 |
|---|---|---|
| Python 3.9+ | 跑两个脚本 | 系统自带或 python.org |
| Playwright (Python) | 逐帧截图渲染 | `pip install playwright` 然后 `playwright install chromium` |
| ffmpeg / ffprobe | 混音、编码、量响度 | Windows: `winget install Gyan.FFmpeg`；macOS: `brew install ffmpeg` |

验证：

```bash
python -c "import playwright; print('ok')"
ffmpeg -version | head -1
```

> Windows 上 `scripts/encode.sh` 用 Git Bash 跑；装了 Git 就有。

---

## 怎么用

装好之后，直接对 Agent 说人话就行，不用记命令：

```
按档案体做一个片子，选题：XXX
```
```
按上次那套流程，出 25 镜分镜
```
```
配音 mp3 在这，把它混了剪进画面
```

技能会被自动加载，Agent 按 `SKILL.md` 里的六个阶段推进：接题 → 剧本 → 动效原型 → 口播稿 → 封面帧 → 混音出片 → 交付核查。

产出目录约定：

```
<主题>-archive/
  index.html            动效原型（?render=1 可逐帧）
  口播稿.txt            带海螺标记的整段纯文本
  分镜总表.png          5×5 拼版，过稿 + 选封面
  封面_1080x1440_3比4.jpg
  成片_<主题>_1080x1920.mp4
```

---

## 包内结构

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 主流程：六阶段、25 镜节奏、七条不可违背的规则 |
| `references/timing.md` | 语速估算、幕界检测、反算权重、长镜预警 |
| `references/visual-system.md` | 色板、字体、栅格、动效参数表 |
| `references/symbol-system.md` | 象征物与母题设计（画物，不画图） |
| `references/cover-frame.md` | 封面三档比例 + 3:4 安全区算法 |
| `references/hailuo-tts.md` | 海螺情绪/语气词语法与配比 |
| `references/audio-mix.md` | RMS 配平、sidechain、loudnorm |
| `references/pitfalls.md` | 踩过的坑，按症状索引 |
| `assets/motion-prototype.html` | 可运行骨架，复制后换 kit |
| `scripts/render_frames.py` | Playwright 逐帧截图 |
| `scripts/make_cover.py` | 按时间点出三档封面 |
| `scripts/encode.sh` | ffmpeg 编码 |

---

## 备注

- 这套流程**不用 AI 生视频模型**。每一帧由 `render(t)` 算出来，所以帧级可控、可复现、改一个参数重渲一镜。
- 代价是要写代码：原型是一个 1000+ 行的单文件 HTML。
- 实测量级：1080×1920 渲染约 0.15–0.20 s/帧，5242 帧 ≈ 15 分钟渲染 + 4 分钟编码。
