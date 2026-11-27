---
name: listing-photo-review
description: 从相同的二手商品说明和原始照片生成两份独立意见，核对覆盖、主图和补拍项并交付本机清单。
---

# 复核流程

使用当前技能目录内 `scripts/review.py`。只读用户授权的原图与商品说明，并且只写本轮授权工作目录。需要 Python 3.10+ 与 WorkSwarm 已开启原生图片读取的视觉模型。使用 `read_file` 读取各张本机照片，将宿主返回的图像作为证据。宿主可能压缩或缩小预览。只有文字、空结果或读取错误就填 `confirm`。不得把图片或文件路径转发给其它服务；使用当前用户授权的模型。

以下路径变量替换为本轮实际路径，`$work` 已存在且由用户授权。命令保留文件名和原件，输出各阶段使用新目录。

```bash
python3 "$skill/scripts/review.py" prepare --source "$source" --photos "$photos" --out "$work/batch"
python3 "$skill/scripts/review.py" seal --source "$source" --photos "$photos" --batch "$work/batch/batch.json" --role evidence --answer "$work/evidence-answer.json" --out "$work/evidence"
python3 "$skill/scripts/review.py" seal --source "$source" --photos "$photos" --batch "$work/batch/batch.json" --role verifier --answer "$work/verify-answer.json" --out "$work/verify"
python3 "$skill/scripts/review.py" deliver --source "$source" --photos "$photos" --batch "$work/batch/batch.json" --evidence "$work/evidence/review.json" --verify "$work/verify/review.json" --out "$work/delivery"
```

两位成员先独立阅读源照片和说明，逐张给出 `usable`（可用于清单）、`retake`（需补拍）、`confirm`（待核实或缺图）。`covers` 仅列可作为主图的可用编号，按偏好排序。逐项写 `supported` 并引用能证明该项的可用照片，或者写 `retake` / `confirm` 并给出下一步。不要省略商品、照片或检查项。示例中的编号取自实际批次文件。

```json
{
  "items": {
    "camera": {
      "covers": ["p01"],
      "photos": {"p01": "usable", "p02": "confirm"},
      "checks": {
        "c01": {"status": "supported", "photos": ["p01"], "note": "正面可看清机身款式。"},
        "c02": {"status": "confirm", "photos": [], "note": "右侧划痕被反光遮挡，请核对后补拍近景。"}
      }
    }
  }
}
```

主理人只读两份封存文件，检查真实宿主任务和各自回执后交付。两位成员支持同一张可用照片才能为对应事实提供证据。批次内容变化、意见缺漏或角色不对应时重新核对。清单中的暂缓项不给可发布的照片顺序。
