# AEP/AEPX 二进制数据结构规格说明

本文档描述了 Adobe After Effects 项目文件（`.aep` 二进制格式 / `.aepx` XML 格式）的内部数据结构，
基于逆向工程分析编写。

---

## 目录

1. [文件容器格式](#1-文件容器格式)
2. [RIFF 数据块布局](#2-riff-数据块布局)
3. [数据块类型参考](#3-数据块类型参考)
4. [项目层级结构](#4-项目层级结构)
5. [项目版本信息 (head / svap)](#5-项目版本信息-head--svap)
6. [项目元素数据 (idta)](#6-项目元素数据-idta)
7. [合成数据 (cdta)](#7-合成数据-cdta)
8. [图层数据 (ldta)](#8-图层数据-ldta)
9. [属性系统](#9-属性系统)
10. [动画属性 (tdbs)](#10-动画属性-tdbs)
11. [关键帧格式](#11-关键帧格式)
12. [素材数据](#12-素材数据)
13. [效果定义](#13-效果定义)
14. [遮罩数据 (mkif)](#14-遮罩数据-mkif)
15. [贝塞尔形状 (shph)](#15-贝塞尔形状-shph)
16. [渐变数据 (GCst)](#16-渐变数据-gcst)
17. [文字数据 (btdk / COS 格式)](#17-文字数据-btdk--cos-格式)
18. [标记数据 (Nmrd)](#18-标记数据-nmrd)
19. [图层样式](#19-图层样式)
20. [AEPX XML 格式](#20-aepx-xml-格式)
21. [常量与枚举](#21-常量与枚举)
22. [Match Name 参考表](#22-match-name-参考表)
23. [写回 / RIFF 序列化](#23-写回--riff-序列化)

---

## 1. 文件容器格式

AEP 文件使用 **RIFF**（Resource Interchange File Format，资源交换文件格式）容器。

### 文件头（12 字节）

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       4     magic           char[4]   "RIFX"（大端序）或 "RIFF"（小端序）
4       4     file_size       uint32    总文件大小减去 8 字节
8       4     file_type       char[4]   "Egg!" — After Effects 文件标识符
```

- **RIFX** = 大端字节序（Big-endian，AEP 文件最常见的格式）
- **RIFF** = 小端字节序（Little-endian）
- 文件中所有多字节整数和浮点数都遵循此字节序

### 尾部数据（XMP 元数据）

AEP 文件可能在 RIFX 数据块之后附加 **XMP 元数据**。此数据不属于 RIFF 结构，在往返保存时必须保留。

```
[RIFX 数据块 (8 + file_size 字节)] [XMP 元数据 (可变, 通常 ~14KB)]
```

RIFX 数据块的边界在偏移量 `8 + file_size`（其中 `file_size` 是偏移量 4 处的 uint32 值）。超出此偏移量的所有字节都是尾部数据。

### AEPX 检测

AEPX 文件基于 XML 格式。它们以 `<?xml` 或 `<AfterEffectsProject` 开头，
而非 RIFF/RIFX 魔数字节。XML 格式的详细说明见[第 19 节](#19-aepx-xml-格式)。

---

## 2. RIFF 数据块布局

文件中的每个数据单元都是一个**数据块（Chunk）**：

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       4     header          char[4]   数据块类型标识（ASCII）
4       4     size            uint32    此字段之后的数据字节数
8       size  data            不定      数据块载荷
```

- 数据块按 **2 字节边界** 对齐（若 `size` 为奇数则填充 1 字节）
- **LIST 数据块** 包含一个 4 字节子类型，后跟子数据块：

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       4     header          char[4]   "LIST"
4       4     size            uint32    子类型 + 所有子块的总大小
8       4     list_type       char[4]   列表子类型（如 "Fold"、"Item"、"Layr"）
12      ...   children        Chunk[]   子数据块序列
```

---

## 3. 数据块类型参考

### 容器数据块（LIST 子类型）

| 子类型 | 说明 |
|--------|------|
| `Fold` | 项目根文件夹 |
| `Item` | 项目元素（合成、文件夹或素材） |
| `Sfdr` | 子文件夹 |
| `Layr` | 合成中的图层 |
| `SecL` | 段落图层（合成标记） |
| `Pin ` | 素材挂载点（素材数据容器） |
| `EfdG` | 效果定义组 |
| `EfDf` | 单个效果定义 |
| `parT` | 效果参数模板列表 |
| `tdgp` | 属性组 |
| `tdbs` | 动画属性数据 |
| `tdsn` | 属性显示名称容器（内含 Utf8） |
| `fnam` | 文件/效果名称容器（内含 Utf8） |
| `pdnm` | 参数显示名称容器（内含 Utf8） |
| `Als2` | 文件别名容器（内含 alas） |
| `om-s` | 动画形状属性 |
| `omks` | 形状关键帧集合 |
| `shap` | 单个形状定义 |
| `GCst` | 动画渐变属性 |
| `GCky` | 渐变关键帧集合 |
| `otst` | 动画方向属性 |
| `otky` | 方向关键帧集合 |
| `mrst` | 动画标记属性 |
| `mrky` | 标记关键帧集合 |
| `Nmrd` | 命名记录（单个标记） |
| `btds` | 动画文字属性 |
| `sspc` | 源参数 / 效果实例 |
| `list` | 通用关键帧列表容器 |

### 数据块（叶级二进制）

| 头标识 | 大小 | 说明 |
|--------|------|------|
| `Utf8` | 可变 | UTF-8 编码字符串 |
| `wsnm` | 可变 | UTF-16 编码工作区名称 |
| `tdmn` | 可变 | Match Name 字符串（ADBE 标识符） |
| `head` | 20 | 项目头部（格式级别、版本号） |
| `svap` | 4 | 最后保存的 AE 版本标识符 |
| `idta` | ~20 | 元素元数据（类型、ID） |
| `cdta` | ~142 | 合成元数据（尺寸、帧率、时长） |
| `ldta` | ~164 | 图层元数据（时间、标志位、混合模式） |
| `tdsb` | 4 | 属性可见性/分裂/启用标志 |
| `tdb4` | ~69 | 属性类型元数据（维度、类型标志） |
| `cdat` | 可变 | 静态属性值（float64 数组） |
| `tdum` | 8 | 属性最小值边界（float64） |
| `tduM` | 8 | 属性最大值边界（float64） |
| `lhd3` | ~20 | 关键帧列表头（数量、单项大小） |
| `ldat` | 可变 | 关键帧列表数据（二进制数组） |
| `opti` | 可变 | 素材选项（纯色颜色或类型代码） |
| `sspc` | 可变 | 源参数（宽度、高度、序列信息） |
| `alas` | 可变 | 文件引用（JSON 字符串） |
| `mkif` | 12 | 遮罩信息（模式、反转、锁定） |
| `shph` | 20 | 形状头（边界框、闭合标志） |
| `btdk` | 可变 | 文字二进制数据（COS 格式） |
| `NmHd` | ~17 | 标记头（时长、标志） |
| `tdpi` | 4 | 图层引用目标 ID |
| `tdps` | 4 | 图层引用源 |
| `tdli` | 4 | 无符号整数引用 |
| `otda` | 24 | 方向数据（3× float64） |

---

## 4. 项目层级结构

整体数据块树结构：

```
RIFX "Egg!"
├── LIST Fold                       ← 项目根文件夹
│   ├── LIST Item                   ← 文件夹元素
│   │   ├── idta                    ← item_type=1（文件夹）
│   │   ├── Utf8                    ← 文件夹名称
│   │   └── LIST Sfdr              ← 子文件夹内容
│   │       └── LIST Item ...
│   │
│   ├── LIST Item                   ← 合成元素
│   │   ├── idta                    ← item_type=4（合成）
│   │   ├── Utf8                    ← 合成名称
│   │   ├── cdta                    ← 合成元数据
│   │   ├── LIST Layr              ← 图层 1
│   │   │   ├── ldta               ← 图层数据
│   │   │   ├── Utf8               ← 图层名称
│   │   │   └── LIST tdgp          ← 属性树根节点
│   │   │       ├── tdmn           ← "ADBE Transform Group"
│   │   │       ├── LIST tdgp      ← 变换组
│   │   │       │   ├── tdmn       ← "ADBE Position"
│   │   │       │   ├── LIST tdbs  ← 动画位置属性
│   │   │       │   │   ├── tdsb   ← 标志位
│   │   │       │   │   ├── tdb4   ← 类型元数据
│   │   │       │   │   ├── cdat   ← 静态值
│   │   │       │   │   ├── list   ← 关键帧（有动画时）
│   │   │       │   │   └── Utf8   ← 表达式（如有）
│   │   │       │   └── ...
│   │   │       └── ...
│   │   ├── LIST Layr              ← 图层 2
│   │   └── LIST SecL              ← 合成标记
│   │
│   └── LIST Item                   ← 素材元素
│       ├── idta                    ← item_type=7（素材）
│       ├── Utf8                    ← 素材名称
│       └── LIST Pin               ← 素材容器
│           ├── sspc               ← 源尺寸
│           ├── opti               ← 素材类型/选项
│           ├── LIST Als2          ← 文件引用（文件素材时）
│           │   └── alas           ← JSON 路径数据
│           └── Utf8               ← 名称部分
│
└── LIST EfdG                       ← 效果定义
    └── LIST EfDf                   ← 单个效果
        ├── tdmn                    ← 效果 Match Name
        └── LIST sspc              ← 效果模板
            ├── LIST fnam          ← 显示名称
            └── LIST parT          ← 参数定义
```

---

## 5. 项目版本信息 (head / svap)

AE 版本信息存储在 RIFX 根节点下的两个顶层数据块中。

### head 数据块（20 字节）

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       2     format_level    uint16    文件格式级别
2       2     format_sub      uint16    格式子版本号（不是 AE 次版本号）
4       4     version_id      uint32    AE 版本标识符（与 svap 相同）
8       12    （保留）         —         时间戳、内部计数器
```

### svap 数据块（4 字节）

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       4     version_id      uint32    AE 版本标识符（与 head[4:8] 相同）
```

### version_id 位域编码

`version_id`（svap 4 字节 = head[4:8]）将完整 AE 版本编码为大端序 uint32 的位域：

```
Bit 31    30-26     25-22    21-19     18-15   14-11   10   9      8   7-0
[保留]  [maj_a 5b] [os 4b] [maj_b 3b] [minor] [patch] [r] [beta] [r] [build]
```

| 字段 | 位 | 说明 |
|------|-----|------|
| maj_a | 30-26 | 主版本号高位（5 位） |
| os | 25-22 | 操作系统代码：12=Windows, 13=macOS Intel, 14=macOS ARM |
| maj_b | 21-19 | 主版本号低位（3 位） |
| minor | 18-15 | 次版本号（4 位） |
| patch | 14-11 | 补丁版本号（4 位） |
| beta | 9 | 0=测试版, 1=正式版 |
| build | 7-0 | 构建号（8 位） |

**AE 主版本号：** `major = maj_a × 8 + maj_b`

**解码示例**（`0x0F0B2603` → AE 25.6.4）：

```
0x0F0B2603 = 00001111 00001011 00100110 00000011

maj_a  = 00011  = 3
os     = 1100   = 12 (Windows)
maj_b  = 001    = 1
minor  = 0110   = 6
patch  = 0100   = 4
beta   = 1      （正式版）
build  = 00000011 = 3

major = 3 × 8 + 1 = 25  →  AE 25.6.4 build 3
```

### 已知 version_id 值

| version_id | AE 版本 | 操作系统 |
|---|---|---|
| `0x0B3B0637` | 23.6.0 | Windows |
| `0x0F000637` | 24.0.0 | Windows |
| `0x0F098E03` | 25.3.1 | Windows |
| `0x0F0A0656` | 25.4.0 | Windows |
| `0x0F0A8604` | 25.5.0 | Windows |
| `0x0F0B2603` | 25.6.4 | Windows |
| `0x0F100643` | 26.0.0 | Windows |

### format_level

`head[0:2]` 是文件格式级别。它在二进制格式变更时递增，但**不**与 AE 主版本号一一对应。应使用 `version_id` 进行准确的版本检测。

### head[2:4] (format_sub)

`head[2:4]` 是内部格式子版本计数器。它**不**对应 AE 次版本号，尽管偶尔会出现巧合匹配。不应用于版本检测。

### 手动编辑的十六进制偏移量

在典型 AEP 文件中：

| 数据块 | 偏移量 | 大小 | 说明 |
|--------|--------|------|------|
| `svap` | 0x14 | 4 | `version_id` — AE 版本位域 |
| `head` format_level | 0x20 | 2 | uint16 — 文件格式级别 |
| `head` format_sub | 0x22 | 2 | uint16 — 格式子版本号 |
| `head` version_id | 0x24 | 4 | 与 svap 相同的值 |

> **注意：** 这些偏移量假设标准 AEP 文件布局。`svap` 数据块是 RIFX 根的第一个子块，后跟 `head`。
>
> **参考来源：** 位域编码基于 [forticheprod/aep_parser](https://github.com/forticheprod/aep_parser) 和 [tinogithub/aftereffects-version-check](https://github.com/tinogithub/aftereffects-version-check)。

---

## 6. 项目元素数据 (idta)

标识项目元素的类型和 ID。

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       2     item_type       uint16    元素类型代码
2       14    (保留)          —         —
16      4     item_id         uint32    唯一元素标识符
```

**元素类型代码：**

| 值 | 含义 |
|----|------|
| 1 | 文件夹 |
| 4 | 合成 |
| 7 | 素材（图片、纯色、视频、音频） |

---

## 7. 合成数据 (cdta)

存储合成级别的元数据。时间值使用**有理数**编码。

```
偏移量  大小  字段名              类型      说明
─────────────────────────────────────────────────────────
0       4     (保留)              —         —
4       4     time_denom          uint32    帧率分母
8       4     time_num            uint32    帧率分子
                                            帧率 = time_num / time_denom
12      9     (保留)              —         —
21      2     playhead_raw        uint16    播放头位置（原始值）
23      2     (保留)              —         —
25      2     playhead_div        uint16    播放头除数
                                            播放头时间 = playhead_raw / (playhead_div / fps)
27      2     (保留)              —         —
29      2     in_time_raw         uint16    工作区入点（原始值）
31      2     (保留)              —         —
33      2     in_time_div         uint16    入点除数
35      2     (保留)              —         —
37      2     out_time_raw        uint16    工作区出点（原始值）
39      2     (保留)              —         —
41      2     out_time_div        uint16    出点除数
43      2     (保留)              —         —
45      2     duration_raw        uint16    时长（原始值）
47      2     (保留)              —         —
49      2     duration_div        uint16    时长除数
51      1     (保留)              —         —
52      1     bg_red              uint8     背景色 R 通道（0–255）
53      1     bg_green            uint8     背景色 G 通道（0–255）
54      1     bg_blue             uint8     背景色 B 通道（0–255）
55      85    (保留)              —         —
140     2     width               uint16    合成宽度（像素）
142     2     height              uint16    合成高度（像素）
144     12    (保留)              —         —
```

**时间计算公式：**

```
divisor = raw_divisor / 帧率
value   = raw_value / divisor
```

**特殊情况：** 当 `out_time_raw == 65535` 时，出点时间等于合成时长。

---

## 8. 图层数据 (ldta)

包含所有核心图层属性。

### 二进制布局

```
偏移量  大小  字段名              类型      说明
─────────────────────────────────────────────────────────
0       4     layer_id            uint32    唯一图层标识符
4       2     quality             uint16    渲染质量（1=草稿, 2=最佳）
6       2     (保留)              —         —
8       4     time_stretch_num    sint32    时间伸缩分子
12      4     start_time_num      sint32    图层起始时间分子
16      4     start_time_den      uint32    图层起始时间分母
20      4     in_time_num         sint32    入点分子
24      4     in_time_den         uint32    入点分母
28      4     out_time_num        sint32    出点分子
32      4     out_time_den        uint32    出点分母
36      4     flags               uint32    图层标志位（见下文）
40      4     asset_id            uint32    引用的源素材/合成 ID
44      17    (保留)              —         —
61      1     label_color         uint8     AE 标签颜色索引（0–16）
62      2     (保留)              —         —
64      32    (保留)              —         —
96      4     blend_mode          uint32    混合模式常量（见§20）
100     4     (保留)              —         —
104     4     matte_mode          uint32    轨道遮罩模式（见§20）
108     2     (保留)              —         —
110     2     time_stretch_den    uint16    时间伸缩分母
112     19    (保留)              —         —
131     1     layer_type          uint8     图层类型代码（见下文）
132     4     parent_id           uint32    父图层 ID（0 = 无父级）
136     24    (保留)              —         —
160     4     matte_id            uint32    轨道遮罩源图层 ID
```

### 图层类型代码

| 值 | 类型 |
|----|------|
| 0 | 素材（影片、纯色、预合成引用） |
| 1 | 灯光 |
| 2 | 摄像机 |
| 3 | 文字 |
| 4 | 形状 |

### 图层标志位（4 字节，位级别）

```
Byte[0]:
  bit 1  is_guide              引导图层
  bit 6  bicubic_sampling      使用双三次采样

Byte[1]:
  bit 0  auto_orient           沿路径自动定向
  bit 1  is_adjustment         调整图层
  bit 2  threedimensional      3D 图层
  bit 3  solo                  独奏开关
  bit 7  is_null               空对象图层

Byte[2]:
  bit 0  visible               图层可见性（眼睛图标）
  bit 2  effects_enabled       效果开关
  bit 3  motion_blur_enabled   运动模糊
  bit 5  locked                图层锁定
  bit 6  shy                   害羞图层
  bit 7  continuously_rasterize  塌陷变换 / 持续光栅化
```

### 时间值计算

```
start_time  = start_time_num  / start_time_den
in_time     = in_time_num     / in_time_den
out_time    = out_time_num    / out_time_den
time_stretch = time_stretch_num / time_stretch_den
```

### 图层名称解析

图层名称来自 `Layr` 列表中的 `Utf8` 数据块。如果名称为空（占位符 `"-_0_/-"`），
解析器会回退到 `asset_id` 引用的**源素材或合成名称**。

---

## 9. 属性系统

After Effects 将所有可动画化的属性存储在**属性组树**中。

### 属性组 (tdgp)

一个 `LIST tdgp` 数据块按顺序包含以下子块：

```
tdmn    → 标识此子项的 Match Name
tdsb    → 属性组自身的可见性/启用标志
tdsn    → 显示名称（内含 Utf8 的 LIST）
tdmn    → 第一个子属性的 Match Name
<child> → 属性数据（tdgp、tdbs、om-s、GCst 等）
tdmn    → 第二个子属性的 Match Name
<child> → 属性数据
...
```

每个 `tdmn` 数据块被序列中的**下一个**非元数据块所消耗。

### 属性可见性标志 (tdsb, 4 字节)

```
偏移量  大小  字段名      类型      说明
─────────────────────────────────────────────────
0       4     flags       uint32    位标志
```

```
Byte[3]:
  bit 0  visible     属性可见（split=true 时为"启用"状态）
  bit 1  split       表示这是图层样式子组
```

**解释：**
- `split=false`：`bit 0` → `visible` 字段（普通属性可见性）
- `split=true`：`bit 0` → `enabled` 字段（图层样式开/关切换）

### 属性类型

属性根据其代表的内容表现为不同的数据块类型：

| 数据块类型 | 结果对象 | 用途 |
|-----------|---------|------|
| `tdgp` | PropertyGroup（属性组） | 子属性容器 |
| `tdbs` | AnimatedProperty（动画属性） | 标准可动画化值 |
| `om-s` | AnimatedProperty（形状） | 贝塞尔路径数据 |
| `GCst` | AnimatedProperty（渐变） | 颜色渐变 |
| `otst` | AnimatedProperty（方向） | 3D 方向 |
| `mrst` | AnimatedProperty（标记） | 合成标记 |
| `btds` | TextProperty（文字属性） | 带样式的文字文档 |
| `sspc` | EffectInstance（效果实例） | 应用的效果及其参数 |

---

## 10. 动画属性 (tdbs)

`LIST tdbs` 包含动画属性的完整定义。

### 子块

```
tdsb    → 可见性标志
tdb4    → 属性类型元数据
cdat    → 静态值（非动画时）
list    → 关键帧列表（有动画时）
Utf8    → 表达式字符串（可选）
tdpi    → 图层引用目标（用于图层引用属性）
tdps    → 图层引用源（用于图层引用属性）
tdli    → 无符号整数引用（用于无符号整数引用属性）
```

### 属性元数据 (tdb4)

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       2     (保留)          —         —
2       2     components      uint16    值的分量数（1–4）
4       2     type_flags      uint16    空间标志（见下文）
6       7     (保留)          —         —
13      4     time_scale      uint32    关键帧时间除数
17      39    (保留)          —         —
56      4     prop_flags      uint32    属性类型指示器
60      8     (保留)          —         —
68      1     animated        uint8     1 = 有关键帧, 0 = 静态
```

**type_flags（偏移量 4）：**

```
Byte[1]:
  bit 3  is_spatial    属性有空间贝塞尔切线（位置、锚点）
```

**prop_flags（偏移量 56）：**

```
Byte[0]:
  bit 0  is_color      RGBA 颜色属性

Byte[2]:
  bit 0  is_bool       布尔/复选框属性
  bit 2  is_ref        图层或值引用
```

### 属性类型判定

按优先级排序（首个匹配即生效）：

| 条件 | prop_type | 名称 | 示例属性 |
|------|-----------|------|---------|
| `is_spatial` | 2 | 空间 | 位置、锚点 |
| `is_bool` | 0 | 颜色* | 不透明度、启用切换 |
| `is_color` | 1 | 标量 | 填充颜色、描边颜色 |
| `is_ref` + 存在 `tdpi` | 4 | 图层引用 | Set Matte 源 |
| `is_ref` + 存在 `tdli` | 6 | 无符号整数引用 | 下拉选择 |
| （默认） | 3 | 多维 | 缩放、旋转 |

*注：在原始 JS 代码中，prop_type 0 映射到布尔/简单类型，prop_type 1 映射到标量类型，
名称与实际含义的不一致是历史遗留问题。*

### 静态值 (cdat)

`cdat` 数据块存储属性的静态值，后跟切线/速度槽位。总大小取决于属性类型：

**非空间属性**（缩放、旋转、不透明度）：`components × 5` 个 float64

```
[值₁..值ₙ] [ease_in₁..ₙ] [ease_out₁..ₙ] [influence_in₁..ₙ] [influence_out₁..ₙ]
```

**空间属性**（位置、锚点）：`components × 3 + 3` 个 float64

```
[值₁..值ₙ] [空间入切线₁..ₙ] [空间出切线₁..ₙ] [时间缓动 × 3]
```

**cdat 大小示例：**

| 属性 | 分量数 | 空间 | float64 数量 | 字节大小 |
|------|--------|------|-------------|---------|
| 不透明度 | 1 | 否 | 1×5 = 5 | 40 |
| Z 旋转 | 1 | 否 | 1×5 = 5 | 40 |
| 位置 (2D) | 2 | 是 | 2×3+3 = 9 | 72 |
| 锚点 (2D) | 2 | 是 | 2×3+3 = 9 | 72 |
| 缩放 (3D) | 3 | 否 | 3×5 = 15 | 120 |

> **重要：** 修改 cdat 值时，只覆盖前 `components` 个 float64（实际值）。剩余的切线/速度数据必须保留，否则会损坏项目文件。

**按 prop_type 解释值：**

| prop_type | 布局 | 说明 |
|-----------|------|------|
| 0（颜色） | `[alpha, R, G, B]` | R/G/B 范围 0–255，alpha 范围 0–1 |
| 1（标量） | 不在 cdat 中 | 值来自 `extra_values` 列表 |
| 2（空间） | `[x, y]` 或 `[x, y, z]` | 位置坐标 |
| 3（多维） | `[v₁, v₂, …]` | 缩放、旋转等 |
| 4（图层引用） | 不在 cdat 中 | 见 tdpi/tdps 数据块 |
| 6（无符号整数） | 不在 cdat 中 | 见 tdli 数据块 |

> **注意：** AE 内部以 0–1 分数存储缩放和不透明度（1.0 = 100%）。AE 界面显示为百分比。

### 属性边界 (tdum / tduM)

`tdum` 和 `tduM` 数据块定义属性的最小和最大允许值。每个包含一个 float64。

```
tdum: 8 字节 → float64 最小值
tduM: 8 字节 → float64 最大值
```

这些数据块在真实 AEP 文件中**始终存在**，即使两个值都为 0.0。例如，不透明度的 tdum=0.0、tduM=100.0。

---

## 11. 关键帧格式

### 关键帧列表容器 (list)

包含 `lhd3`（头部）和 `ldat`（数据）。

**列表头 (lhd3)：**

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       10    (保留)          —         —
10      2     count           uint16    关键帧数量
12      6     (保留)          —         —
18      2     item_size       uint16    每个关键帧记录的字节数
```

**列表数据 (ldat)：** `count × item_size` 字节，分为固定大小的记录。

### 关键帧记录 — 公共头（8 字节）

所有关键帧类型共享此前缀：

```
偏移量  大小  字段名              类型      说明
─────────────────────────────────────────────────────────
0       1     (保留)              —         —
1       4     time_raw            sint32    关键帧时间（除以 time_scale 得到秒）
5       1     transition_type     uint8     插值类型
6       1     label_color         uint8     标签颜色索引
7       1     flags               uint8     贝塞尔模式标志
```

**插值类型：**

| 值 | 名称 | 说明 |
|----|------|------|
| 1 | Linear | 线性插值 |
| 2 | Bezier | 贝塞尔曲线插值 |
| 3 | Hold | 定格/保持（无插值） |

**标志位字节（偏移量 7）：**

```
bit 3  continuous_bezier    连续贝塞尔手柄
bit 4  auto_bezier          自动贝塞尔模式
bit 5  roving               游离关键帧（平滑运动）
```

贝塞尔模式：`continuous_bezier` → 模式 1，`auto_bezier` → 模式 2，均无 → 模式 0。

### 关键帧记录 — 类型特定数据

**空间类型 (prop_type=2) — 位置/锚点：**

```
偏移量  大小             字段名          说明
───────────────────────────────────────────────────────
8       16               (保留)          —
24      8                in_speed        float64 入速度
32      8                in_influence    float64 入影响
40      8                out_speed       float64 出速度
48      8                out_influence   float64 出影响
56      C×8              value           [x, y, z] 坐标
56+C×8  C×8              in_tangent      贝塞尔入切线 [x, y, z]
56+C×16 C×8              out_tangent     贝塞尔出切线 [x, y, z]
```

*（C = 分量数量）*

**标量类型 (prop_type=1) — 不透明度、旋转等：**

```
偏移量  大小  字段名          说明
──────────────────────────────────────────
8       16    (保留)          —
24      8     in_speed        float64 入速度
32      8     in_influence    float64 入影响
40      8     out_speed       float64 出速度
48      8     out_influence   float64 出影响
```

值来自 `extra_values[index]`，而非关键帧数据本身。

**多维类型 (prop_type=3,5) — 缩放等：**

```
偏移量  大小    字段名          说明
─────────────────────────────────────────────
8       C×8     value           [v₁, v₂, …] float64 数组
8+C×8   C×8     in_speed        每个分量的 float64 入速度
8+C×16  C×8     in_influence    每个分量的 float64 入影响
8+C×24  C×8     out_speed       每个分量的 float64 出速度
8+C×32  C×8     out_influence   每个分量的 float64 出影响
```

**颜色类型 (prop_type=0)：**

```
偏移量  大小  字段名          说明
──────────────────────────────────────────
8       16    (保留)          —
24      8     in_speed        float64 入速度
32      8     in_influence    float64 入影响
40      8     out_speed       float64 出速度
48      8     out_influence   float64 出影响
56      C×8   value           [alpha, R, G, B] — R/G/B 范围 0–255
```

### 短关键帧（标记）

标记关键帧的 `item_size` 可能小至 16 字节，仅包含公共头（8 字节）+ 8 字节基本数据。
解析器在尝试读取速度/影响值之前会检查 `reader.remaining()`。

### 速度值处理

速度字段中的 `NaN` float64 值会被替换为 `0.0`。

---

## 12. 素材数据

素材存储在 `item_type=7` 的 `LIST Item` 下，包含一个 `LIST Pin`。

### 源参数（Pin 中的 sspc）

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       32    (保留)          —         —
32      2     width           uint16    素材宽度（像素）
34      2     (保留)          —         —
36      2     height          uint16    素材高度（像素）
38      2     (保留)          —         —
40      2     seq_count       uint16    序列帧数量
42      132   (保留)          —         —
174     2     seq_start       uint16    序列起始帧
176     2     (保留)          —         —
178     2     seq_end         uint16    序列结束帧
180     2     (保留)          —         —
182     2     seq_max_len     uint16    帧名称最大数字位数
```

### 素材选项 (opti)

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       4     type_code       char[4]   素材类型标识符
4       2     (保留)          —         —
6       4     (保留)          —         —
```

**当 type_code == `"Soli"`（纯色）时：**

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
10      4     alpha           float32   透明度（0.0–1.0）
14      4     red             float32   红色分量
18      4     green           float32   绿色分量
22      4     blue            float32   蓝色分量
26      256   name            char[256] 以 null 结尾的纯色名称（UTF-8）
```

颜色分量编码：值 `== 255` → 直接使用，否则 `value × 255`。

**当 type_code != `"Soli"`（文件引用）时：**

文件路径存储在 `LIST Als2 → alas` 中，以 JSON 字符串形式：

```json
{
  "fullpath": "C:\\Users\\...\\image.png",
  "target_is_folder": false
}
```

当 `target_is_folder` 为 `true` 时，素材是**图片序列**，sspc 中的
`seq_count`、`seq_start`、`seq_end`、`seq_max_len` 字段有效。

---

## 13. 效果定义

全局效果模板存储在 `LIST EfdG` 中。

### 每个效果的结构 (LIST EfDf)

```
tdmn              → 效果 Match Name（如 "ADBE Gaussian Blur 2"）
LIST sspc         → 效果模板
  LIST fnam       → 显示名称
    Utf8          → "Gaussian Blur"
  LIST parT       → 参数定义
    tdmn          → 参数 1 的 Match Name
    <param_data>  → 参数 1 的二进制元数据
    pdnm          → 参数 1 的显示名称（可选）
    tdmn          → 参数 2 的 Match Name
    <param_data>  → 参数 2 的二进制元数据
    ...
```

### 参数二进制元数据

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       14    (保留)          —         —
14      2     param_type      uint16    参数类型代码
16      32    name            char[32]  以 null 结尾的参数名称（UTF-8）
48      8     (可变)          —         默认/最近值（取决于类型）
```

### 参数类型代码

| 代码 | 类型 | 值格式 |
|------|------|--------|
| 0 | 图层引用 | LayerRef 对象 |
| 2 | 角度 | `sint32 / 65536`（弧度，定点数） |
| 3 | 百分比 | `sint32 / 65536`（定点数） |
| 4 | 下拉菜单 | `uint32`（选中索引）+ `uint8`（默认值） |
| 5 | 颜色（RGB） | `[alpha/255, R, G, B]` 以 uint8 表示 |
| 6 | 2D 点 | `[sint32/128, sint32/128]`（定点数） |
| 7 | 弹出菜单 | `uint32`（选中值）+ skip(2) + `uint16`（默认值） |
| 10 | 浮点数 | `float64` |
| 18 | 3D 颜色 | `[float64×512, float64×512, float64×512]` |

### 效果实例（属性树中的 sspc）

当效果被应用到图层时，它以 `LIST sspc` 的形式出现在属性树中
`"ADBE Effect Parade"` 下。包含 `fnam`（实例名称）和 `tdgp`（参数值）。

---

## 14. 遮罩数据 (mkif)

遮罩元数据块，存在于 `"ADBE Mask Parade"` 下的属性组中。

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       1     inverted        uint8     1 = 遮罩反转
1       1     locked          uint8     1 = 遮罩锁定
2       4     (保留)          —         —
6       2     mode            uint16    遮罩操作模式
8       3     (保留)          —         —
11      1     index           uint8     遮罩顺序索引
```

**遮罩模式：**

| 值 | 模式 |
|----|------|
| 0 | 无 |
| 1 | 相加 |
| 2 | 相减 |
| 3 | 相交 |
| 4 | 变暗 |
| 5 | 变亮 |
| 6 | 差值 |

`mkif` 数据块之后是一个属性组（`tdgp`），包含遮罩的形状、羽化、不透明度和扩展属性。

---

## 15. 贝塞尔形状 (shph)

用于矢量遮罩和形状图层的路径数据。

### 形状头 (shph)

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       3     (保留)          —         —
3       1     flags           uint8     形状标志
4       4     min_x           float32   边界框左边
8       4     min_y           float32   边界框上边
12      4     max_x           float32   边界框右边
16      4     max_y           float32   边界框下边
```

**标志位字节：**

```
bit 3  open_path    0 = 闭合路径，1 = 开放路径
```

注：`closed` 属性是 bit 3 的**取反值**：`closed = !flags.bit(0, 3)`。

### 形状点

存储在 `list` 数据块中（与关键帧列表格式相同）。每个点记录：

```
偏移量  大小  字段名  类型      说明
──────────────────────────────────────────
0       4     x       float32   X 坐标
4       4     y       float32   Y 坐标
```

坐标为 `NaN` 的点会被跳过。

点以**三元组**形式组织：`[入切线, 顶点, 出切线]`。
总顶点数 = `len(points) / 3`。

### 动画形状属性

动画形状使用 `LIST om-s`：

```
LIST om-s
  LIST omks          ← 形状关键帧集合
    LIST shap        ← 关键帧 0 的形状
      shph           ← 形状头
      list           ← 形状点
    LIST shap        ← 关键帧 1 的形状
    ...
  LIST tdbs          ← 动画时间（标量关键帧）
```

每个形状附带组信息：`maxVertexCount`（所有关键帧中的最大顶点数）
和 `bezierCount`（形状关键帧总数）。

---

## 16. 渐变数据 (GCst)

动画渐变属性。

### 结构

```
LIST GCst
  LIST GCky          ← 渐变关键帧集合
    Utf8             ← 渐变 0 的 XML 字符串
    Utf8             ← 渐变 1 的 XML 字符串
    ...
  LIST tdbs          ← 动画时间
```

### 渐变 XML 格式

每个关键帧的渐变以 After Effects 属性 XML 格式的字符串存储：

```xml
<prop.map>
  <prop.list>
    <prop.pair>
      <key>Gradient Color Data</key>
      <prop.list>
        <prop.pair>
          <key>Color Stops</key>
          <prop.list>
            <prop.pair>
              <key>Stops List</key>
              <prop.list>
                <prop.pair>
                  <key>0</key>
                  <prop.list>
                    <prop.pair>
                      <key>Stops Color</key>
                      <array>
                        <array.type><float/></array.type>
                        <float>0.0</float>      <!-- 位置 (0-1) -->
                        <float>0.5</float>      <!-- 中间点 (0-1) -->
                        <float>1.0</float>      <!-- R (0-1) -->
                        <float>0.0</float>      <!-- G (0-1) -->
                        <float>0.0</float>      <!-- B (0-1) -->
                        <float>1.0</float>      <!-- alpha (0-1) -->
                      </array>
                    </prop.pair>
                  </prop.list>
                </prop.pair>
                ...
              </prop.list>
            </prop.pair>
          </prop.list>
        </prop.pair>
        <prop.pair>
          <key>Alpha Stops</key>
          <prop.list>
            <prop.pair>
              <key>Stops List</key>
              <prop.list>
                <prop.pair>
                  <key>0</key>
                  <prop.list>
                    <prop.pair>
                      <key>Stops Alpha</key>
                      <array>
                        <array.type><float/></array.type>
                        <float>0.0</float>      <!-- 位置 -->
                        <float>0.5</float>      <!-- 中间点 -->
                        <float>1.0</float>      <!-- 透明度值 -->
                      </array>
                    </prop.pair>
                  </prop.list>
                </prop.pair>
              </prop.list>
            </prop.pair>
          </prop.list>
        </prop.pair>
      </prop.list>
    </prop.pair>
  </prop.list>
</prop.map>
```

---

## 17. 文字数据 (btdk / COS 格式)

文字文档使用 **COS**（Carousel Object System）二进制格式，
一种类似 PDF 的标记流。

### COS 标记类型

| 语法 | 类型 | 示例 |
|------|------|------|
| `123`, `3.14` | 数字 | 整数或浮点数 |
| `(Hello World)` | 字符串 | 转义括号字符串 |
| `<48656C6C6F>` | 十六进制字符串 | 十六进制编码字节 |
| `/key` | 名称 | 字典键 |
| `true`, `false` | 布尔值 | — |
| `null` | 空值 | — |
| `<< ... >>` | 字典 | 键值对 |
| `[ ... ]` | 数组 | 有序列表 |
| `% ...` | 注释 | 到行尾 |

### 字符串转义序列

| 序列 | 含义 |
|------|------|
| `\\` | 反斜杠 |
| `\(` | 左括号 |
| `\)` | 右括号 |
| `\n` | 换行符 |
| `\r` | 回车符 |
| `\t` | 制表符 |
| `\NNN` | 八进制字符代码 |

字符串中的嵌套括号通过深度计数器跟踪。

### 文字文档结构

解析后的 COS 对象具有以下层级（使用整数字符串键）：

```
根字典
├── "0": 字体和元数据
│   └── "1"
│       └── "0": 字体条目数组
│           └── [i]
│               └── "0"
│                   └── "0"
│                       └── "0": 字体族名称（字符串）
│
└── "1": 文字文档
    └── "1": 文档条目数组
        └── [i]: 单个文字文档
            ├── "0"
            │   ├── "0": 文字内容（字符串）
            │   ├── "5"
            │   │   └── "0": 行样式数组
            │   │       └── [j]
            │   │           ├── "0"
            │   │           │   └── "0"
            │   │           │       └── "5": 对齐数据
            │   │           │           └── [0]: 文字对齐模式
            │   │           └── "1": 字符数量
            │   └── "6"
            │       └── "0": 字符样式数组
            │           └── [j]
            │               ├── "0"
            │               │   └── "0"
            │               │       └── "6": 样式数据
            │               │           ├── [0]:  字体索引
            │               │           ├── [1]:  字体大小
            │               │           ├── [2]:  仿粗体（布尔）
            │               │           ├── [3]:  仿斜体（布尔）
            │               │           ├── [4]:  自动行间距（布尔）
            │               │           ├── [5]:  行间距
            │               │           ├── [8]:  字间距
            │               │           ├── [12]: 文字变换
            │               │           ├── [13]: 垂直对齐
            │               │           ├── [53]: 填充颜色 [a, r, g, b]
            │               │           ├── [54]: 描边颜色 [a, r, g, b]
            │               │           ├── [56]: 填充启用（布尔）
            │               │           ├── [57]: 描边启用（布尔）
            │               │           ├── [58]: 描边在填充上方（布尔）
            │               │           └── [63]: 描边宽度
            │               └── "1": 字符数量
            └── "1"
                └── "2": 段落样式数组
                    └── [j]
                        └── "6": 段落矩形数组
                            └── [k]
                                ├── "0"
                                │   └── "0": 位置 [x, y]
                                └── "1": 大小 [?, ?, width, height]
```

### 动画文字属性 (btds)

```
LIST btds
  btdk             ← COS 二进制数据（字体 + 文档样式）
  LIST tdbs        ← 文字值的动画关键帧
```

---

## 18. 标记数据 (Nmrd)

合成标记（章节点、提示标记）。

### 命名记录 (Nmrd)

```
LIST Nmrd
  NmHd             ← 标记头
  Utf8             ← 标记名称（可选）
```

### 标记头 (NmHd)

```
偏移量  大小  字段名          类型      说明
─────────────────────────────────────────────────────
0       3     (保留)          —         —
3       1     flags           uint8     标记标志
4       4     (保留)          —         —
8       4     duration_num    uint32    时长分子
12      4     duration_den    uint32    时长分母
16      1     label_color     uint8     标签颜色索引
```

**标志位：**

```
bit 1  is_protected    标记被保护/锁定
```

**时长：** `duration = duration_num / duration_den`（瞬时标记为 0）。

### 动画标记 (mrst)

```
LIST mrst
  LIST mrky        ← 标记数据集合
    LIST Nmrd      ← 标记 0
    LIST Nmrd      ← 标记 1
    ...
  LIST tdbs        ← 时间（关键帧时间 = 标记位置）
```

---

## 19. 图层样式

图层样式（投影、内发光、斜面、描边等）有特殊处理逻辑。

### 结构

```
ADBE Layer Styles (tdgp)
├── tdsb                        ← 根标志（split=true, visible=true — 不可靠！）
├── ADBE Blend Options Group    ← 始终存在，始终"启用"
├── dropShadow/enabled          ← 投影开关 + 属性
├── innerShadow/enabled         ← 内阴影开关 + 属性
├── outerGlow/enabled           ← 外发光开关 + 属性
├── innerGlow/enabled           ← 内发光开关 + 属性
├── bevelEmboss/enabled         ← 斜面和浮雕开关 + 属性
├── chromeFX/enabled            ← 光泽开关 + 属性
├── solidFill/enabled           ← 颜色叠加开关 + 属性
├── gradientFill/enabled        ← 渐变叠加开关 + 属性
├── patternFill/enabled         ← 图案叠加开关 + 属性
└── frameFX/enabled             ← 描边开关 + 属性
```

### 启用状态检测

`ADBE Layer Styles` 的根 `tdsb` 标志**始终**为 `0x00000003`
（`split=true, visible=true`），无论是否有任何样式实际启用。此标志**不可靠**。

**正确逻辑：**

1. 对于每个 `*/enabled` 子组：
   - 如果 tdsb 中 `split=true`：使用 `bit(3,0)` 作为启用状态
   - 如果 tdsb 中 `split=false`：根据组是否包含子属性推断启用状态
     （有属性 → 启用，空 → 禁用）
2. 根启用状态 = `any(子样式.enabled for 子样式 in */enabled 组)`

### 子样式 Match Name

图层样式使用**非 ADBE** 的 Match Name 作为子组标识：

| Match Name | AE 图层样式 |
|-----------|-------------|
| `dropShadow/enabled` | 投影 |
| `innerShadow/enabled` | 内阴影 |
| `outerGlow/enabled` | 外发光 |
| `innerGlow/enabled` | 内发光 |
| `bevelEmboss/enabled` | 斜面和浮雕 |
| `chromeFX/enabled` | 光泽 |
| `solidFill/enabled` | 颜色叠加 |
| `gradientFill/enabled` | 渐变叠加 |
| `patternFill/enabled` | 图案叠加 |
| `frameFX/enabled` | 描边 |

每个子样式内部的属性 Match Name 使用相同前缀：

```
innerShadow/color       ← 颜色
innerShadow/opacity     ← 不透明度
innerShadow/distance    ← 距离
innerShadow/blur        ← 模糊
```

---

## 20. AEPX XML 格式

AEPX 文件将相同的数据块树编码为 XML。

### 根元素

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AfterEffectsProject ...>
  <!-- 子元素代表数据块 -->
</AfterEffectsProject>
```

### 数据块 → XML 映射

| AEP（二进制） | AEPX（XML） |
|--------------|------------|
| 数据块头标识 | 元素标签名 |
| LIST 数据块 | 带子元素的元素 |
| 二进制数据 | `bdata="hex..."` 属性 |
| Utf8 字符串 | `<string>文字</string>` 子元素 |
| 文件引用 | `<fileReference>` 子元素 |

### 示例

二进制：
```
LIST Fold
  LIST Item
    idta [二进制数据]
    Utf8 "My Comp"
```

XML：
```xml
<Fold>
  <Item>
    <idta bdata="0004000000000000000000000000000000000001"/>
    <Utf8>
      <string>My Comp</string>
    </Utf8>
  </Item>
</Fold>
```

### 字节序

AEPX 文件包含 `byteOrder` 属性或可从 XML 内容中检测。
解析器默认对 `bdata` 属性中的二进制数据使用大端序。

---

## 21. 常量与枚举

### 混合模式

| 值 | 模式 | 值 | 模式 |
|----|------|-----|------|
| 2 | 正常 (Normal) | 21 | 发光预乘 (Luminescent Premul) |
| 3 | 溶解 (Dissolve) | 22 | Alpha 添加 (Alpha Add) |
| 4 | 添加 (Add) | 23 | 经典颜色减淡 (Classic Color Dodge) |
| 5 | 正片叠底 (Multiply) | 24 | 经典颜色加深 (Classic Color Burn) |
| 6 | 滤色 (Screen) | 25 | 排除 (Exclusion) |
| 7 | 叠加 (Overlay) | 26 | 差值 (Difference) |
| 8 | 柔光 (Soft Light) | 27 | 颜色减淡 (Color Dodge) |
| 9 | 强光 (Hard Light) | 28 | 颜色加深 (Color Burn) |
| 10 | 变暗 (Darken) | 29 | 线性减淡/添加 (Linear Dodge) |
| 11 | 变亮 (Lighten) | 30 | 线性加深 (Linear Burn) |
| 12 | 经典差值 (Classic Difference) | 31 | 线性光 (Linear Light) |
| 13 | 色相 (Hue) | 32 | 亮光 (Vivid Light) |
| 14 | 饱和度 (Saturation) | 33 | 点光 (Pin Light) |
| 15 | 颜色 (Color) | 34 | 实色混合 (Hard Mix) |
| 16 | 明度 (Luminosity) | 35 | 浅色 (Lighter Color) |
| 17 | 蒙版 Alpha (Stencil Alpha) | 36 | 深色 (Darker Color) |
| 18 | 蒙版亮度 (Stencil Luma) | 37 | 相减 (Subtract) |
| 19 | 轮廓 Alpha (Silhouette Alpha) | 38 | 相除 (Divide) |
| 20 | 轮廓亮度 (Silhouette Luma) | | |

### 轨道遮罩模式

| 值 | 模式 |
|----|------|
| 0 | 无 |
| 1 | Alpha 遮罩 |
| 2 | Alpha 反转遮罩 |
| 3 | 亮度遮罩 |
| 4 | 亮度反转遮罩 |

### 图层类型

| 值 | 类型 |
|----|------|
| 0 | 素材（影片/纯色/预合成） |
| 1 | 灯光 |
| 2 | 摄像机 |
| 3 | 文字 |
| 4 | 形状 |

### 插值类型（关键帧插值）

| 值 | 类型 |
|----|------|
| 1 | 线性 (Linear) |
| 2 | 贝塞尔 (Bezier) |
| 3 | 定格 (Hold) |

### 贝塞尔模式

| 值 | 模式 |
|----|------|
| 0 | 普通 (Normal) |
| 1 | 连续 (Continuous) |
| 2 | 自动 (Auto) |

### 遮罩模式

| 值 | 模式 |
|----|------|
| 0 | 无 (None) |
| 1 | 相加 (Add) |
| 2 | 相减 (Subtract) |
| 3 | 相交 (Intersect) |
| 4 | 变暗 (Darken) |
| 5 | 变亮 (Lighten) |
| 6 | 差值 (Difference) |

---

## 22. Match Name 参考表

Match Name（`tdmn` 数据块）用于标识标准的 After Effects 属性。
解析器将这些名称映射为人类可读的显示名称。

### 变换

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Transform Group` | 变换 (Transform) |
| `ADBE Anchor Point` | 锚点 (Anchor Point) |
| `ADBE Position` | 位置 (Position) |
| `ADBE Position_0` | X 位置 |
| `ADBE Position_1` | Y 位置 |
| `ADBE Position_2` | Z 位置 |
| `ADBE Scale` | 缩放 (Scale) |
| `ADBE Rotate X` | X 旋转 |
| `ADBE Rotate Y` | Y 旋转 |
| `ADBE Rotate Z` | Z 旋转 |
| `ADBE Rotation` | 旋转 (Rotation) |
| `ADBE Opacity` | 不透明度 (Opacity) |
| `ADBE Orientation` | 方向 (Orientation) |
| `ADBE Skew` | 倾斜 (Skew) |
| `ADBE Skew Axis` | 倾斜轴 (Skew Axis) |

### 形状图层

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Root Vectors Group` | 内容 (Contents) |
| `ADBE Vector Group` | 组 (Group) |
| `ADBE Vectors Group` | 内容 (Contents) |
| `ADBE Vector Transform Group` | 变换 (Transform) |
| `ADBE Vector Shape - Rect` | 矩形 (Rectangle) |
| `ADBE Vector Rect Position` | 位置 (Position) |
| `ADBE Vector Rect Size` | 大小 (Size) |
| `ADBE Vector Rect Roundness` | 圆度 (Roundness) |
| `ADBE Vector Shape - Ellipse` | 椭圆 (Ellipse) |
| `ADBE Vector Ellipse Position` | 位置 (Position) |
| `ADBE Vector Ellipse Size` | 大小 (Size) |
| `ADBE Vector Shape - Star` | 多边星形 (Polystar) |
| `ADBE Vector Shape - Group` | 路径 (Path) |
| `ADBE Vector Shape` | 路径 (Path) |
| `ADBE Vector Graphic - Fill` | 填充 (Fill) |
| `ADBE Vector Fill Color` | 颜色 (Color) |
| `ADBE Vector Fill Opacity` | 不透明度 (Opacity) |
| `ADBE Vector Fill Rule` | 填充规则 (Fill Rule) |
| `ADBE Vector Graphic - Stroke` | 描边 (Stroke) |
| `ADBE Vector Stroke Color` | 颜色 (Color) |
| `ADBE Vector Stroke Opacity` | 不透明度 (Opacity) |
| `ADBE Vector Stroke Width` | 描边宽度 (Stroke Width) |
| `ADBE Vector Stroke Line Cap` | 线段端点 (Line Cap) |
| `ADBE Vector Stroke Line Join` | 线段连接 (Line Join) |
| `ADBE Vector Stroke Miter Limit` | 尖角限制 (Miter Limit) |
| `ADBE Vector Stroke Dashes` | 虚线 (Dashes) |
| `ADBE Vector Graphic - G-Fill` | 渐变填充 (Gradient Fill) |
| `ADBE Vector Graphic - G-Stroke` | 渐变描边 (Gradient Stroke) |
| `ADBE Vector Grad Start Pt` | 起始点 (Start Point) |
| `ADBE Vector Grad End Pt` | 结束点 (End Point) |
| `ADBE Vector Grad Colors` | 颜色 (Colors) |
| `ADBE Vector Grad Type` | 类型 (Type) |
| `ADBE Vector Filter - Trim` | 修剪路径 (Trim Paths) |
| `ADBE Vector Trim Start` | 开始 (Start) |
| `ADBE Vector Trim End` | 结束 (End) |
| `ADBE Vector Trim Offset` | 偏移 (Offset) |
| `ADBE Vector Filter - Merge` | 合并路径 (Merge Paths) |
| `ADBE Vector Filter - Offset` | 偏移路径 (Offset Paths) |
| `ADBE Vector Filter - PB` | 收缩和膨胀 (Pucker & Bloat) |
| `ADBE Vector Filter - Repeater` | 中继器 (Repeater) |
| `ADBE Vector Repeater Copies` | 副本 (Copies) |
| `ADBE Vector Repeater Offset` | 偏移 (Offset) |
| `ADBE Vector Repeater Transform` | 变换 (Transform) |
| `ADBE Vector Filter - RC` | 圆角 (Round Corners) |
| `ADBE Vector RoundCorner Radius` | 半径 (Radius) |
| `ADBE Vector Filter - Twist` | 扭曲 (Twist) |
| `ADBE Vector Filter - Zigzag` | 锯齿 (Zig Zag) |
| `ADBE Vector Blend Mode` | 混合模式 (Blend Mode) |
| `ADBE Vector Group Opacity` | 不透明度 (Opacity) |

### 效果与遮罩

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Effect Parade` | 效果 (Effects) |
| `ADBE Mask Parade` | 遮罩 (Masks) |
| `ADBE Mask Atom` | 遮罩 (Mask) |
| `ADBE Mask Shape` | 遮罩路径 (Mask Path) |
| `ADBE Mask Feather` | 遮罩羽化 (Mask Feather) |
| `ADBE Mask Opacity` | 遮罩不透明度 (Mask Opacity) |
| `ADBE Mask Offset` | 遮罩扩展 (Mask Expansion) |

### 文字

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Text Properties` | 文字 (Text) |
| `ADBE Text Document` | 源文本 (Source Text) |
| `ADBE Text Animators` | 动画制作工具 (Animators) |
| `ADBE Text Animator` | 动画制作工具 (Animator) |
| `ADBE Text Selectors` | 选择器 (Selectors) |
| `ADBE Text Selector` | 范围选择器 (Range Selector) |
| `ADBE Text Percent Start` | 开始 (Start) |
| `ADBE Text Percent End` | 结束 (End) |
| `ADBE Text Animator Properties` | 属性 (Properties) |
| `ADBE Text Path Options` | 路径选项 (Path Options) |
| `ADBE Text More Options` | 更多选项 (More Options) |

### 其他

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Time Remapping` | 时间重映射 (Time Remap) |
| `ADBE Layer Styles` | 图层样式 (Layer Styles) |
| `ADBE Marker` | 标记 (Markers) |
| `ADBE Camera Options Group` | 摄像机选项 (Camera Options) |
| `ADBE Camera Aperture` | 光圈 (Aperture) |
| `ADBE Camera Zoom` | 缩放 (Zoom) |

### 常用效果

| Match Name | 显示名称 |
|-----------|---------|
| `ADBE Gaussian Blur 2` | 高斯模糊 (Gaussian Blur) |
| `ADBE Drop Shadow` | 投影 (Drop Shadow) |
| `ADBE Fill` | 填充 (Fill) |
| `ADBE Stroke` | 描边 (Stroke) |
| `ADBE Tint` | 色调 (Tint) |
| `ADBE Tritone` | 三色调 (Tritone) |
| `ADBE Pro Levels2` | 色阶 (Levels) |
| `ADBE Displacement Map` | 置换贴图 (Displacement Map) |
| `ADBE Set Matte3` | 设置遮罩 (Set Matte) |
| `ADBE Twirl` | 旋转扭曲 (Twirl) |
| `ADBE Spherize` | 球面化 (Spherize) |
| `ADBE Radial Wipe` | 径向擦除 (Radial Wipe) |

---

## 23. 写回 / RIFF 序列化

本节描述如何将修改后的数据块树序列化为有效的 `.aep` 二进制文件。

### 概述

写回过程在内存中的数据块树上操作：通过修改单个数据块的数据来改变值，然后重新序列化整棵树。**数据块大小在序列化时重新计算** — 不信任容器数据块的原始 `chunk.length`。

### 按数据块类型序列化

#### 根数据块 (RIFX/RIFF)

```
[magic 4B] [size 4B] [file_type 4B "Egg!"] [子块...]
```

- `magic`：保留解析时的值（`"RIFX"` 或 `"RIFF"`）
- `size`：**重新计算** = `4 (file_type) + 全部子块字节数`
- 先写占位符 `0x00000000`，待所有子块写入后回填

#### LIST 数据块

```
"LIST" [size 4B] [list_type 4B] [子块...]
```

- `size`：**重新计算** = `4 (list_type) + 全部子块字节数`
- 同根数据块使用占位符后回填

#### 非 LIST 容器数据块 (tdsn, fnam, pdnm)

```
[header 4B] [size 4B] [子块...]
```

- 这类数据块的 `ChunkList.type` 为空字符串 — **不写入类型前缀**（与 LIST 不同，LIST 会写入 4 字节类型）
- `size`：根据子块重新计算

#### 字符串数据块 (Utf8, alas, tdmn, wsnm)

```
[header 4B] [size 4B] [编码字节...]
```

- `Utf8` / `alas`：UTF-8 编码
- `wsnm`：UTF-16-LE 编码
- `tdmn`：UTF-8 + 空终止符，**填充至原始 `chunk.length`**（通常 32 字节）。这保留了 AE 期望的固定大小对齐。
- `size`：编码后的字节长度（tdmn 包含填充）

#### 原始二进制数据块 (idta, cdta, ldta, tdb4 等)

```
[header 4B] [size 4B] [data...]
```

- `size`：`len(data)` — 使用 `chunk.data` 的当前字节长度
- 数据原样写入

#### 特殊情况：btdk（文字数据）

解析器将 `btdk` 存储为 `header="btdk"`、`data=bytes`，但在二进制格式中 btdk 实际上是一个 LIST 子类型：

```
"LIST" [size 4B] "btdk" [data...]
```

- `size`：`4 (类型 "btdk") + len(data)`
- 序列化器检测到 `header == "btdk"` 时自动包装为 LIST 信封

### 2 字节对齐

所有数据块按 2 字节边界对齐。如果数据块的数据大小为奇数，在数据之后追加 **1 个填充字节** (`0x00`)。此填充字节**不**包含在数据块的 `size` 字段中。

```
[header 4B] [size 4B] [data (size 字节)] [0x00（若 size 为奇数）]
```

### 大小重算公式

对于容器数据块（根、LIST、非 LIST 容器），子块字节总量为：

```
child_bytes = sum(
    8 + child.data_size + (child.data_size % 2)    # header(4) + size(4) + data + 填充
    for child in children
)
```

容器的 `size` 字段：
- **LIST**：`4 (list_type) + child_bytes`
- **非 LIST 容器** (tdsn, fnam, pdnm)：`child_bytes`（无类型前缀）
- **根** (RIFX/RIFF)：`4 (file_type) + child_bytes`

### XMP 尾部数据

AEP 文件可能在 RIFF 容器边界之后（偏移量 `8 + file_size`）附加 XMP 元数据。此数据不属于数据块树。

保存时保留尾部数据的方式：
1. 加载时：将 `8 + file_size` 之后的所有字节存储为 `trailing_data`
2. 保存时：`write(序列化数据块 + trailing_data)`

### 修改图层名称

1. 导航至 `Fold → Item (comp_id) → Layr (layer_id)`
2. 在 `Layr` LIST 中找到 `Utf8` 数据块
3. 将 `chunk.data` 替换为新名称字符串
4. 如果不存在 `Utf8`，创建一个并插入到 `ldta` 之后
5. 序列化时数据块大小自动重算

### 修改属性值（cdat 原位修补）

1. 导航至 `Layr → tdgp → [match_name_path] → tdbs → cdat`
2. 读取前 `components` 个 float64 值（实际属性值）
3. 仅覆盖这些字节，**保留剩余的切线/速度数据**

```
cdat 布局（非空间属性，如不透明度）：
[值 × N] [ease_in × N] [ease_out × N] [influence_in × N] [influence_out × N]
 ↑ 修补    ↑ 保留...

cdat 布局（空间属性，如位置）：
[值 × N] [空间入切线 × N] [空间出切线 × N] [时间缓动 × 3]
 ↑ 修补    ↑ 保留...
```

`cdat.data` 的大小**不会改变** — 仅覆盖开头的值部分。

### 创建缺失的属性数据块

当 Transform 属性（锚点、位置、缩放、旋转、不透明度）在二进制中没有对应数据块（AE 省略未修改的默认值）时，从模板创建新的 `tdbs` 子树：

```
LIST tdbs
├── tdsb    4B    标志 = 0x00000001（可见）
├── tdsn    LIST  显示名称占位符 "-_0_/-"
├── tdb4    124B  属性类型元数据（来自模板）
├── cdat    可变   值 + 零切线
├── tdum    8B    float64 最小边界值
└── tduM    8B    float64 最大边界值
```

**模板 tdb4 按 Match Name 选择：**

| Match Name | 分量数 | 空间 | cdat float64 数量 |
|---|---|---|---|
| `ADBE Opacity` | 1 | 否 | 1×5 = 5（40 字节） |
| `ADBE Rotate Z` | 1 | 否 | 1×5 = 5（40 字节） |
| `ADBE Scale` | 3 | 否 | 3×5 = 15（120 字节） |
| `ADBE Anchor Point` | 2 | 是 | 2×3+3 = 9（72 字节） |
| `ADBE Position` | 2 | 是 | 2×3+3 = 9（72 字节） |

**插入位置**：新的 `tdmn` + `LIST tdbs` 对插入到父 `tdgp` 中 `"ADBE Group End"` tdmn 哨兵之前。

**tdmn 填充**：新建的 tdmn 数据块以空字符终止并用 `0x00` 填充至 32 字节。

### 修改关键帧值（ldat 原位修补）

1. 导航至 `tdbs → list → lhd3 + ldat`
2. 从 `lhd3` 读取 `count` 和 `item_size`（偏移量 10 和 18）
3. 计算每个关键帧记录中值的偏移量：
   - 公共头：8 字节 `[1B 跳过][4B 时间][1B 插值][1B 标签][1B 标志]`
   - 空间属性：+16 字节跳过，然后 `components × 8` 字节的值
   - 非空间多维属性：值从偏移量 8 开始
4. 修补：`ldat[idx × item_size + value_offset : +packed_size]`

### 修改关键帧时间（ldat 原位修补）

1. 导航至属性的 `ldat`（同上述值修补）
2. 从 `tdb4` 偏移量 11 读取 `time_scale`（uint32）
3. 计算：`time_raw = round(new_time_seconds × time_scale)`
4. 在偏移量 `idx × item_size + 1`（跳过 1 字节后）修补 4 字节（有符号 int32）

### 修改关键帧插值类型（ldat 原位修补）

1. 导航至属性的 `ldat`
2. 在偏移量 `idx × item_size + 5`（1 跳过 + 4 时间字节后）修补 1 字节
3. 值：`1` = 线性, `2` = 贝塞尔, `3` = 定格

**注意：** 此字节控制**出方向**的插值。要修改关键帧的入方向插值，需修改**前一个**关键帧的插值字节。

### 修改关键帧缓动数据（ldat 原位修补）

缓动数据布局取决于属性类型：

**标量 / 空间属性（components=1 或 is_spatial）：**
```
记录: [8B 头][16B 跳过][in_speed f64][in_influence f64][out_speed f64][out_influence f64]
                        ↑ 缓动从偏移量 24 开始
```

**多维属性（components > 1，非空间）：**
```
记录: [8B 头][值: C×8B][in_speed: C×8B][in_influence: C×8B][out_speed: C×8B][out_influence: C×8B]
                        ↑ 缓动从值块之后开始
```

其中 `C` = 分量数（如 2D 位置为 2，缩放为 3）。

### 修改素材文件路径（alas JSON 修补）

素材资产的文件路径存储在 `alas` 数据块的 JSON 中：

1. 导航至 `Fold → Item (asset_id) → Pin  → Als2 → alas`
2. 将 `alas` 数据解析为 UTF-8 JSON
3. 更新 `"fullpath"` 键
4. 重新序列化 JSON 并替换 `alas.data`

元素查找通过递归遍历文件夹层级，按 `idta` 中的元素 ID（偏移量 16，uint32）匹配。

### 字节序

所有多字节整数和浮点数遵循文件的字节序：
- `RIFX` → 大端序 (`>`)
- `RIFF` → 小端序 (`<`)

解析时确定的 `big_endian` 标志贯穿所有序列化函数。
