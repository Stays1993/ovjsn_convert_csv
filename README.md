```markdown
# 奥维地图 OVJSN 转 CSV 工具

将奥维地图导出的 `.ovjsn` 文件（JSON 格式）批量转换为结构化的 CSV 表格，自动解析点位名称及其配套设施数量。

## 功能特点

- 自动读取 `input` 文件夹下的所有 `.ovjsn` 文件
- 提取文件夹名称作为 CSV 文件名
- 解析 `Comment` 字段中的设备清单（如“设备×2”、“设备2x1”）
- 生成动态列宽表格，每种设备为一列，数量填入对应单元格
- 自动处理 UTF-8 BOM 编码问题
- 输出文件以时间戳为前缀，避免覆盖
- 支持批量转换

## 目录结构

项目根目录/
├── ovjsn_convert_csv.py   # 主脚本
├── input/                 # 放置 .ovjsn 文件的文件夹（需手动创建）
│   ├── 示列.ovjsn
│   └── 示列2.ovjsn
└── output/                # 转换后 CSV 文件输出目录（自动创建）
    ├── 20260611_143025_示列.csv
    └── 20260611_143025_示列2.csv

## 使用方法

### 1. 准备环境

- 安装 Python 3.6 或更高版本
- 无需额外安装第三方库（仅使用标准库）

### 2. 运行脚本

**Windows (PowerShell / CMD)**
```bash
python ovjsn_convert_csv.py
```

**Linux / macOS**
```bash
python3 ovjsn_convert_csv.py
```

### 3. 查看输出

转换完成后，所有 CSV 文件会保存在 `output` 文件夹中，文件名格式为：  
`时间戳_原始文件夹名称.csv`

## 输入文件格式示例

`.ovjsn` 文件内容结构（简化）：

```json
{
  "ObjItems": [
    {
      "Object": {
        "Name": "示列",
        "ObjectDetail": {
          "ObjChildren": [
            {
              "Object": {
                "Name": "01点位",
                "Comment": "设备×1\r\n设备2x1\r\n设备4×1"
              }
            }
          ]
        }
      }
    }
  ]
}
```

## 输出 CSV 示例

| Name | 设备2 | 设备 | 监控箱 | 设备4
|------|----------|--------|--------|------|
| 01点位 | 1        | 1      | 1      | 1    |
| 02点位 | 2        | 2      | 1      | 1    |
| 11点位 |          | 2      | 1      | 1    |

## 解析规则

- 支持 `×` 和 `x` 作为数量分隔符（例如“设备×2”）
- 若一行中没有数量符号，则默认数量为 1
- Comment 字段中多行用 `\r\n` 分隔
- 设备类型自动去重并排序

## 常见问题

### Q: 提示“输入目录中没有 .ovjsn 文件”
A: 请确保在脚本同级目录下创建了 `input` 文件夹，并将 `.ovjsn` 文件放入其中。

### Q: JSONDecodeError: Unexpected UTF-8 BOM
A: 本脚本已使用 `utf-8-sig` 编码自动处理 BOM，请确保使用最新版本脚本。

### Q: 输出 CSV 中某些单元格为空
A: 空单元格表示该监控点不含此设备类型，不影响数据分析。

## 自定义修改

如需修改输出列的处理逻辑（例如将空值改为 0），可编辑脚本中的：

```python
row_list.append(count if count != '' else '')
```

将 `''` 改为 `0` 即可。

## 许可证

MIT License
```
