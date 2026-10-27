---
name: video-channel-ops
description: 在视频频道运营目录（含 channel.json 与 OPERATIONS.md）中创建频道、制作当天的长 / 短视频、记录生成任务、渲染与上传前检查、记录发布结果和指标时使用；规定防重复制作、job ID 立即记录与“上传尝试不等于完成”的标准。
version: 1.0.1
---

# 视频频道日更流水线

在频道目录中工作时始终遵守本说明。各频道的具体规则以该目录下的 `OPERATIONS.md` 为准。所有调用使用同一个 `channel_dir`（绝对路径；Windows 路径如 `D:\\频道\\世界新闻` 可直接传入）。默认用简体中文回复，用户明确要求其他语言时照办。

## 用户说法与调用

| 用户意图 | 做法 |
| --- | --- |
| “新建一个频道” / “建频道目录” | 只有频道名称是必填。用户已给出名称时直接 `video_channel new_channel`，没给的项全部留空，**不要再追问**。用户没给名称时，用**一条消息**同时列出全部可选项（名称、handle、语言、时区、主题与语气、长 / 短视频规格、配音工具与 voice_id、画面工具与风格）请用户一次回答；用户回答后无论缺什么都直接创建，不再逐项提问。目录已有 channel.json 时工具会拒绝，不要换路径绕过。完成后告诉用户：先按自己的频道修改 OPERATIONS.md；第一期在不上传的情况下试做 |
| “做今天的视频” / “日更” | 按下方“每日制作”执行 |
| “检查这个视频能不能传” | `video_channel preflight video=<mp4> srt=<srt>`，原样展示每项 PASS/WARN/FAIL，再列出 human_checklist，未确认的写“未确认”。有 FAIL 时明确说不要上传 |
| “渲染视频” | 确认运行目录中有 scenes.json 和 narration.* 后 `video_channel render run_dir=...`（横屏加 long_form=true） |
| “视频已经发出去了，ID 是…” | 用户没说是“已预约”还是“已公开”时先问，不要猜。然后 `video_channel publish`：第一次调用**只会**返回 question 和 confirm_token，不会记录。把 question 原样问用户并**结束本轮回复**；用户在下一条消息中明确确认后，才用同样参数加 confirm_token 再调用。绝不在同一轮里替用户确认 |
| “记录指标” | `video_channel log_metric`，elapsed_hours 填实际经过的小时数；平台仍在处理的数值留空，不填 0 |
| “允许自动上传” / “允许付费” | 先复述将改变什么，用户明确同意后 `video_channel authorize ... confirm=true` |
| 今天进度如何 | `video_channel status` |

## 每日制作

1. `video_channel status`。今天某栏位已有视频 ID 时只报告，不再制作该栏位；两个栏位都完成则直接结束。
2. 从头到尾读完 `OPERATIONS.md`，先执行其中“开工前检查”。status 返回进行中的 job 时，用原 job ID 继续查询结果，不要重新提交。
3. 按 7 步依次做：调研 → 脚本 → 配音 → 画面 → 渲染 → 字幕与检查 → 上传。每一步结束都用 `video_channel log_step` 记录结果文件和状态（完成 / 进行中 / 待人工 / 跳过 / 失败）。
4. 每次提交付费生成请求（配音、图片、视频）后**立即** `video_channel log_job`（job_id、tool、预计 credits）。拿到结果后 `video_channel job_done`。
5. 当前环境没有连接配音或视频生成工具时，只做到脚本、场景列表 `scenes.json` 和生成提示词，相应步骤记为“待人工”，并整理“需要人来做的事”清单后停下。绝不把没有用过的工具说成用过。
6. 渲染完成不等于完成：必须 `preflight` 无 FAIL。
7. 上传需要用户自己连接的平台上传工具。`authorization.daily_upload` 为 false 或没有上传工具时，不上传，上传步骤记为“跳过”，只告诉用户最终文件路径；不要声称会替用户预约或上传。为 true 且有上传工具时，上传后按上面的两步 publish 记录；上传步骤不能用 log_step 记为“完成”（工具会拒绝）。
8. 最后 `video_channel finish_day`，用不超过 3 行汇报：今天做了什么 / 花了多少 credits / 卡在哪里。
9. 汇报进度时，每一步的状态按工具返回的 steps 原样转述（例如上传记的是“跳过”就说跳过），不要自行改写。工具返回 warnings 时必须告诉用户。

## 重复与费用

- 同一天同一栏位不做两次；工具会拒绝在已有视频 ID 的栏位上继续记录制作进度。
- 不做任何额外付费、充值或订阅变更；需要时把金额和理由交给用户决定。

## 内容

- 区分事实与分析（推断），写下来源 URL 和核实时间。
- 不使用授权不明的照片、电视画面或音乐；不制作只加翻译字幕的搬运视频。
- 不使用承诺播放量或收益的表达。

## 记录

- 指标在发布后 24 小时、72 小时、7 天分别记录（publish 会自动排好，status 的 metrics_due 显示到期项）。晚测的数值连同实际经过时间一起记录。
- 短视频与长视频分开比较；同类样本少于 3 条不下结论。

## render 的输入

`<run_dir>/scenes.json`：`[{"image": "scene01.png", "duration": 3.5}, ...]`（路径相对运行目录）；`<run_dir>/narration.mp3`（或 .wav/.m4a/.aac）。输出 `<run_dir>/final.mp4`，默认 1080×1920，旁白比画面长时自动拉长最后一个场景。字幕不烧录，单独上传。需要本机已安装 FFmpeg（或用环境变量 FFMPEG_PATH / FFPROBE_PATH 指定）。
