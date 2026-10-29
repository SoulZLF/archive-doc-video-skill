# 混音：配平、闪避、归一

## 第一原则：先量 RMS，再定增益

```
ffmpeg -i bgm.mp3 -af astats -f null -
ffmpeg -i vo.mp3  -af astats -f null -
```

看 `RMS level dB`。

真实案例：配乐源 **−8.2 dB**（接近满刻度的压缩母带），口播源 **−21.7 dB**。
**配乐比人声响 13.5 dB。** 这时候凭感觉写 `volume=0.26` 还是压不住——
0.26 只等于 −11.7 dB，音乐仍在人声之上。这就是「背景音乐太吵」的全部原因。

**目标：配乐比人声低 10–15 dB。**

## 第二原则：只调音量不够，必须配 EQ

压下去的音乐会「闷在后面」，反而更难受。正确做法是把高频让给人声：

```
highpass=f=58            // 切掉低频浑浊，给语音腾出基频空间
highshelf=f=2600:g=-6    // 2.6k 以上压 6dB，这是「退到后面」的关键
lowpass=f=12000          // 再砍掉空气感，避免和齿音打架
volume=<按实测定>
```

## 第三原则：闪避要轻

```
sidechaincompress=threshold=0.05:ratio=2.4:attack=30:release=480
```

`ratio` 6 以上会把音乐抽得一抽一抽，很假；2–3 是「人声一出现，音乐轻轻让一下」。

## 完整滤镜链（可直接复用）

```
[0:a]adelay=1100:all=1[a1];
[1:a]adelay=32300:all=1[a2];
[2:a]adelay=73380:all=1[a3];
[3:a]adelay=115600:all=1[a4];
[4:a]adelay=151880:all=1[a5];
[a1][a2][a3][a4][a5]amix=inputs=5:normalize=0,apad=whole_dur=192,asplit=2[vo][voSC];
[5:a]asplit=2[bga][bgb];
[bga]atrim=0:160.1,asetpts=N/SR/TB[main];
[bgb]atrim=24:58.9,asetpts=N/SR/TB[fill];
[main][fill]acrossfade=d=4:c1=tri:c2=tri[bg1];
[bg1]highpass=f=58,highshelf=f=2600:g=-6,lowpass=f=12000,volume=0.052,
     afade=t=in:st=0:d=3,afade=t=out:st=183:d=8[bg2];
[bg2][voSC]sidechaincompress=threshold=0.05:ratio=2.4:attack=30:release=480[bgd];
[vo][bgd]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:191,
     afade=t=out:st=189.2:d=1.8[mix]
```

三个关键点：

1. **`apad=whole_dur=N` 必须加在侧链上**（见下面的坑）。
2. **`amix` 一定要 `normalize=0`**，否则它会自动把每条降到 1/N。
3. **`atrim` 收尾**，让音轨和画面一样长。

## 三个必踩的坑

### ① `sidechaincompress` 会被侧链截断

它的输出长度跟**侧链**走。口播在 186.5 秒结束，音乐就被一起截断，
最后 4 秒变成纯静音——而画面还在走。

**修法：侧链先 pad。**

```
[a1]..[a5]amix=...,apad=whole_dur=192,asplit=2[vo][voSC]
```

**交付前单独量片尾 3 秒**，确认不是 `-inf`。

### ② `loudnorm` 单遍到不了目标

实测目标 −14，单遍只到 −16.6。必须二次精补：

```
loudnorm=I=-14:TP=-1.5:LRA=11,volume=2.6dB,alimiter=limit=0.841:level=false
```

`0.841` ≈ −1.5 dBFS。补完用 `ebur128=peak=true` 复核。

### ③ BGM 不够长

不要拉伸（变调），用**等功率交叉循环**：

```
[bga]atrim=0:A[main];
[bgb]atrim=S:E[fill];
[main][fill]acrossfade=d=4:c1=tri:c2=tri[bg1]
```

接缝听不出来。取中段（避开前奏）做 fill，长度 = 需要的差额 + 4 秒。

## 换轨不必重渲画面

```
ffmpeg -i film.mp4 -i mix.m4a -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
       -ar 48000 -shortest -movflags +faststart out.mp4
```

两分钟。**改声音永远不要重跑渲染**（27 分钟）。

## 验收数字

| 指标 | 目标 | 命令 |
|---|---|---|
| 整片响度 | −14 LUFS | `-af ebur128=peak=true` |
| 真峰值 | ≤ −1.5 dBFS | 同上 |
| 音乐 vs 人声 | 低 5–8 dB（闪避后 9–10） | 分别 `astats` 量纯音乐段和口播段 |
| 片尾 3 秒 | 非静音 | `-ss 188 -t 3 -af astats` |
