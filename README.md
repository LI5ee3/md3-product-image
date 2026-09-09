# md3-product-image

生成 3:4 Google Classic MD3 电商产品图

Image Gen 生成空背景，产品、固定 50° 二维投影、源 Logo 和 Rubik Variable（默认字重 700）文字在本地合成

母版由用户锁定，SKU 成功后自动写入成品目录

## 母版

上传产品 PNG/WEBP 和 Logo PNG/WEBP：

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

## SKU

上传当前 SKU 产品图：

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

重做成功后原名替换；失败时保留旧成品

## 输出

`output` 只保存 `ORIGINAL_MASTER_FINAL.png` 和最终 `SKU_VARIANT-*.png`
