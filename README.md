# md3-product-image

生成 3:4 Google Material Design 3（Classic MD3）电商产品主图。

Image Gen 只生成空背景；产品、固定 50° 二维投影、源 Logo 和 Rubik Variable（默认字重 700）文字均由本地确定性脚本合成。

Images 2.5 生产流程使用结构化 Markdown 提示词、确定性色板参考和锁定 MASTER raster 合同。完整产品图不会为了配色发送给 Image Gen。

## 母版

上传产品 PNG/WEBP 和 Logo PNG/WEBP，并提供完整产品名称、标题行数与文字：

```text
使用 $md3-product-image

完整产品名称：[完整名称]
产品名称显示行数：[一行/两行]
产品名称第一行：[文字]
产品名称第二行：[仅两行时填写]
版本文字：[可选；无则删除本行]

创建一个母版预览
```

确认后发送：

```text
锁定母版
```

MASTER 锁定后，其实际 3:4 raster 成为该产品所有 SKU 的尺寸合同。

## SKU

上传当前 SKU 产品图后发送：

```text
生成 SKU 变体
```

重做最近完成的 SKU：

```text
重做当前 SKU
```

重做指定 SKU：

```text
重做 SKU_VARIANT-A
```

SKU 使用已锁定 MASTER 背景作为构图参考，并使用当前 SKU 的确定性色板作为颜色参考。重做成功后原名替换；失败时保留旧成品。

## 输出

`output` 只保存 `ORIGINAL_MASTER_FINAL.png` 和最终 `SKU_VARIANT-*.png`。
