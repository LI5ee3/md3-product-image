# md3-product-image

生成 3:4 Google Material Design 3（Classic MD3）电商产品主图。

Image Gen 只负责生成空背景；产品、固定 50° 二维投影、源 Logo、Rubik Variable（默认字重 700）标题/版本文字以及最终合成都由本地确定性脚本完成。

母版必须由用户明确锁定。锁定后，后续 SKU 复用母版构图关系并自动写入最终成品目录。

## 当前生产合同

- `1536 × 2048` 仅是逻辑布局坐标系，不代表最终 PNG 必然使用该分辨率。
- MASTER 接受任意严格 3:4 的实际 Image Gen raster；用户锁定后，该实际宽高成为该产品所有 SKU 的硬约束。
- SKU 背景必须与已锁定 MASTER 的实际宽高完全一致；同为 3:4 但尺寸不同也会确定性失败，不自动重试或放大。
- 产品颜色通过本地确定性 `palette-reference.png` 提供给 Image Gen；完整产品图保留在本地用于最终合成，不作为配色参考发送给 Image Gen。
- MASTER 的 Image Gen 引用仅为 `palette-reference.png`。
- SKU 的 Image Gen 引用仅为 `ORIGINAL_MASTER_BACKGROUND.png` + 当前 SKU 的 `palette-reference.png`。
- Work 运行时通过显式 `referenced_image_paths` 传入权威参考图；`num_last_images_to_include` 完全省略。
- 当前已验证的 Work + Skill 接口不直接暴露 model、quality、resolution、background/transparency、output format 或 edit/action 选择器，因此 Skill 不推断或硬编码这些公开 API 参数。
- SKU 使用“母版背景作为构图参考 + SKU 色板作为颜色参考”的新背景生成路径，不把现有背景编辑语义当作生产能力。

## 母版

上传产品 PNG/WEBP 和 Logo PNG/WEBP，并提供明确的标题行数和文字：

```text
使用 $md3-product-image

完整产品名称：[完整名称]
产品名称显示行数：[一行/两行]
产品名称第一行：[文字]
产品名称第二行：[仅两行时填写]
版本文字：[可选；无则删除本行]

创建一个母版预览
```

Skill 会依次完成：

```text
MEASURE
→ PALETTE
→ BUILD_PROMPT
→ IMAGE_GEN_BACKGROUND
→ LOCAL_FULL_COMPOSITE
→ 等待用户决定
```

确认候选后发送：

```text
锁定母版
```

只有这一步会把当前候选绑定为 `ORIGINAL_MASTER_FINAL.png`，并记录实际 MASTER raster。

需要重做时发送：

```text
重做母版
```

可在重做指令中附加额外背景要求；新增要求会按该完整产品名称持续累积。

## SKU

母版锁定后，上传当前 SKU 产品图：

```text
生成 SKU 变体
```

成功后自动写入：

```text
SKU_VARIANT-A.png
SKU_VARIANT-B.png
...
```

重做最近完成的 SKU：

```text
重做当前 SKU
```

重做指定 SKU：

```text
重做 SKU_VARIANT-A
```

SKU 重做在新结果通过确定性检查前不会覆盖旧成品；失败时保留原文件，成功后原名原子替换，并且不消耗新的 SKU 序号。

## 本地确定性职责

以下内容始终不交给图像模型生成：

- 权威产品图
- 源 Logo
- 标题和版本文字
- Rubik Variable 字体渲染（默认字重 700）
- 产品位置和尺寸规则
- 固定 50° 二维投影
- 信息安全区计算
- 产品目录、源文件哈希和可复用资产身份
- MASTER 绑定
- SKU 命名和重做替换

每次用户生成指令最多触发一次 Image Gen 调用。确定性失败不会触发自动图像重试，视觉是否接受由用户决定。

## 输出

每个完整产品名称使用独立产品目录。

`output` 只保存最终成品：

```text
ORIGINAL_MASTER_FINAL.png
SKU_VARIANT-*.png
```

布局、色板缓存、母版背景、提示词增量和其他可复用资产保存在该产品目录中。

## 回归

长期回归入口为 `.github/workflows/regression.yml`，覆盖原工作流、raster contract、structured prompt、palette extraction/cache 和 Work reference-path 合同。

升级过程和真实 Work 验证证据保存在 `docs/`。
