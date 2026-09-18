# Rust 版 AEP 离线编辑器 — 设计文档

> 状态：v1.0，架构评审已通过（决策记录见 11.1）
> 日期：2026-09-18
> 范围：将现有 Python + Rust 混合的 aep-tools 重建为纯 Rust 核心的 AEP 解析 / 编辑引擎，
> 覆盖 ExtendScript 持久化对象模型，支持离开 AE 的全自动化项目操作，并作为 LLM / Agent 的可靠工具层。

---

## 目录

1. [目标与非目标](#1-目标与非目标)
2. [现状与可复用资产](#2-现状与可复用资产)
3. [需求来源：管线实际 API 面](#3-需求来源管线实际-api-面)
4. [总体架构](#4-总体架构)
5. [核心设计](#5-核心设计)
6. [Agent / LLM 集成设计](#6-agent--llm-集成设计)
7. [工具形态：选项与推荐](#7-工具形态选项与推荐)
8. [验证策略](#8-验证策略)
9. [子项目拆分与里程碑](#9-子项目拆分与里程碑)
10. [风险与逆向缺口](#10-风险与逆向缺口)
11. [待敲定决策清单](#11-待敲定决策清单)
12. [附录](#12-附录)

---

## 1. 目标与非目标

### 1.1 目标

- **离线编辑 .aep**：不依赖 After Effects 进程，读取、修改、生成 AE 2025（25.x）格式的项目文件，AE 打开无警告、行为与 AE 自身操作一致。
- **ExtendScript 持久化对象模型全覆盖**：Project / Item / CompItem / FolderItem / FootageItem / Layer 各子类 / Property / PropertyGroup / Effect / Mask / Marker / TextDocument / RenderQueue 中所有**落盘**的属性与方法，命名与 AE Scripting Guide 对齐。
- **管线优先**：第一版以 BaseMan / OpenBase / RenderBird / LPads 实际用到的约 90 个 API 为验收标准（见第 3 节和附录 A）。
- **Agent 友好**：提供稳定寻址、声明式操作、干跑 / diff / 校验、紧凑投影等能力，使 LLM 驱动的自动化可靠且可审计。
- **可验证**：字节级往返、结构校验器、AE 真值回归三层验证。
- **可扩展**：模板与效果库可在任意装有 AE 的机器上一键重采，换 AE 版本或新增第三方插件不改代码。

### 1.2 非目标（显式排除）

ExtendScript 中依赖 AE 运行时的 API 不在范围内，只提供明确的"不支持"错误或近似实现：

| 类别 | 例子 | 处理 |
|---|---|---|
| 渲染与预览 | `RenderQueue.render()`, `queueInAME`, `openInViewer` | 队列**设置**可写；实际渲染交给 `aerender.exe` 包装器（可选子项目） |
| 依赖渲染的几何 | `sourceRectAtTime`, `TextLayer` 文字度量 | 不支持 |
| 表达式求值 | `Property.valueAtTime` 含表达式时、`expressionError` | 表达式字符串可读写；求值不支持；`valueAtTime` 只做关键帧插值 |
| 菜单与 UI | `executeCommand`, ScriptUI, `app.settings` | 不支持 |
| 字体系统 | `app.fonts`, 字体替换 | 字体名作为字符串读写 |
| 像素级导入 | PSD 合并图层样式、栅格化 | 不涉及；AE 打开时自行处理 |

### 1.3 兼容性边界

- **写入格式**：与源文件相同的 `format_level` / `version_id`，永不"升级"文件。
- **目标版本**：AE 2026（`format_level 0x61`）与 AE 2025（`format_level 0x60`）**完全读写**，各自独立采集模板集、结构语法与夹具，26 先行；读取兼容 23.x–24.x 并给"未验证版本"警告。26 可直接打开 25 的文件，不做升级转换。
- **语言环境**：日文 AE 为主，显示名同时存储 ja / en 两套，match name 为主键。

---

## 2. 现状与可复用资产

| 资产 | 位置 | 复用方式 |
|---|---|---|
| 格式文档（1759 行，23 节） | `docs/aep-format.md` | 直接作为 `aep-codec` 的实现依据；缺口见第 10 节 |
| Rust RIFX 解析器 ×2 | `rust/lib.rs`, `tools/aep-collect/src/rifx.rs` | 合并为 `aep-riff`，`aep-collect` 改为依赖它 |
| Python 解析器与模型 | `python/aep_parser/` | 作为**语义对照**：新旧 JSON 输出比对，直到 Rust 达到 parity |
| Python 写回逻辑 | `python/aep_tools/_writer/` | 逐函数移植；偏移量、模板选择、cdat / ldat 就地打补丁规则全部沿用 |
| 图层模板（7 种） | `_writer/_layers.py` 内嵌 base85 | 迁移为 `aep-templates` 的 `include_bytes!` 资源，并由采集脚本重新生成 |
| COS 解析器 | `_parser/cos.py` | 移植并补序列化 |
| Diff 引擎 | `gui/diff_engine.py` | 移植为 `aep-ops` 的 diff 模块 |
| 版本编码 | `tools/aep-collect/src/version.rs` | 直接迁入 `aep-codec` |
| 测试 | `tests/` | 用例思路沿用，夹具改为真实 AE 样本 |

现有代码验证了三条关键路线可行：chunk 树原样透传保证往返、就地打补丁保证未知字段不丢、从 AE 生成文件中提取模板保证新建结构合法。新架构不推翻这些结论，而是把它们做成系统化能力。

真实文件覆盖率测量（2026-09-18，`BY254H_JIN_v002.aep`，12 MB）：

| 指标 | 值 |
|---|---|
| chunk 总数 | 76,703 |
| chunk 类型数 | ~170 |
| 文档已覆盖类型 | ~40 |
| 所用效果 | 27 种，其中第三方 9 种 |

未覆盖的类型靠透传保住往返，但**新建**素材项、合成、渲染队列项时必须自己生成它们，这是逆向工作的主要来源。

---

## 3. 需求来源：管线实际 API 面

从 `digital_AE-tools` 的 TypeScript 源码统计（BaseMan、OpenBase、RenderBird、LPads、libs/ts），持久化相关 API 约 90 个，按管线重要性分级。完整清单见附录 A。

### P0 — 出片必需

| 组 | API | 备注 |
|---|---|---|
| 项目结构 | `items.addFolder`, `item.parentFolder`, `item.comment`, `item.name`, `item.remove`, `rootFolder`, `item(i)`, `numItems` | `comment` 是所有查找的主键（`getItemByComment`），对应 `cmta` chunk |
| 项目设置 | `bitsPerChannel`, `workingGamma`, `workingSpace`, `linearBlending`, `colorManagementSystem`, `timeDisplayType`, `framesCountType` | `_Baseman_initProjectSettings` |
| 合成 | `addComp`, `comp.duplicate`, `width/height/duration/frameRate`, `workAreaStart/Duration`, `comment` | duplicate 需要深拷贝全部图层并重分配 ID |
| 素材导入 | `importFile` 单帧 (tga/jpg/png)、序列 (`sequence=true`, EXR, `forceAlphabetical`)、**PSD 转合成** (`ImportAsType.COMP`)、mov | OpenBase/Replacement 自动扫描目录导入 |
| 素材操作 | `replace(file)`, `replaceWithSequence`, `mainSource.isStill`, `mainSource.conformFrameRate`, `footageMissing`, `file` | |
| 图层 | `layers.add(item[, duration])`, `addText`, `remove`, `duplicate`, `moveToBeginning/End/Before/After`, `replaceSource`, `name/comment/label`, `enabled/solo/shy/locked/guideLayer`, `startTime/inPoint/outPoint`, `blendingMode`, `source`, `containingComp`, `index` | |
| 关键帧 | `timeRemapEnabled` 开关、`property("timeRemap")`, `setValueAtTime`（**新建关键帧**）, `removeKey`, `setInterpolationTypeAtKey(HOLD)`, `numKeys`, `keyValue/keyTime` | `_Baseman_setLayerFrames`：タイムシート → 时间重映射，赛璐珞管线核心 |
| 属性 | `position/scale/opacity.setValue`, `expression`, `expressionEnabled` | |
| 效果 | `effect.addProperty(matchName 或日文显示名)`, `effect(name)`, `param.setValue`, `effect.remove`, `matchName` | 第三方：PSOFT ANTI-ALIASING, OLM Smoother |
| 文字 | `sourceText.value` / `setValue(TextDocument)`, `TextDocument.text/font/fontSize/fillColor/applyStroke/tracking/leading/baselineShift`, `resetCharStyle` | 渲染 comp 的信息文字层 |
| 保存 | `save(file)`, `newProject` | |

### P1 — 常用

| 组 | API |
|---|---|
| 渲染队列 | `renderQueue.items.add(comp)`, `item.applyTemplate("最良設定")`, `outputModule(1)`, `outputModules.add()`, `om.applyTemplate(name)`, `om.file`, `setSetting("Proxy Use"/"Motion Blur")`, `logType`, `timeSpanStart/Duration`, `render` 标志, `remove`, `duplicate` |
| 项目合并 | `importFile(另一个 .aep)` → FolderItem（Reference 文件夹） |
| 图层样式 | `property("ADBE Layer Styles")`, `<style>/enabled`, `/color`, `/opacity`, `/blur` |
| 素材解释 | `alphaMode`, `premulColor`, `invertAlpha`, `loop`, `fieldSeparationType`, `removePulldown` |
| 关键帧进阶 | `setValueAtKey`, `setTemporalEaseAtKey`, `keyInInterpolationType`, `valueAtTime` |
| 其他 | `copyToComp`, `layer.parent`, `pixelAspect`, `reduceProject`（可作为纯结构操作实现） |

### P2 — 长期全覆盖

形状图层内容、蒙版新建、标记读写、摄像机 / 灯光选项、文字动画器、Essential Graphics、Guides、代理设置，以及 ExtendScript 其余持久化属性。

---

## 4. 总体架构

### 4.1 分层

```
┌──────────────────────────────────────────────────────────────────┐
│  接口层（薄壳，可多选）                                            │
│  aep-cli   aep-mcp   aep-py (PyO3)   [aep-js]   [aep-gui]        │
├──────────────────────────────────────────────────────────────────┤
│  aep-ops        声明式操作 / 事务 / diff / 校验 / 投影     ← Agent 契约 │
├──────────────────────────────────────────────────────────────────┤
│  aep-api        ExtendScript 形对象 API（Project/Comp/Layer/...） │
│  aep-model      完整类型化树：coverage / 差分 / 往返（不进生产写入）│
├──────────────────────────────────────────────────────────────────┤
│  aep-doc        文档模型：arena chunk 树 + 索引 + 编辑原语          │
│  aep-templates  模板与效果库（采集产物）   aep-media  媒体探测/PSD  │
├──────────────────────────────────────────────────────────────────┤
│  aep-codec      每种 chunk 的类型化编解码（读 + 就地写）             │
├──────────────────────────────────────────────────────────────────┤
│  aep-riff       RIFX/RIFF 容器：无损解析与字节精确序列化             │
└──────────────────────────────────────────────────────────────────┘
        ▲
        │ 开发期工具（不进运行时）
   harvest/   ExtendScript 采集脚本 + Rust 运行器 + AE 真值比对
```

依赖方向自上而下，下层不知道上层。`aep-api` 与 `aep-ops` 并列依赖 `aep-doc`：`aep-ops` 内部通过 `aep-api` 实现每个 op，保证 Python 直接调 API 与 Agent 走 ops 的行为一致。`aep-model`（5.11）与 `aep-api` 同层，只被 CLI 的 coverage 子命令与测试使用。

### 4.2 Cargo workspace 布局

```
aep-tools-rs/                 # 新仓库（D8）
├─ Cargo.toml                 # [workspace]
├─ crates/
│  ├─ aep-riff/               # 容器层
│  ├─ aep-codec/              # 类型化 chunk 编解码、版本编码、常量表
│  ├─ aep-doc/                # 文档模型、ID 分配、导航、编辑原语
│  ├─ aep-templates/          # 模板清单 + include_bytes 资源 + 外部目录加载
│  ├─ aep-media/              # 图片头 / 序列检测 / PSD 元数据 / mov 探测
│  ├─ aep-model/              # 完整类型化树（5.11）：coverage / 差分 / 往返，不进生产写路径
│  ├─ aep-api/                # ExtendScript 形 API
│  ├─ aep-ops/                # ops schema、执行器、diff、validate、inspect 投影
│  ├─ aep-cli/                # 二进制 `aep`
│  ├─ aep-mcp/                # MCP stdio server
│  └─ aep-py/                 # PyO3 → Python 包 `aep_tools`
├─ tools/aep-collect/         # 从旧仓库迁入，改为依赖 aep-riff / aep-doc
├─ harvest/
│  ├─ jsx/                    # 采集脚本（ExtendScript）
│  ├─ runner/                 # Rust：驱动 afterfx -r、收集产物、生成 manifest / schema / format-diff
│  ├─ re/                     # 加载器分析脚本：TTD 查询、IDA 脚本、访问图产物（8.6）
│  └─ catalog/                # 采集产物，按 AE 版本分目录：ae-26.0/（先行）, ae-25.6/
├─ fixtures/
│  ├─ ae-25.6/                # AE 2025 生成的回归样本（KB 级，入库）
│  ├─ ae-26.0/                # AE 2026 生成的回归样本
│  └─ golden/                 # 旧 Python 实现生成的 JSON 对照（8.4）
└─ docs/
   ├─ aep-format.md           # 从旧仓库迁入，作为活规范
   └─ specs/                  # 本文档与各里程碑 spec
```

旧仓库 `AEP-Tools` 冻结为参考实现，不再开发。

### 4.3 crate 职责一句话

| crate | 做什么 | 不做什么 |
|---|---|---|
| `aep-riff` | 字节 ↔ chunk 树，无损，2 字节对齐，btdk / tdsn 等特例 | 不理解任何 chunk 语义 |
| `aep-codec` | `ldta`/`cdta`/`tdb4`/`cdat`/`ldat`/`opti`/`sspc`/`alas`/`cmta`/`NmHd`/`mkif`/`shph`/COS 等的 `decode(&[u8]) -> T` 与 `patch(&mut [u8], &T)`；版本位域；枚举常量 | 不持有树，不做导航 |
| `aep-doc` | arena 树、`ItemId`/`LayerId` 索引、路径导航、插入 / 删除 / 深拷贝、ID 分配、模板实例化入口、`validate`（L1–L3 校验，见 8.5）、原子保存 | 不暴露 ExtendScript 语义 |
| `aep-templates` | 模板清单（类型、AE 版本、填充点）、内置资源、外部 catalog 加载、效果 / RQ 模板查询 | 不知道如何插入文档（由 `aep-doc` 负责） |
| `aep-media` | 从文件系统推断素材元数据（尺寸、帧数、序列范围、PSD 图层树、视频时长帧率） | 不写 AEP |
| `aep-model` | 完整类型化树 `TypedDoc`：`from_doc` / `to_doc`、coverage 报告、差分测试支撑 | 不被 `aep-api` / `aep-ops` 依赖，不参与生产写入 |
| `aep-api` | ExtendScript 命名的对象与方法，1-based 索引，错误语义与 AE 一致 | 不做批处理 / 事务 |
| `aep-ops` | JSON ops 契约、执行器、`as` 绑定、事务快照、diff、op 级校验与 verified 覆盖矩阵（L4）、inspect 投影、JSON Schema 导出 | 不做 IO 以外的副作用 |

---

## 5. 核心设计

### 5.1 文档模型：chunk 树为真值

**决策：不做完整反序列化。** 文档的唯一真值是 chunk 树；类型化结构是树上的**视图**，写入以就地打补丁方式回写，未知字节永远原样保留。

理由：真实文件约 170 种 chunk 类型，已知语义约 40 种。完整反序列化意味着每个未知字段都要建模，任何遗漏都会在保存时丢数据。视图 + 补丁的模型下，未知内容天然透传，已知字段逐个点亮。

这也是写入安全的前提：没有被编辑的区域在字节级与原文件相同，编辑只发生在三种受控路径上（补丁已知字段、模板实例化、子树深拷贝），因此"输出是否可用"可以被归约为对这三条路径的验证。完整保障体系见 8.5。

```rust
// aep-doc
pub struct Doc {
    arena: Arena<Node>,         // 稳定 NodeId，插入删除不失效
    root: NodeId,
    big_endian: bool,
    trailing: Vec<u8>,          // XMP 等尾部数据
    format: FormatVersion,      // 来自 head/svap
    index: Index,               // 惰性构建：ItemId→NodeId, LayerId→NodeId, comp→layers
}

pub enum Node {
    List { kind: [u8;4], header: [u8;4], children: Vec<NodeId> },  // LIST 与 tdsn/fnam/pdnm 非 LIST 容器
    Leaf { header: [u8;4], data: Vec<u8> },
}
```

- `Utf8`/`alas`/`tdmn` 在 `aep-riff` 层也只是 `Leaf` 的字节；字符串解码在 `aep-codec`。这避免了现有实现中"合法 UTF-8 存 str、否则存 bytes"的双态。
- 典型视图：

```rust
let ldta = doc.leaf(node)?;                       // &[u8]
let mut layer = codec::LayerData::decode(ldta, doc.endian())?;
layer.flags.set(LayerFlag::Shy, true);
layer.patch_into(doc.leaf_mut(node)?, doc.endian());  // 只写已知偏移
```

- `Index` 在结构性编辑后按脏标记局部重建；`NodeId` 稳定，所以外部持有的引用不会失效。
- 保存 = `aep-riff::serialize(&doc)` + `trailing`，所有容器尺寸重算。

### 5.2 编解码层与版本策略

- 每种 chunk 一个模块，统一接口：`decode(&[u8]) -> T`、`T::patch_into(&mut [u8])`（只写已知字段，生产写路径）、`T::encode() -> Vec<u8>`（完整输出，供 5.11 的类型化路径）、`new_default(version)`（有模板的类型才提供）。
- 每个结构体显式携带 `reserved: Vec<(usize, Vec<u8>)>` 保存未理解的字节区间，保证 `encode(decode(x)) == x` 在理解不完整时也成立；理解推进时把 reserved 拆成具名字段。
- 偏移与字段来自 `docs/aep-format.md`；每个字段带注释指向文档章节。
- `FormatVersion { format_level, format_sub, version_id }`，`AeVersion` 解码沿用 `version.rs`。
- 版本差异用 `match format_level` 在 codec 内部处理，不向上层泄漏。目前只知 25.x 的布局，其他版本先按相同布局读并在 `validate` 中给出"未验证版本"警告。

### 5.3 ID、引用与寻址

AEP 内部引用全部基于 ID：`idta.item_id`、`ldta.layer_id`、`ldta.asset_id`、`parent_id`、`matte_id`、`tdpi` 图层引用、渲染队列的 comp 引用。

- **分配**：全局扫描 `max(idta.id, ldta.id) + 1`，item 与 layer 共用一个号段（现有 Python 实现如此，AE 已能正常打开其产物；是否与 AE 自身规则完全一致待 R11 采集确认）。`Doc` 缓存 `next_id`，结构性插入后递增。
- **深拷贝**（comp.duplicate、layer.duplicate、precompose、PSD 分组）：拷贝子树后重映射所有内部 ID，映射表同时用于修正 `parent_id`、`matte_id`、`tdpi`、表达式中的 `comp("name")` 不改（与 AE 一致）。
- **删除**：先扫描引用，悬空引用清零并记录警告（AE 删除素材时对应图层会变成缺失素材，我们与之一致）。

**对外寻址（Agent / CLI / Python 共用）**，稳定性从高到低：

```jsonc
// Item 选择器
{"id": 123}                               // idta.item_id，文件内稳定
{"ref": "cell_A"}                         // 本次 ops 内由 "as" 绑定
{"path": "0_sozai/_CELL/A"}               // 文件夹路径，名称可重复时取第一个并警告
{"comment": "cellFolder"}                 // 管线主键
{"name": "Main", "type": "comp"}          // type: comp|folder|footage|solid

// Layer 选择器
{"layer_id": 456}
{"comp": <ItemSel>, "index": 3}           // 1-based
{"comp": <ItemSel>, "name": "A"}
{"comp": <ItemSel>, "comment": "*cell"}

// Property 选择器：match name 路径，索引消歧
{"layer": <LayerSel>, "path": "ADBE Effect Parade/ADBE Color Key/ADBE Color Key-0001"}
{"layer": <LayerSel>, "path": "ADBE Effect Parade/[2]/[1]"}
{"layer": <LayerSel>, "path": "timeRemap"}   // ExtendScript 别名表：timeRemap, position, opacity ...
```

显示名（含日文）允许作为 fallback，但解析时给出"依赖语言环境"的警告，并在结果中回显解析到的 match name，便于 Agent 下次直接用稳定名。

### 5.4 模板系统与采集

模板是"AE 自己生成的合法二进制片段 + 填充点描述"。所有新建结构都走模板，不手写字节。

```
harvest/catalog/ae-25.6/                   # 每个 AE 版本一个目录；ae-26.0/ 结构相同
├─ manifest.json
├─ schema.json                             # 语料学习的结构语法（8.5 L3）
├─ verified-ops.json                       # op × 版本 覆盖矩阵（8.5 L4）
├─ layers/{solid,null,adjustment,shape,text,camera,light,precomp}.bin
├─ items/{folder,comp,footage-still,footage-seq,footage-mov,solid,psd-comp-root,psd-layer}.bin
├─ effects/ADBE Gaussian Blur 2.bin        # EfDf 定义 + 默认实例 sspc
├─ effects/PSOFT ANTI-ALIASING.bin
├─ rq/render-settings/最良設定.bin
├─ rq/output-modules/Prores 0_Edit(4444).bin
├─ props/{tdbs-1d,tdbs-2d-spatial,tdbs-3d,tdbs-color,...}.bin
└─ project/blank.aep                       # app.newProject 等价物
```

`manifest.json` 记录每个模板的：AE 版本、采集时间、类型、**填充点**（chunk 路径 + 偏移 + 类型 + 语义，例如 `ldta@0:u32=layer_id`）、显示名 ja/en、参数列表（效果）。填充点由采集脚本用"两次导出对比"自动推导：同一模板改一个已知值再导出，diff 出偏移。

- **内置**：AE 自带效果、基础图层 / 素材 / 属性模板随 crate `include_bytes!` 打包（压缩）。
- **外部**：第三方插件效果、公司渲染模板放在外部 catalog 目录，运行时通过 `AEP_CATALOG` 或配置加载，可多目录叠加。
- **采集**：`harvest/jsx/*.jsx` 在装有 AE 的机器上由 `harvest/runner` 通过 `AfterFX.exe -r` 无人值守执行，输出到 catalog。换 AE 版本 = 重跑一次。AE 2025 与 2026 可并存安装，runner 按安装路径分别采集，并自动生成 `format-diff.md`：两版本模板与结构语法的逐 chunk 差异，作为 codec 版本分支的依据。

### 5.5 操作层 `aep-ops`（Agent 契约）

所有非交互式使用（CLI、MCP、以及 Python 的批处理接口）共享同一份 JSON 契约。

```jsonc
{
  "version": 1,
  "open": "N:/kmt/_template/kmt_template.aep",
  "ops": [
    {"op": "project.set", "bits_per_channel": 16, "working_gamma": 2.2, "linear_blending": false},
    {"op": "folder.add", "name": "_CELL", "parent": {"comment": "sozailFolder"}, "comment": "cellFolder", "as": "cell_folder"},
    {"op": "footage.import", "file": "N:/kmt/ep01/c012/cell/A/A_0001.tga", "sequence": true,
     "parent": {"ref": "cell_folder"}, "as": "cell_A"},
    {"op": "layer.add", "comp": {"comment": "loComp_000"}, "source": {"ref": "cell_A"},
     "name": "A", "comment": "*cell", "label": 3, "start_time": 0, "as": "layer_A"},
    {"op": "effect.add", "layer": {"ref": "layer_A"}, "match_name": "ADBE Color Key",
     "params": {"ADBE Color Key-0001": [1, 1, 1, 1]}},
    {"op": "effect.add", "layer": {"ref": "layer_A"}, "match_name": "PSOFT ANTI-ALIASING"},
    {"op": "prop.time_remap", "layer": {"ref": "layer_A"}, "enabled": true,
     "keys": [{"t": 0, "v": 0}, {"t": 0.125, "v": 0.0417}], "interpolation": "hold"},
    {"op": "assert", "layer": {"ref": "layer_A"}, "num_keys": {"path": "timeRemap", "eq": 2}},
    {"op": "save", "to": "N:/kmt/ep01/c012/kmt01_c012_cmp_T1.aep"}
  ]
}
```

执行语义：

- **事务**：在内存副本上顺序执行；任一 op 失败则整体回滚，不写文件。`--continue-on-error` 可选。
- **绑定**：`"as"` 把新建对象绑定为 `ref`，后续 op 引用。结果中返回每个 `as` 的实际 `id`。
- **确定性**：相同输入文件 + 相同 ops → 字节相同的输出（ID 分配顺序固定、无时间戳），用于回归测试。
- **干跑**：`--dry-run` 执行全部 op 但不保存，返回 diff 与校验结果。
- **结果**：

```jsonc
{
  "ok": true,
  "bindings": {"cell_folder": {"id": 201}, "cell_A": {"id": 202}, "layer_A": {"layer_id": 203}},
  "warnings": [{"op": 4, "code": "display_name_lookup", "detail": "\"ブラインド\" → \"ADBE Venetian Blinds\""}],
  "diff": {"items_added": 2, "layers_added": 1, "properties_changed": 3, "chunks": [...]},
  "validation": {"errors": [], "warnings": []}
}
```

op 清单（v1）按对象分组，与 ExtendScript 方法一一对应，完整表见附录 B。JSON Schema 由 `aep-ops` 从类型定义导出，供 Agent 系统提示或工具描述直接引用。

### 5.6 ExtendScript 形 API `aep-api`

Rust 与 Python 共用的对象 API，命名规则：ExtendScript camelCase → Rust / Python snake_case，1-based 索引保留。

```rust
let mut proj = Project::open("template.aep")?;
let comp = proj.item_by_comment("loComp_000")?.as_comp()?;
let cell = proj.import_file(ImportOptions::sequence("A/A_0001.tga"))?;
let layer = comp.layers().add(&cell, None)?;
layer.set_comment("*cell")?;
layer.effects().add_property("ADBE Color Key")?.property(1)?.set_value([1.0, 1.0, 1.0, 1.0])?;
proj.save("out.aep")?;
```

- 对象是轻量句柄（`Doc` 引用 + `NodeId` / ID），不缓存状态，避免结构编辑后的失效问题。
- 错误类型区分：`NotFound`、`Unsupported(reason)`（运行时 API）、`Invalid(detail)`（参数）、`Format(detail)`（文件损坏或未知版本）。
- Python 绑定通过 PyO3 直出，方法签名与 Rust 一致；旧 `aep_tools` 的 `change_*` 底层接口不再提供。

### 5.7 素材导入与媒体探测

`importFile` 离线实现 = 媒体探测 + 素材项模板实例化 + 文件夹挂接。

| 类型 | 探测方式 | 模板 |
|---|---|---|
| 静帧 png/jpg/tga/tif/bmp/gif/exr/psd(作素材) | 自写头解析（尺寸、位深、alpha） | `footage-still` |
| 序列帧 | 目录扫描 + 编号模式（`name_0001.ext`、`name.0001.ext`、`[####]`）；`force_alphabetical` | `footage-seq`，填 `sspc` 序列字段与 `alas.target_is_folder` |
| mov / mp4 | 解析 atom（`mvhd`/`stts`）得时长与帧率；可选 `ffprobe` 后端 | `footage-mov`，按 importer 类型选 `opti` |
| wav / aiff | RIFF/AIFF 头 | `footage-audio` |
| **PSD 转合成** | 见下 | `psd-comp-root` + `psd-layer` |
| 另一个 .aep | 直接解析 | 项目合并（5.7.2） |

解释设置（alpha、预乘色、帧率一致化、循环、场）作为素材项上的可写字段，偏移由采集推导。

#### 5.7.1 PSD 转合成

AE 不在 .aep 中存像素，只存：以 PSD 命名的合成、`"<stem> レイヤー"` 文件夹（名称随语言环境，可配置）、每个 PSD 图层一个素材项，素材项引用同一 .psd 并携带图层标识。

实现：

1. `aep-media::psd` 只读 Layer & Mask Info：图层名（`luni`）、`lyid`、边界、混合模式键、不透明度、可见性、`lsct` 分组开合、剪贴标志、调整图层键（`levl`/`curv`/`hue2`/...）、文字层标记。不解码像素。
2. 按 `ImportAsType::Comp`（BaseMan 用法）：每层素材尺寸 = 文档尺寸，位置居中。`CompCroppedLayers` 作为后续选项。
3. 映射规则（由采集样本验证）：混合模式 → AE 混合模式枚举；不透明度 → `ADBE Opacity`；隐藏 → visible 标志；剪贴蒙版 → 保留底层透明度；分组 → 嵌套合成 + 子文件夹（递归）；调整图层 → AE 调整图层 + 对应效果模板；文字 / 智能对象 / 图层样式 → 按"合并进素材"处理，仅引用。
4. 采集变体：平铺、分组、隐藏、不透明度 + 混合模式、剪贴、调整层、文字层、图层蒙版、16 位、仅背景层。图层标识存放位置通过"同一 PSD 改图层顺序再导入"的 diff 定位。

#### 5.7.2 项目合并（导入 .aep 为文件夹）

解析源项目 → 所有 item / layer ID 重映射到目标号段 → `Fold` 子树整体挂到新文件夹 → 合并 `EfdG` 效果定义（按 match name 去重）→ 渲染队列不合并（与 AE 一致）。

### 5.8 效果库

- 采集脚本遍历 `app.effects`，对每个效果：在临时合成的纯色层上 `addProperty`，保存。提取 `EfdG/EfDf` 定义与图层内实例 `sspc` 子树作为模板，记录 ja/en 显示名、参数 match name、类型、默认值、取值范围。
- `effect.add`：若项目 `EfdG` 中无该定义则先注入定义，再实例化到 `ADBE Effect Parade` 末尾（或指定位置），分配参数 `tdbs`。
- 参数写入按 `parT` 类型码分派（滑块、角度、颜色、点、下拉、图层引用、复选框），沿用 `cdat` 就地补丁规则；下拉与图层引用走 `tdli`/`tdpi`。
- 第三方效果在目标机器缺失时 AE 会显示"缺失效果"，与 ExtendScript 抛错的行为不同：我们在 `validate` 中给出警告而不阻止保存（管线上渲染农场通常装了插件）。

### 5.9 渲染队列与模板

- 渲染设置模板（`.ars`）与输出模块模板（`.aom`）存于 AE 偏好，不在 .aep 内。采集脚本对每个命名模板生成一个队列项并保存，提取 `LRdr/LItm` 与 `LOm ` 子树作为模板；`applyTemplate(name)` = 用模板子树替换对应部分并回填 comp 引用、输出路径、时间跨度。
- `setSetting("Proxy Use")`、`"Motion Blur"`、`logType`、`skipFrames`、`timeSpanStart/Duration` 的偏移由采集 diff 推导。
- 实际渲染：可选 `aep render` 子命令包装 `aerender.exe`，不属于核心。

### 5.10 文本与形状

- COS 解析器移植自 `cos.py`，新增序列化；`TextDocument` 模型覆盖 `_Baseman_setGengaWorkerName` / `boldSequence` 用到的字段（text、font、fontSize、fillColor、applyStroke、tracking、leading、baselineShift、justification）。未识别键原样保留。
- `addText(str)`：文字层模板 + 由默认 `btdk` 改写文本。
- 形状内容（矩形 / 椭圆 / 填充 / 描边 / 修剪路径）走同一模板机制，P2。

### 5.11 完整反序列化：学习与对比验证路径（`aep-model`）

与 5.1 不矛盾：生产写入只走 chunk 树 + 补丁；完整反序列化是**同一套 `aep-codec` 结构体的第二条出口**，不是并行实现，用于理解度量、差分验证和学习。

```rust
// aep-model
pub struct TypedDoc { root: TypedNode, format: FormatVersion, endian: Endian, trailing: Vec<u8> }
pub enum TypedNode {
    Layer(codec::LayerData, Vec<TypedNode>),   // 已建模的容器：类型化头 + 子节点
    Property(codec::PropertyBlock),            // ...
    Opaque { header: [u8;4], data: Vec<u8> },  // 尚未建模的 chunk：原样携带
    List   { kind: [u8;4], children: Vec<TypedNode> },
}
impl TypedDoc {
    pub fn from_doc(doc: &Doc) -> Self;        // 递归 decode
    pub fn to_doc(&self) -> Doc;               // 递归 encode
}
```

三项用途：

1. **理解度量**：`aep coverage file.aep` 按 chunk 类型输出"已解释字节 / reserved 字节 / Opaque 字节"，并列出 reserved 区间。与 8.6 的 TTD 字节访问图取交集，"AE 读了但我们未建模"的区间即逆向最高优先级。度量随里程碑推进，目标在 M6 结束时核心八种 chunk 的 reserved 字节为零。
2. **差分测试**：对每个 op，分别经补丁路径（`aep-api` 直接改 `Doc`）与类型化路径（`TypedDoc` 修改字段后 `to_doc`）生成输出，断言字节相同。这证明 `patch_into` 与 `encode` 对同一字段的理解一致，是 L0 的补充证据。
3. **往返测试**：所有夹具与生产文件 `to_doc(from_doc(doc)).serialize() == original`，任何差异都是 codec 的 bug 或未携带的 reserved。

约束：`aep-api` 与 `aep-ops` **不依赖** `aep-model`；它只被 `aep-cli coverage`、测试与 harvest 工具使用。这样保证 D1 的生产路径不受影响，同时两条路径共享结构体定义，不会漂移。

---

## 6. Agent / LLM 集成设计

### 6.1 设计原则

1. **单一契约**：Agent 只需理解 5.3 的选择器和 5.5 的 ops 契约，CLI / MCP / Python 批处理三者行为一致。
2. **先看后做**：提供紧凑、可分页、带 id 的项目投影，避免把 7 万 chunk 灌进上下文。
3. **可干跑、可审计**：每次 apply 返回 diff 与校验；`--dry-run` 零副作用；输出确定性便于复核。
4. **错误可自纠**：错误信息携带候选（match name 模糊匹配、同名 item 列表、允许取值范围），Agent 无需猜测。
5. **能力可发现**：`catalog` 系列命令返回效果 / 模板 / 支持的 op 与 JSON Schema。
6. **边界明确**：不支持的 ExtendScript 能力返回 `Unsupported` 而不是静默近似。

### 6.2 投影格式（inspect）

```
$ aep inspect template.aep --outline --depth 3
Project  AE 25.6.4  16bpc  gamma 2.2  items=72 comps=10 footage=43
├─ 0_sozai/                         #5   folder  comment=sozailFolder
│  ├─ _CELL/                        #6   folder  comment=cellFolder
│  │  ├─ A                          #12  seq tga 1920x1080 48f 24fps
│  │  └─ B                          #13  seq tga 1920x1080 36f 24fps
│  └─ BG/                           #9   folder  comment=bgFolder
│     └─ bg_c012.psd                #40  comp 2048x1152 24fps 1000s  layers=6
├─ 1_lo/                            #7
└─ 9_render/                        #8   folder  comment=renderFolder
   └─ kmt01_c012_cmp_T1             #60  comp 1920x1080 24fps 5.5s  layers=29 rq=2
```

```
$ aep inspect template.aep --comp '{"comment":"loComp_000"}' --layers
#  id   name        src           in     out    flags     comment  effects
1  203  A           #12 seq       0.000  2.000  V         *cell    ADBE Color Key, PSOFT ANTI-ALIASING
2  188  bg_c012     #40 comp      0.000  2.000  V         *bg      -
```

`--json` 给结构化版本；`--property <sel>` 深入到关键帧级；每个节点都带可直接用于选择器的 `id`。

### 6.3 MCP 工具集（`aep-mcp`）

会话式：`open` 返回句柄，编辑在内存中累积，显式 `save`。所有工具参数 / 返回都是 5.5 的 JSON。

| 工具 | 作用 |
|---|---|
| `aep_open(path) → session` | 打开文件 |
| `aep_inspect(session, scope, depth, format)` | 投影 |
| `aep_query(session, selector)` | 选择器解析为节点，含候选 |
| `aep_apply(session, ops, dry_run)` | 执行 ops，返回 bindings / diff / validation |
| `aep_diff(session)` | 相对打开时的差异 |
| `aep_validate(session)` | 结构校验 |
| `aep_save(session, path)` | 保存 |
| `aep_catalog(kind, query)` | 效果 / 模板 / op schema 查询，支持模糊搜索 |
| `aep_media_probe(path)` | 导入前探测，返回将生成的素材元数据 |
| `aep_render(path, comp, ...)` | 可选：aerender 包装 |

MCP 只是 `aep-ops` 的转发层，不含业务逻辑。分两步交付：**M3 最小版**只有 `aep_open`、`aep_inspect`、`aep_query`、`aep_apply`、`aep_save` 五个工具，让 Agent 从 M3 起参与采集验证与回归排查；**M7 完整版**补齐 `aep_diff`、`aep_validate`、`aep_catalog`、`aep_media_probe`、`aep_render` 与审计日志。

### 6.4 典型 Agent 工作流

```
inspect(outline) → 定位目标（comment / path）→ media_probe(待导入文件)
→ 生成 ops → apply(dry_run) → 读 diff / warnings → 修正 → apply → save
→ [另一台机器] AE 真值验证：afterfx -r dump.jsx → 比对
```

### 6.5 安全边界

- 文件访问限制在配置的根目录白名单内（管线服务器路径）。
- `save` 默认拒绝覆盖打开的源文件，需显式 `overwrite: true`。
- ops 中不含任何执行外部命令的能力；`aep_render` 单独开关。
- 所有 apply 记录到本地 JSONL 审计日志（时间、ops、diff 摘要、输出路径），便于回溯 Agent 行为。

### 6.6 与现有管线的衔接

BaseMan.py / RenderBird.py 已是 Python 驱动。迁移路径：`ae.executeScript("#include BasemanFunctions.js")` 改为 `import aep_tools`；TS 中每个 `_Baseman_*` 函数对应移植为 Python 函数或一段 ops。Deadline 提交、目录扫描、命名规则（`namerule.py`）不变。

---

## 7. 工具形态：选项与推荐

形态尚未定，以下为候选。它们不是互斥的，核心只有一份，形态是薄壳。

| 形态 | 面向 | 成本 | 优点 | 缺点 |
|---|---|---|---|---|
| **F1 CLI + JSON ops** | 脚本、CI、任何语言、shell 型 Agent | 低 | 零依赖分发，单 exe；最容易测试 | 每次调用重新解析大文件（12 MB 约百毫秒级，可接受） |
| **F2 Python 包（PyO3）** | 现有管线、写代码型 Agent、Jupyter | 低 | 直接替换 `ae.executeScript`；对象式 API 表达力最强 | 需按 Python 版本发 wheel |
| **F3 MCP server** | 工具调用型 Agent（Claude Code、Cursor、自研 agent） | 低（建立在 ops 上） | Agent 原生；会话内多步编辑不重复解析 | 需要宿主支持 MCP |
| **F4 HTTP 服务** | 农场、多人、Web 面板 | 中 | 集中部署、鉴权、队列 | 运维负担；单机场景多余 |
| **F5 ExtendScript 兼容 JS 运行时** | 直接跑历史 .jsx | 高 | 旧脚本零改动 | 需模拟 File/Folder/ScriptUI/`$.global.Python`；ES3 方言；投入大 |
| **F6 GUI（egui）** | 人工审阅 Agent 改动、diff 查看、临时修复 | 中 | 人机协作闭环 | 与 PySide GUI 重复；可推迟 |

**推荐组合**：

- **第一批**：F1 + F2。两者都是 `aep-api` / `aep-ops` 的直接产物，管线迁移与测试都依赖它们。
- **紧随其后**：F3。ops 契约成型后 MCP 只是几百行转发代码，是 Agent 集成的主入口。M3 先出五工具最小版，M7 完整版。
- **按需**：F6 的 diff 查看器（可先复用 Python diff GUI 读 Rust 输出的 JSON）；F4 在多人 / 农场场景出现时再做；F5 仅当"历史 .jsx 必须零改动运行"成为硬需求时立项。

需要讨论的形态问题见第 11 节 D4–D6。

---

## 8. 验证策略

三层，缺一不可。

### 8.1 字节级往返（`aep-riff` / `aep-codec`）

- 任意真实文件：parse → serialize 必须字节相同（现有实现已达成，作为回归底线）。
- 每个 codec：`decode → patch(相同值) → 字节不变`；`patch(新值) → decode == 新值`。
- 属性测试（proptest）：随机 chunk 树 → serialize → parse → 相等。

### 8.2 语义校验器（`aep-doc::validate`，对应 8.5 的 L2）

不依赖 AE 的静态检查，在 apply 后与保存前自动运行：

- ID 唯一、引用可解析（asset_id / parent_id / matte_id / tdpi / RQ comp）。
- `cdat` 长度与 `tdb4` 组件数 / 空间标志一致；`ldat` 长度 = `count × item_size`。
- 图层块完整（Layr + Ewst + 视图状态 14 项）；comp 内 `DLay/SLay/CLay` 与图层数一致（规则待采集确认）。
- 素材 `alas` 路径存在性（可选，`--check-files`）。
- 效果定义存在于 `EfdG`。
- 版本已知；未知版本降级为警告。

### 8.3 AE 真值（另一台机器）

- `harvest/jsx/dump.jsx`：用 ExtendScript 把项目导出为 JSON（items / comps / layers / properties / keyframes / effects / RQ）。
- 回归流程：Rust 生成文件 → `afterfx -r dump.jsx` → 与预期 JSON 比对；同时 AE 打开无"项目损坏"对话框。
- 语义 parity：同一文件，Rust 解析 JSON 与 AE dump JSON 逐字段比对，覆盖第 3 节全部 API。
- 夹具库：`fixtures/` 存 AE 生成的小样本（每个特性一个，KB 级），入库；生产大文件不入库，用本地路径清单。

### 8.4 与旧实现的 parity

用旧仓库的 `python/aep_parser` 对每个夹具生成一次 JSON，作为 golden 文件提交到新仓库 `fixtures/golden/`。M1–M2 期间逐文件比对 Rust 输出，差异必须能解释（旧实现的 bug 或新实现的缺失）。新仓库不依赖旧代码在场。

### 8.5 写入保障阶梯："100% 可用"的工程化定义

格式是逆向的，AE 的加载器是唯一真值，任何离线校验器都不能在数学意义上证明 AE 一定接受输出。本节把"可用"拆成五个可证明、可测量、可审计的层级，并规定默认行为拒绝一切没有证据支撑的写入。

| 层 | 名称 | 保证内容 | 证明手段 | 所在 |
|---|---|---|---|---|
| L0 | 构造安全 | 写入只经由三条受控路径：补丁已知字段；AE 生成模板 + 白名单填充点实例化；子树深拷贝 + ID 重映射。**禁止手写字节。** | 代码审查规则 + 模板填充点在 manifest 中声明，实例化函数拒绝声明外的修改 | `aep-doc`, `aep-templates` |
| L1 | 容器不变量 | RIFX 结构、尺寸、2 字节对齐、字节序永远正确 | 序列化器从子节点重算尺寸，结构上不可能出错；往返测试；proptest 随机树模糊 | `aep-riff` |
| L2 | 语义不变量 | 8.2 的规则清单：cdat/ldat 长度、ID 唯一、引用可解析、枚举范围、效果定义存在、版本已知 | 每条规则一个失败夹具（人为破坏文件 → 必须被拒） | `aep-doc::validate` |
| L3 | 结构语法 | 输出树中每个容器的子块序列（类型、顺序、次数、尺寸集合、非 LIST 容器的类型前缀规则）都曾在 AE 生成的语料中出现过。**AE 没生成过的结构一律拒绝。** | 从语料自动提取 `schema.json`（每 AE 版本一份）；语料 = `fixtures/` + 本地生产文件清单；语料扩大只会放宽语法，不会误拒已验证输出 | `harvest/runner` 生成，`aep-doc::validate` 检查 |
| L4 | AE 真值 | 每个 op × AE 版本 都有 AE 验证过的夹具：AE 打开无警告，`dump.jsx` 输出与预期一致 | `verified-ops.json` 覆盖矩阵随 catalog 发布；`aep catalog ops` 可查；未 verified 的 op 在 strict 模式下拒绝执行 | `harvest/`, `aep-ops` |

L3 是离线能达到的最强保证。它把"这个文件 AE 能不能开"的问题转换为"这个文件是否只由 AE 自己产生过的结构片段组成"，后者可以离线判定。

**运行时闸门**（默认全部开启，`strict = true`）：

1. **原子保存**：写临时文件 → 重新解析 → 跑 L1–L3 → 重新解析的语义 dump 与内存模型一致 → `rename` 覆盖目标。任何一步失败，目标文件不变。
2. **源文件保护**：`save` 默认拒绝写回打开的源路径，需 `overwrite: true`；覆盖前自动备份到 `<name>.bak.aep`。
3. **warning 即失败**：strict 模式下 L2/L3 的 warning 与 error 同等对待；`--lenient` 仅供调试。
4. **未验证即拒绝**：op 未在当前 AE 版本 verified、文件版本无 catalog，均拒绝写入。
5. **审计**：每次保存记录校验结果、覆盖矩阵版本、catalog 版本到审计日志。

**保障体系抓不到的**：AE 接受但语义偏差，例如某标志位含义误判。这类问题只能靠 L4 的 dump 比对暴露，因此 L4 是每个里程碑的发布门槛，不是可选项；每新增一个 op，先写 AE 验证夹具，再实现。

### 8.6 AE 加载器分析（动态 / 静态逆向）

样本 diff 只能推断"AE 写了什么"，加载器分析回答"AE 读了什么、检查了什么、哪里按版本分支"。作为 M0 的并行轨道，在装有 AE 与 IDA 的机器上进行。

| 手段 | 工具 | 产出 | 喂给 |
|---|---|---|---|
| **字节访问图** | WinDbg TTD 录制"打开 aep"，对文件缓冲区做内存读查询（地址 → 指令指针） | 每种 chunk 的 per-byte 访问掩码：未读字节仅需模板复制，已读字节附带读取函数地址 | `aep-codec` 字段优先级；`schema.json` 的 required/ignored 掩码 |
| **chunk 分发定位** | IDA：搜索 4CC 立即数（如 `0x6C647461` = `ldta`）→ 反编译读取函数 | 精确字段布局、类型、单位；`format_level` 版本分支 | `aep-codec` 布局与版本分支；`format-diff.md` 交叉验证 |
| **校验点清单** | IDA：从损坏 / 版本错误字符串反查引用 | AE 加载时实际执行的检查列表 | `aep-doc::validate` L2 规则上限：AE 不检查的不过度约束 |
| **写入路径映射** | 断点在写 chunk 头的函数，记录 tag + 调用栈；反编译写函数 | 每种 chunk 的规范序列化顺序与默认值 | 模板填充点核对；`new_default()` 实现 |

工作方式：IDA 通过 MCP 接入，交叉引用、反编译、注释由 Agent 驱动；TTD 查询脚本与 IDA 脚本入库 `harvest/re/`，分析结论写回 `docs/aep-format.md` 对应小节并标注来源（样本 diff / 访问图 / 反编译）。

注意：Adobe EULA 禁止逆向；日本与欧盟法律有互操作性例外。是否开展由使用方自行判断，本文档只描述技术路线。

---

## 9. 子项目拆分与里程碑

每个里程碑单独出 spec 与实现计划；顺序体现依赖关系。

| 里程碑 | 交付 | 退出标准 |
|---|---|---|
| **M0 采集与真值工具链** | `harvest/jsx`（dump、模板采集、效果遍历、RQ 模板、PSD 变体）、`harvest/runner`（含 `schema.json` 提取、`format-diff.md`、`verified-ops.json` 生成）、`fixtures/` 首批样本与 golden JSON、catalog 目录结构与 manifest 格式；并行轨道 `harvest/re/`：加载器分析（8.6）产出字节访问图、版本分支清单、校验点清单 | 在采集机上一条命令对 AE 2026 产出完整 catalog（2025 待安装后同法补齐）；dump.jsx 覆盖第 3 节 API；`ldta/cdta/tdb4/cdat/ldat/idta/opti/sspc` 八种核心 chunk 有访问图与反编译布局 |
| **M1 核心读** | `aep-riff`、`aep-codec`（`decode` + `encode` + reserved）、`aep-doc` 含 `validate` L1–L3、`aep-model` 读侧与 `aep-cli coverage`、`aep-cli inspect / validate`、JSON 输出 | 25.x 与 26.x 生产文件字节往返（riff 层与 TypedDoc 层各自成立）；JSON 与 golden parity；与 AE dump parity；L3 语法对全部语料零误拒；coverage 报告可用 |
| **M2 写回与图层 CRUD** | `aep-codec` 的 `patch_into`、`aep-templates` 加载、`aep-api` 图层 / 合成 / 项目设置、comment、`aep-ops` 基础 op 与事务 / diff、原子保存与 strict 闸门、补丁路径 vs 类型化路径差分测试框架 | 旧 Python 写回能力 100% 平移；M2 全部 op 在两个 AE 版本上 verified 且差分测试通过 |
| **M3 项目结构与素材导入** | `aep-media`、`footage.import`（静帧 / 序列 / mov）、`folder.add`、`comp.add`、`comp.duplicate`、`replace`、解释设置、项目合并；`aep-mcp` 最小版（open / inspect / query / apply / save） | OpenBase 目录扫描导入可用 Rust 复现，AE 验证一致；Agent 通过最小 MCP 完成"导入素材 → 加图层 → 保存"并经 AE 验证 |
| **M4 PSD 转合成** | `aep-media::psd`、PSD 模板集、映射规则 | BaseMan `_Baseman_importPsdAsBgComp` 场景全部变体 AE 验证一致 |
| **M5 效果与关键帧** | 效果库注入与实例化、参数类型全覆盖、关键帧新建 / 删除 / 插值 / 缓动、时间重映射、表达式、图层样式 | `_Baseman_setLayerFrames`、`setAntiAliasing`、CharaLightSetter 场景 AE 验证一致 |
| **M6 文字与渲染队列** | COS 序列化、TextDocument、`addText`、RQ 模板应用、输出模块 | RenderBird 队列构建与 boldSequence 场景 AE 验证一致 |
| **M7 接口层** | `aep-py` 完整绑定、`aep-mcp`、ops JSON Schema 发布、审计日志、BaseMan 迁移示例 | BaseMan 新建工程流程离线跑通；Agent 通过 MCP 完成"导入素材 → 加图层 → 加效果 → 保存"演示 |
| **M8（可选）** | aerender 包装、diff GUI、HTTP 服务、JS 运行时、P2 API | 按需立项 |

M0 与 M1 可并行：M0 在有 AE 的机器上进行，M1 只需现有生产文件。

---

## 10. 风险与逆向缺口

按对里程碑的阻塞程度排序。

| # | 缺口 | 影响 | 解法 |
|---|---|---|---|
| R1 | **素材项内部**：`Pin` 下 `opti` 各 importer 变体、`pgui`、`CLRS`（色彩空间）、`mnfo`、item 级 `ftgi`、视图状态 `fidi/fipl/fmpl/fimr/fips` | M3 | 采集每种 importer 的最小样本，diff 推导填充点；未知块整体从模板复制 |
| R2 | **PSD 图层标识**存放位置与分组 / 剪贴 / 调整层映射 | M4 | 5.7.1 的变体采集 |
| R3 | **`cmta` 注释**编码（item 与 layer 级） | M2 | 采集含注释样本，预计为 Utf8 变体 |
| R4 | **comp 级图层簿记**：`DLay/SLay/CLay`、`CIFO/CIF2/CIF3`、`Ewst/ewin/ewot` | M2–M3 | 现有图层 CRUD 已处理 16 块结构；comp.add / duplicate 需完整规则，采集验证 |
| R5 | **效果参数类型**全覆盖（`parT` 类型码 0–18 及未知） | M5 | 效果遍历采集自动暴露全部类型；未知类型标记为只读 |
| R6 | **关键帧从零创建**：各属性类型 `ldat` 记录布局、`lhd3` 头、`tdb4.animated`、时间刻度 | M5 | 现有文档已覆盖读取布局；用"1 个 / 2 个关键帧"样本 diff 确认写入 |
| R7 | **渲染队列 chunk**：`LRdr/Rhed/Rout/LItm/LOm/ARsi`、setting 偏移 | M6 | 模板采集 + diff |
| R8 | **AE 版本差异**：25.x（`0x60`）与 26.x（`0x61`）format_level 不同，布局可能有差异；23.x / 24.x 未采集 | 全程 | 两版本各自采集 catalog，`format-diff.md` 暴露差异，codec 按 format_level 分支；23/24 只读并警告。需要采集机同时装有 AE 2025 与 2026 |
| R9 | **语言环境**：显示名依赖 ja/en | M5–M7 | 采集时同时记录两种语言（AE 可切换语言重采） |
| R10 | **大文件性能**：37 MB 生产文件、arena 内存 | M1 | 目标：解析 < 200 ms、内存 < 3× 文件大小；惰性索引 |
| R11 | **AE ID 规则**是否允许 item / layer 号段共用、是否有上限 | M2 | 已有证据支持共用；采集 AE 连续新建后的 ID 序列确认 |
| R12 | **`iide/idpc/Gide/gdta`** 等 item 伴随块语义 | M3 | 透传 + 模板复制，暂不解读 |

---

## 11. 待敲定决策清单

评审时逐条确认，确认后写入本文档"决策记录"。

| # | 决策 | 推荐 | 备选 |
|---|---|---|---|
| D1 | 文档模型：chunk 树为真值 + 视图补丁 | **采用** | 完整反序列化（否决理由见 5.1） |
| D2 | Workspace 与 crate 边界（4.2） | **采用** | 更少 crate（合并 codec 进 doc） |
| D3 | ops JSON 作为 Agent / CLI / MCP 唯一契约 | **采用** | 每个接口各自定义 |
| D4 | 第一批形态 | **F1 CLI + F2 Python** | 先 MCP |
| D5 | MCP 时机 | **M3 最小版（五工具），M7 完整版** | M7 一次到位 |
| D6 | GUI | **推迟；先复用 Python diff GUI** | egui 新 GUI |
| D7 | JS 运行时（F5） | **不立项，除非硬需求** | M8 |
| D8 | 仓库策略 | **新仓库 `aep-tools-rs`**：干净 workspace；迁入格式文档（改为活规范）、本设计文档、后续 aep-collect；旧仓库冻结为参考，parity 通过 golden JSON 解耦 | 本仓库改 workspace，Python 归档到 M2 后 |
| D9 | Python 包 | **新 `aep_tools` v2，ExtendScript 命名，不兼容旧 `change_*`**；1.0 时接管 PyPI `aep-tools` 名称 | 保留旧 API 兼容层 |
| D10 | 模板分发 | **内置 AE 自带 + 外部 catalog 目录叠加** | 全部外部 |
| D11 | 目标 AE 版本 | **25.x 与 26.x 完全读写，各自 catalog；23/24 只读并警告** | 仅 25.x |
| D12 | 采集执行位置 | **另一台装 AE 的机器，无人值守 `afterfx -r`** | 手动导出 |
| D13 | 夹具入库 | **KB 级 AE 样本入库，生产文件走本地清单** | 全部不入库 |
| D14 | ExtendScript 运行时 API 处理 | **`Unsupported` 错误** | 静默忽略 |
| D15 | Agent 安全边界（6.5） | **路径白名单 + 审计日志 + 覆盖需显式** | 无限制 |
| D16 | 写入保障（8.5） | **五层阶梯 + strict 默认 + 未 verified 即拒绝 + 原子保存** | 仅 L1–L2 校验，L4 作为人工流程 |
| D17 | 采集与验证顺序 | **先 AE 2026（采集机已有），2025 待安装后补齐 catalog；期间 25.x 生产文件作只读夹具** | 仅 2026 |
| D18 | 加载器逆向（8.6） | **作为 M0 并行轨道开展，IDA 经 MCP 接入，TTD 做访问图** | 仅样本 diff |
| D19 | 完整反序列化（5.11） | **做，作为共享结构体的第二出口：coverage / 差分 / 往返；不进生产写路径** | 不做 |

### 11.1 决策记录

| 日期 | 决策 | 结论 |
|---|---|---|
| 2026-09-18 | D1 文档模型 | 确认：chunk 树为真值 + 视图补丁，配合 8.5 保障阶梯 |
| 2026-09-18 | D8 仓库策略 | 确认：新仓库 `aep-tools-rs`，旧仓库冻结 |
| 2026-09-18 | D11 目标版本 | 确认：25.x 与 26.x 完全读写 |
| 2026-09-18 | D16 写入保障 | 确认：五层阶梯 + strict 默认 |
| 2026-09-18 | D17 采集顺序 | 确认：26 先行，25 后补 |
| 2026-09-18 | D18 加载器逆向 | 确认：M0 并行轨道 |
| 2026-09-18 | D19 完整反序列化 | 确认：用户提出，作为学习与对比验证路径 |
| 2026-09-18 | D2 crate 边界 | 确认：按 4.2 拆分，边界由 Cargo 依赖强制 |
| 2026-09-18 | D3 ops 契约 | 确认：5.3 选择器 + `as` 绑定 + 事务默认全有或全无 + JSON Schema 自动导出；Agent 只经 ops 改文件 |
| 2026-09-18 | D4 第一批形态 | 确认：CLI + Python |
| 2026-09-18 | D5 MCP 时机 | 确认：M3 最小版五工具，M7 完整版 |
| 2026-09-18 | D6 GUI | 确认：推迟，先复用 Python diff GUI |
| 2026-09-18 | D7 JS 运行时 | 确认：不立项 |
| 2026-09-18 | D9 Python 包 | 确认：新 `aep_tools` v2，不兼容旧 `change_*` |
| 2026-09-18 | D10 模板分发 | 确认：内置 + 外部 catalog 叠加 |
| 2026-09-18 | D12 采集位置 | 确认：采集机无人值守 |
| 2026-09-18 | D13 夹具入库 | 确认：KB 级样本入库，生产文件本地清单 |
| 2026-09-18 | D14 运行时 API | 确认：`Unsupported` 错误 |
| 2026-09-18 | D15 Agent 安全边界 | 确认：路径白名单 + 审计日志 + 覆盖需显式 |

全部 19 条决策已确认，架构评审关闭。下一步：为 M0 与 M1 分别撰写实现计划。

---

## 12. 附录

### 附录 A：脚本用到的 ExtendScript API 全表

来源：`digital_AE-tools/root/Scripts/{BaseMan,OpenBase,RenderBird,LPads,InternalScripts}` 与 `libs/ts`，2026-09-18 统计。

**app / project**：`app.project`, `app.newProject`, `app.project.save(file)`, `app.project.file`, `app.project.item(i)`, `app.project.items`, `numItems`, `rootFolder`, `renderQueue`, `selection`, `activeItem`, `bitsPerChannel`, `workingGamma`, `workingSpace`, `linearBlending`, `colorManagementSystem`, `timeDisplayType`, `framesCountType`, `importFile(ImportOptions)`, `items.addFolder`, `items.addComp`, `app.version`, `app.effects`（只读枚举）, `app.beginUndoGroup/endUndoGroup`（无操作）, `app.settings`（不支持）, `reduceProject`。

**ImportOptions**：`file`, `sequence`, `forceAlphabetical`, `importAs`（FOOTAGE / COMP）。

**Item 通用**：`name`, `comment`, `id`, `parentFolder`, `remove`, `selected`, `typeName`, `label`。

**FolderItem**：`numItems`, `item(i)`, `items`。

**CompItem**：`name`, `comment`, `width`, `height`, `duration`, `frameRate`, `frameDuration`, `pixelAspect`, `workAreaStart`, `workAreaDuration`, `numLayers`, `layer(i)`, `layers`, `layers.add(item[, duration])`, `layers.addText(text)`, `layers.addSolid`, `layers.addNull`, `duplicate`, `selectedLayers`。

**FootageItem / FootageSource**：`file`, `mainSource`, `mainSource.isStill`, `mainSource.conformFrameRate`, `mainSource.alphaMode`, `premulColor`, `invertAlpha`, `loop`, `fieldSeparationType`, `highQualityFieldSeparation`, `removePulldown`, `hasAlpha`, `footageMissing`, `replace(file)`, `replaceWithSequence(file, forceAlphabetical)`, `width`, `height`, `duration`, `frameRate`, `SolidSource`/`FileSource` 类型判断。

**Layer / AVLayer**：`name`, `comment`, `label`, `index`, `enabled`, `solo`, `shy`, `locked`, `guideLayer`, `nullLayer`, `active`, `startTime`, `inPoint`, `outPoint`, `blendingMode`, `parent`, `source`, `containingComp`, `timeRemapEnabled`, `canSetTimeRemapEnabled`, `remove`, `duplicate`, `moveToBeginning`, `moveToEnd`, `moveBefore`, `moveAfter`, `replaceSource(item, fixExpressions)`, `copyToComp`, `property(name)`, `layer("Effects")`, `effect`, `position`, `scale`, `opacity`。

**TextLayer / TextDocument**：`sourceText`, `sourceText.value`, `sourceText.setValue(doc)`, `sourceText.expressionEnabled`, `new TextDocument(str)`, `text`, `font`, `fontSize`, `fillColor`, `applyStroke`, `tracking`, `leading`, `baselineShift`, `resetCharStyle`。

**Property / PropertyGroup**：`value`, `setValue`, `setValueAtTime`, `setValueAtKey`, `numKeys`, `keyValue`, `keyTime`, `removeKey`, `setInterpolationTypeAtKey`, `keyInInterpolationType`, `setTemporalEaseAtKey`, `valueAtTime`, `expression`, `expressionEnabled`, `matchName`, `numProperties`, `property(i|name)`, `addProperty(name)`, `remove`, `propertyGroup`。

**RenderQueue**：`items.add(comp)`, `numItems`, `item(i)`, `item.remove`, `item.duplicate`, `applyTemplate(name)`, `getSetting/setSetting`, `logType`, `render`, `timeSpanStart`, `timeSpanDuration`, `comp`, `numOutputModules`, `outputModule(i)`, `outputModules.add()`, `om.applyTemplate(name)`, `om.file`。

**效果 / 属性名字面量**：`ADBE Color Key`, `ADBE Gaussian Blur 2`, `ADBE Effect Parade`, `ADBE Transform Group`, `ADBE Position`, `ADBE Layer Styles`, `ADBE Mask Shape`, `ADBE CHANNEL MIXER`, `ADBE Exposure2`, `ADBE Slider Control`, `ADBE Point Control`, `ADBE Angle Control`, `PSOFT ANTI-ALIASING`, `OLM Smoother`, `VIDEOCOPILOT VIBRANCE`, `Optical Glow`, 日文显示名 `ブラインド`, `ブラー`, `チャンネルミキサー`, `露光量`, `角度制御`, `ポイント制御`, `スライダー制御`, `timeRemap`, `Layer Styles`, `<style>/enabled|color|opacity|blur`。

**渲染模板名**：`最良設定`, `最良設定 23.976`, `マルチマシン設定`, `Prores 0_Edit(4444)`, `Prores 0_sozai(4444)`, `Prores 1_HQ(422HQ)`, `Prores 4_preview(422proxy)`, `DNx_175_10bit_1520_855_23976`, `H.264 - レンダリング設定を一致 - 15 Mbps`, `PNG(lossless)`, `PNG(lossless)+`, `JPEG_低画質`, `OpenEXR+`, `OpenEXR_Backup`。

### 附录 B：ops v1 清单

| op | 对应 ExtendScript | 关键字段 |
|---|---|---|
| `project.set` | Project 属性 | `bits_per_channel`, `working_gamma`, `working_space`, `linear_blending`, `color_management`, `time_display_type`, `frames_count_type` |
| `project.import_aep` | `importFile(.aep)` | `file`, `parent`, `as` |
| `folder.add` | `items.addFolder` | `name`, `parent`, `comment`, `as` |
| `item.set` | Item 属性 | `target`, `name`, `comment`, `label`, `parent` |
| `item.remove` | `item.remove` | `target` |
| `comp.add` | `items.addComp` | `name`, `width`, `height`, `pixel_aspect`, `duration`, `frame_rate`, `parent`, `as` |
| `comp.duplicate` | `comp.duplicate` | `target`, `name`, `as` |
| `comp.set` | CompItem 属性 | `target`, `width`, `height`, `duration`, `frame_rate`, `work_area_*`, `bg_color`, 各标志 |
| `footage.import` | `importFile` | `file`, `sequence`, `force_alphabetical`, `import_as` (`footage`/`comp`/`comp_cropped`), `parent`, `as` |
| `footage.replace` | `replace` / `replaceWithSequence` | `target`, `file`, `sequence` |
| `footage.set_interpretation` | FootageSource 属性 | `target`, `conform_frame_rate`, `alpha_mode`, `premul_color`, `invert_alpha`, `loop`, `field_separation`, `remove_pulldown` |
| `layer.add` | `layers.add` | `comp`, `source`, `duration`, `index`, `name`, `comment`, `label`, `start_time`, `as` |
| `layer.add_solid` / `add_null` / `add_adjustment` / `add_text` / `add_shape` / `add_camera` / `add_light` | `layers.add*` | `comp`, `name`, 类型特定字段, `as` |
| `layer.set` | Layer 属性 | `target`, `name`, `comment`, `label`, `enabled`, `solo`, `shy`, `locked`, `guide`, `adjustment`, `three_d`, `start_time`, `in_point`, `out_point`, `stretch`, `blending_mode`, `track_matte`, `parent`, `quality`, `preserve_transparency` |
| `layer.remove` / `duplicate` / `move` | 对应方法 | `target`, `to`: `beginning`/`end`/`{before}`/`{after}`/`{index}` |
| `layer.replace_source` | `replaceSource` | `target`, `source`, `fix_expressions` |
| `layer.precompose` | `precompose` | `comp`, `layers`, `name`, `move_all_attributes`, `as` |
| `layer.copy_to_comp` | `copyToComp` | `target`, `comp` |
| `prop.set_value` | `setValue` | `target`, `value` |
| `prop.set_keys` | 替换全部关键帧 | `target`, `keys: [{t, v, in?, out?, ease?}]`, `interpolation` |
| `prop.add_key` / `remove_key` / `set_key` | `setValueAtTime` / `removeKey` / `setValueAtKey` + 插值 / 缓动 | `target`, `t` / `index`, `value`, `in_interp`, `out_interp`, `ease` |
| `prop.set_expression` | `expression` | `target`, `expression`, `enabled` |
| `prop.time_remap` | `timeRemapEnabled` + 关键帧 | `layer`, `enabled`, `keys`, `interpolation` |
| `effect.add` | `effect.addProperty` | `layer`, `match_name` \| `display_name`, `index`, `name`, `params`, `as` |
| `effect.set_params` | 参数 `setValue` | `target`, `params: {match_name: value}` |
| `effect.remove` / `move` | `remove` / 顺序 | `target`, `to` |
| `layer_style.set` | Layer Styles 子属性 | `layer`, `style`, `enabled`, `params` |
| `mask.add` / `mask.set` | Mask Parade | `layer`, `path`, `mode`, `inverted`, `feather`, `opacity` |
| `text.set` | `sourceText.setValue` | `layer`, `text`, `font`, `font_size`, `fill_color`, `stroke`, `tracking`, `leading`, `justification` |
| `marker.set` | `Marker` | `target`, `markers` |
| `rq.add` | `renderQueue.items.add` | `comp`, `render_template`, `settings`, `log_type`, `time_span`, `as` |
| `rq.output.add` / `rq.output.set` | `outputModules.add` / `applyTemplate` / `file` | `item`, `template`, `file`, `settings` |
| `rq.clear` | 循环 `remove` | — |
| `assert` | 测试辅助 | 任意选择器 + 断言 |
| `save` | `app.project.save` | `to`, `overwrite` |

### 附录 C：ExtendScript ↔ Rust / Python 命名规则

- 类名保留：`Project`, `CompItem`, `FolderItem`, `FootageItem`, `AVLayer`, `TextLayer`, `ShapeLayer`, `CameraLayer`, `LightLayer`, `Property`, `PropertyGroup`, `TextDocument`, `RenderQueueItem`, `OutputModule`, `ImportOptions`。
- 方法 / 属性：camelCase → snake_case（`setValueAtTime` → `set_value_at_time`, `numLayers` → `num_layers`）。
- 集合：`layers[i]`、`items[i]` 1-based；同时提供 `iter()`。
- 枚举：`BlendingMode::MULTIPLY` 等与 AE 常量同名同值。
- 属性别名：`"timeRemap"`, `"position"` 等 ExtendScript 简写在 `property()` 中可用，内部映射到 match name。

### 附录 D：ldta / cdta 等已知偏移

沿用 `docs/aep-format.md` 第 6–19、23 节，不在此重复；`aep-codec` 实现每个字段时在注释中引用对应小节。
