# M-REx Perception — Python 全栈架构设计

> 版本: v0.1（设计草案） · 日期: 2026-10-01 · 状态: 待评审
>
> 技术选型: **Python + PySide6 (Qt6) + PyVista/VTK + pyqtgraph**
>
> UI 专题: Qt6 界面架构与工作流全部内容见 [`ui-architecture.md`](./ui-architecture.md)；本文档 UI 部分仅作概览。
>
> 目标: 在完全不依赖 MATLAB 的前提下复刻 `runSimulation.m` 的全部仿真逻辑，并提供 Rhino 式多视图 3D + 仪表盘的现代 GUI。**首期目标是在纯仿真（虚拟）环境中跑通全部逻辑**；YOLO 与实体泵为可插拔的后续阶段（当前以占位接口存在）。

---

## 1. 目标与范围

### 1.1 目标

| # | 目标 | 说明 |
|---|------|------|
| G1 | 逻辑等价 | 复刻 `src/**/*.m` + `runSimulation.m` 的仿真语义（状态机、公式、边界行为） |
| G2 | 纯虚拟可运行 | 仿真模式（无硬件、无 YOLO、无 MATLAB）即可完成完整 pick-and-place 流程 |
| G3 | 现代 GUI | 三个同步 3D 正交视图（Top/Front/Right，Rhino 风格）+ 仪表盘参数/控制/图表 |
| G4 | 可插拔 | 胚胎来源（随机 / YOLO）、泵驱动（仿真 / 串口）均为接口，运行期切换 |
| G5 | 不阻塞 | 仿真运行于工作线程，UI 渲染于主线程，任意时刻可暂停/停止/关闭 |
| G6 | 可打包 | PyInstaller 产出可分发的桌面应用（详见 §14） |
| G7 | VS Code 全流程 | 纯 `.py` + `.md`，全部可在 VS Code 中编辑与调试 |

### 1.2 非目标（当前阶段）

- YOLO 模型训练与数据标注（继续留在 `python/` 目录的既有工具链中）
- 真实机械臂/运动平台控制（当前硬件接口只有注射泵）
- 多用户/网络/远程操作
- 修改既有 MATLAB 代码（MATLAB 仅作为参考实现保留）

---

## 2. 设计原则

1. **核心与 UI 严格分层**：`mrex_perception/core/**` 不 import 任何 Qt/VTK；UI 只消费只读快照。
2. **语义保真优先**：移植阶段遇到 MATLAB 的"怪行为"（如 `clustered` 不参与选择）先原样保留，逐条记录在 §16，评审后再改。
3. **单一数据流**：UI 只通过"命令 → 引擎 → 快照 → 渲染"单向流转，无双向状态同步。
4. **可复现**：所有随机性通过注入的 `numpy.random.Generator` 实现，测试可固定 seed。
5. **线程边界**：仿真在线程 A，渲染在线程 B；两者之间只传不可变快照。
6. **单位与坐标约定**（与 MATLAB 完全一致）：
   - 长度 **mm**，角度内部用 **rad**，仅在 UI 显示时转 deg；
   - 坐标：x、y 为水平面，z 为高度；`pixelToWorkspace` 中图像 y 轴翻转逻辑保持一致；
   - 向量：`numpy.ndarray`，形状 `(3,)`；旋转矩阵 `(3,3)`；位姿 `(4,4)`；运动日志 `(N,3)`。
   - **ID 保持 1 起始**（沿用 MATLAB 语义，UI 显示与日志一致，避免 off-by-one 混淆）。

---

## 3. 总体架构

```mermaid
flowchart TB
    subgraph UI["UI 层（主线程）— PySide6（详见 ui-architecture.md）"]
        MW[MainWindow<br/>组合根 / 运行控制器]
    end

    subgraph APP["应用层"]
        WORKER[SimulationWorker<br/>QThread]
    end

    subgraph CORE["核心层 mrex_perception/core（纯 Python，可无头运行）"]
        ENGINE[SimulationEngine<br/>主循环编排]
        PLANNER[planner 选胚/落位]
        MOTION[motion 运动插值]
        GRASP[grasping 抓取/释放]
        SUMMARY[summary 统计汇总]
        MODELS[models 领域模型]
        MLOG[motion_log 运动记录]
    end

    subgraph ADAPTERS["适配层（可插拔）"]
        SRCDET[detection<br/>RandomSource / YoloSource（占位）]
        HW[hardware<br/>SimulatedPump / SerialPump]
    end

    CFG[config 配置加载<br/>workspace YAML + app 默认值]

    MW --> WORKER
    WORKER --> ENGINE
    ENGINE --> PLANNER
    ENGINE --> MOTION
    ENGINE --> GRASP
    ENGINE --> MLOG
    ENGINE --> SUMMARY
    ENGINE --> MODELS
    ENGINE --> SRCDET
    ENGINE --> HW
    CFG --> ENGINE
    WORKER -. "快照 latest-wins / 完成信号" .-> MW
```

**数据流一句话**：`UI 命令（start/pause/stop/reset）→ MainWindow → SimulationWorker(QThread) → SimulationEngine 逐步推进 → 发布不可变 Snapshot → UI 主线程渲染`；UI 侧细节（组件四件套、快照泵、节流、信号接线）见 [`ui-architecture.md`](./ui-architecture.md)。

---

## 4. 目录结构

```text
M-REx_Perception/
├── doc/
│   ├── python-architecture.md        # 本文档
│   ├── ui-architecture.md            # Qt6 UI 架构与工作流（UI 专题）
│   └── migration-plan.md             # 迁移计划
├── mrex_perception/                  # 【新增】Python 全栈应用
│   ├── __init__.py
│   ├── __main__.py                   # 入口: python -m mrex_perception
│   ├── main.py                       # QApplication 启动与依赖装配
│   ├── core/                         # 【纯逻辑】不依赖 Qt/VTK；按角色分层，依赖只向下
│   │   ├── __init__.py
│   │   ├── math/                     # ① 纯函数：旋转/位姿变换 + 像素映射
│   │   │   ├── transforms.py         # rotation_z / make_pose
│   │   │   └── geometry.py           # pixel_to_workspace 等坐标映射
│   │   ├── models/                   # ② 数据模型（子包 __init__ 转发导出）
│   │   │   ├── states.py             # EmbryoState / ToolState 枚举（字符串值对齐 MATLAB）
│   │   │   └── entities.py           # Workspace / Embryo / EmbryoSpec / ToolHead / Snapshot
│   │   ├── setup/                    # ③ 构造：配置/检测 → 实体
│   │   │   └── embryos.py            # populate_random / from_detections / mark_clustered
│   │   ├── sim/                      # ④ 运行期行为
│   │   │   ├── planner.py            # has_free / select_nearest_free / next_moved_position
│   │   │   ├── motion.py             # move_tool / raise / lower / return_home ...
│   │   │   ├── motion_log.py         # 运动记录（ZYX 欧拉角提取）
│   │   │   └── grasping.py           # pickup_probability / grasp / release
│   │   ├── reporting/                # ⑤ 结果输出
│   │   │   └── summary.py            # compute_summary（对应 simulationSummary.m）
│   │   └── engine.py                 # SimulationEngine：主循环 + 停止/暂停令牌
│   ├── detection/                    # 【可插拔】胚胎来源
│   │   ├── __init__.py
│   │   ├── base.py                   # EmbryoSource Protocol
│   │   ├── random_source.py          # 随机布置（现在可用）
│   │   └── yolo.py                   # YOLO 占位（NotImplementedError + 未来接入点）
│   ├── hardware/                     # 【可插拔】硬件
│   │   ├── __init__.py
│   │   ├── base.py                   # PumpDriver Protocol
│   │   ├── simulated.py              # 仿真泵（空操作，不等待）
│   │   └── serial_pump.py            # pyserial（对齐 releaseWithPump.m 命令集）
│   ├── ui/                           # 【UI 层】PySide6 组件四件套 + uic 工作流
│   │                                 # （目录、约定与运行机制详见 doc/ui-architecture.md）
│   └── config/
│       ├── __init__.py
│       ├── loader.py                 # 通用 YAML 读取机制（路径解析 / 解析 / 报错）
│       ├── workspace.py              # workspace schema（pydantic）+ 加载 / 枚举可用配置
│       ├── embryo.py                 # embryo schema → EmbryoSpec（几何 + 设置阈值）
│       ├── tool_head.py              # tool head schema → to_tool_head(workspace) 工厂
│       └── app.py                    # AppConfig 聚合（注入用）+ load_app_config
├── config/
│   ├── workspace/
│   │   └── default.yaml              # 工作区配置（snake_case 键）
│   ├── embryo/
│   │   └── default.yaml              # 胚胎模板（几何 / 检测阈值）
│   └── tool_head/
│       └── default.yaml              # 工具头（交互面 / 粘附模型 / 运动学）
├── python/                           # 【保留】YOLO 工具链（训练/推理脚本 + models）
├── src/                              # 【保留】MATLAB 参考实现（冻结，仅作对照）
├── tests/
│   ├── README.md                     # 测试布局说明
│   ├── core/                         # 与 core 分层对应（math/setup/motion/planner/grasping/summary）
│   └── test_config.py                # config loader + workspace 校验
└── pyproject.toml                    # 【新增】依赖与工具配置
```

**说明**：包名 `mrex_perception`（2026-10-01 由 `mrex` 更名而来）与 MATLAB 工程 "TaskFlow" 命名并存；如需再次更名只需整体重命名一次，文档中不依赖包名语义。

---

## 5. 领域模型

### 5.1 Workspace（配置驱动）

字段与 `config/workspace/default.yaml` 一一对应（键为 snake_case、与 Python 属性同名；2026-10-06 起不再与 MATLAB 共用 camelCase 键名）：

| 字段 | 默认值 | 单位/含义 |
|---|---|---|
| `size` | `[100, 40, 10]` | 工作区尺寸 (x, y, z) mm |
| `source_region` | `[0, 5, 30, 30]` | 源区域 `[x, y, w, h]` mm |
| `moved_region` | `[40, 5, 45, 30]` | 落位区域 `[x, y, w, h]` mm |
| `moved_spacing` | `4` | 落位间距系数（× 胚胎 length） |
| `material` | `glass` | 基底材料 |
| `surface_height` | `0` | 表面高度 mm |
| `coeff_friction` | `0.4` | 摩擦系数 |
| `youngs_modulus` | `7e10` | 弹性模量 Pa |
| `poisson_ratio` | `0.22` | 泊松比 |
| `density` | `2500` | 密度 kg/m³ |
| `surface_energy` | `0.1` | 表面能 |

校验规则：所有字段必填（pydantic 原生，缺字段抛 `ValidationError`）；`size` 3 个值、`source_region` / `moved_region` 各 4 个值。

### 5.2 Embryo

| 字段 | 类型 | 默认/来源 | 说明 |
|---|---|---|---|
| `id` | int (1-based) | 列表索引 | UI 显示用 |
| `state` | `EmbryoState` | `free` | 见 §5.4 状态机 |
| `attempts` | int | 0 | 抓取尝试次数 |
| `picked_successfully` | bool | False | 是否成功抓取过 |
| `shape` | str | `"ellipsoid"` | 固定 |
| `width` / `length` / `height` | float (mm) | `0.2 / 0.5 / 0.2` | 尺寸（默认来自 `EmbryoSpec`，即 `config/embryo/*.yaml`） |
| `confidence` | float | 1.0（随机）/ CSV（YOLO） | |
| `position` | `(3,)` | 随机或像素反算 | z=0.1 mm |
| `orientation` | `(3,3)` | 绕 z 的 yaw 旋转矩阵 | 见下 |
| `pose` | `(4,4)` | 组装 | |
| `is_clustered` | bool | 聚类检测写入 | |

- 随机源：`yaw = 2π·U(0,1)`，`Rz` 同 MATLAB；
- YOLO 源：`yaw = -theta`（YOLO OBB 角度取负），尺寸取 `EmbryoSpec`（默认同一组固定值，与 `createEmbryoFromYOLO.m` 一致）。
- 创建参数（几何、`min_confidence`、`cluster_threshold`、`min_spacing`）集中在 core `EmbryoSpec`（2026-10-08 起由 `config/embryo/*.yaml` 驱动）。

### 5.3 ToolHead

2026-10-08 起几何/粘附系数/运动学由 `config/tool_head/*.yaml` 驱动（嵌套段 `contact_surface` / `adhesion` 在 core 模型上平铺；默认值镜像 `config/tool_head/default.yaml`）：

| 字段 | 值 | 说明 |
|---|---|---|
| `name` | `"adhesionTool"` | |
| `contact_radius` | 0.25 mm | 交互面（液滴接触斑）半径 |
| `contact_shape` | `"circular"` | 交互面形状（预留非圆形态） |
| `diameter` / `radius` / `height` | 1.5 / 0.75 / 0.5 mm | 圆柱体 |
| `clearance` | 1 mm | 胚胎吸附时相对工具的 z 偏移、接近高度 |
| `position` | `[sx/2+15, sy/2+15, 10]` = `[15, 17.5, 10]`（默认配置） | 初始/回零位置（`home_offset` 驱动） |
| `orientation` | `I₃` | |
| `state` | `ToolState` | |
| `has_embryo` / `attached_embryo_id` | False / 0 | |
| `adhesion_model` | `"vanDerWaalsDroplet"` | |
| `base_probability` / `reference_width` / `attempt_penalty` / `max_attempts` | 0.7 / 0.2 / 0.05 / 3 | pickup 概率模型系数（见 §6.5；`reference_width` 是工具标定工作点，与胚胎默认 width 解耦） |
| `home_position` / `target_position` | 初始位置 | |
| `velocity` / `max_velocity` | 0 / 10 mm/s | 当前未参与运动学，预留 |
| `path` | `[]` | 预留 |

### 5.4 状态机

**胚胎状态**（字符串值与 MATLAB 完全一致，便于日志对照）：

```mermaid
stateDiagram-v2
    [*] --> free
    free --> clustered: 初始化聚类检测，之后不再参与选择
    free --> selected: select_nearest_free
    selected --> free: grasp 失败 (attempts<3)
    selected --> failed: grasp 失败 (attempts>=3)
    selected --> grasped: grasp 成功
    grasped --> moved: release
    moved --> [*]
    failed --> [*]
    clustered --> [*]
```

> 行为注记：`clustered` 状态的胚**不会被选中**（选择条件为 `state == "free"`，聚类检测在循环开始前执行）。此为 MATLAB 现行为，先保真移植，见 §16-①。

**工具状态**（主流程实际使用链）：

```text
home → aboveEmbryo → grasped | failedGrasp → aboveMovedPosition → released → … → home
```

另有遗留状态 `lifted`（`raiseTool`）、`contact` / `placeContact`（`lowerTool*`，主循环未调用）。全部保留在枚举中，其中 `lowerTool*` 标注为 legacy。

### 5.5 运动日志 MotionLog

| 数组 | 形状 | 内容 |
|---|---|---|
| `positions` | `(N,3)` | 工具位置 |
| `rotation` | `(N,3)` | ZYX 欧拉角 (roll, pitch, yaw)，含万向锁回退分支 |
| `tool_state` | `(N,)` | 工具状态字符串 |
| `move_yaw_changes` | `(M,1)` | 每次 `move_tool` 调用各记录一次 \|最短角差\| |

---

## 6. 计算核心模块

> 分层布局：`math` → `models` → `setup` → `sim` → `reporting`，依赖只向下；各子包 `__init__.py` 转发导出公开 API（跨子包引用一律走公开 API，如 `from mrex_perception.core.models import Embryo`）。`core/engine.py`（M3，顶层）负责编排 `sim` 中的行为。

### 6.1 `core/math/geometry.py`

```python
def pixel_to_workspace(x_pixel, y_pixel, image_width, image_height, workspace) -> np.ndarray:
    sx, sy, sw, sh = workspace.source_region
    x = sx + (x_pixel / image_width) * sw
    y = sy + ((image_height - y_pixel) / image_height) * sh
    return np.array([x, y, 0.1])
```

### 6.2 `core/setup/embryos.py`

- `populate_random(count, workspace, rng, spec=None)`：源区域内均匀采样，与已放置胚距离 ≥ `spec.min_spacing`（`spec: EmbryoSpec`，默认镜像 `config/embryo/default.yaml`；最多 1000 次尝试，超限取最后候选——对齐 MATLAB 的 best-effort 行为）；几何取自 spec。
- `from_detections(records, workspace, spec=None)`：置信度过滤 `≥ spec.min_confidence`；`yaw = -theta`；空结果返回 `[]` 并告警；几何取自 spec。
- `mark_clustered(embryos, threshold=1.0)`：两两距离（仅 xy 平面）< `threshold` 时双方 `is_clustered=True`、`state="clustered"`（引擎传入 `EmbryoSpec.cluster_threshold`；注意：与 MATLAB 相同，无条件覆盖 state）。

### 6.3 `core/sim/planner.py`

- `has_free_embryos(embryos) -> bool`
- `select_nearest_free(embryos, target_point)`：对 `free` 状态按 3D 距离取最近（`target_point` 默认 `[50, 50, 0.1]`，仅用于排序）。
- `next_moved_position(embryos, workspace)`（对齐 `getMovedPosition.m`）：

```text
moved_count = 已 moved 数量
spacing     = embryo.length × moved_spacing         # 0.5 × 4 = 2.0 mm
num_cols    = floor(region_width / spacing)         # floor(45/2) = 22
col         = moved_count % num_cols
row         = moved_count / num_cols
x = x_start + spacing/2 + col·spacing
y = y_start + spacing/2 + row·spacing
z = embryo.height/2                                  # 0.1 mm
```

边界：`y + spacing/2 > y_start + region_height` → 抛"落位区满"错误；`num_cols < 1` → 抛错。

### 6.4 `core/sim/motion.py`（核心：`move_tool`）

语义（逐行对齐 `moveTool.m`）：

```text
start_pos, start_R  = tool.pose
start_yaw           = atan2(R[1,0], R[0,0])
target_yaw          = target_rotation（标量 yaw 或 3×3 矩阵，二选一）
d_yaw               = wrap_to_pi(target_yaw - start_yaw)   # 最短角
log.move_yaw_changes.append(abs(d_yaw))

for k in 1..num_steps:
    if stop_token.is_set(): break
    alpha = k / num_steps
    tool.position    = (1-alpha)·start_pos + alpha·target_pos
    yaw              = start_yaw + alpha·d_yaw
    tool.orientation = Rz(yaw)
    tool.pose        = 组装
    if tool.has_embryo:
        embryo.position    = tool.position - [0, 0, clearance]
        embryo.orientation = tool.orientation      # 胚随工具旋转
        embryo.pose        = 组装
    log.record(tool)
    on_step()                                      # ← 引擎注入：发布快照
tool.target_position = target_position
```

派生函数：
- `move_tool_to_embryo`：目标 = 选中胚位置 + `[0,0,clearance]`，目标朝向 = 胚朝向；结束置 `aboveEmbryo`。
- `move_tool_final`：目标 = `moved_position + [0,0,clearance]`，朝向保持当前；结束置 `aboveMovedPosition`。
- `raise_tool`：目标 = 当前位置 + `[0,0,clearance]`，朝向保持；结束置 `lifted`。
- `return_home`：目标 = `home_position`，朝向回到单位阵；结束置 `home`。
- `lower_tool` / `lower_tool_moved`：**legacy，主循环不调用**，保真移植但不接入。

> Python 版 `move_tool` 以 `on_step` 回调 + `stop_token` 参数替代 MATLAB 中直接调用 `updateSimulation` / `simulationStopped`，保证 core 零 UI 依赖。

### 6.5 `core/sim/grasping.py`

```text
pickup_probability(embryo, tool):      # 系数全部来自 tool（config/tool_head/*.yaml）
    p = tool.base_probability × (embryo.width / tool.reference_width)
        − tool.attempt_penalty × embryo.attempts
    return clamp(p, 0, 1)
    # 默认值 0.7 / 0.2 / 0.05 与 MATLAB pickupModel.m 逐项一致

grasp(embryos, tool, rng, pump):
    attempts += 1
    success = rng.random() < pickup_probability(selected, tool)
    if success: has_embryo=True; attached_id=id; 双方 state="grasped"; picked_successfully=True
    else:
        has_embryo=False; tool.state="failedGrasp"
        embryo.state = "failed" if attempts >= tool.max_attempts else "free"
    （硬件模式才与泵交互：先 "stop"）

release(embryos, tool, moved_position, pump):
    if not tool.has_embryo: 告警返回
    if not simulation: pump.dispense(2.7)              # releaseWithPump(pump, 2.7)
    embryo.orientation = Rz(π/2)                        # 固定最终朝向
    embryo.position    = moved_position
    embryo.state       = "moved"
    tool.has_embryo=False; attached_id=0; state="released"
```

### 6.6 `core/sim/motion_log.py`

`record_tool_motion(tool)`：ZYX 提取 roll/pitch/yaw，含 `|cos(pitch)| ≤ 1e-8` 时的万向锁回退分支（逐行对齐）。追加 `positions/rotation/tool_state`。

### 6.7 `core/reporting/summary.py`

`compute_summary(embryos, motion_log) -> SummaryReport`，字段与 `simulationSummary.m` 输出**一一对应**（UI 表格/导出 JSON 复用同一数据类）：

- 计数：`total / moved / grasped / selected / failed / free`、`total_attempts`、`successful_pickups`、`average_attempts`、`success_rate`（分母 `moved + failed`）；
- 位置：start/final/min/max/range；
- 距离：总/最小/最大/平均步长（排除 < 1e-9 的静止段）；
- 旋转：`np.unwrap` 后计算 cumulative / net / min / max / range / total angular motion；yaw 调整的 max/mean（来自 `move_yaw_changes`）。

格式化（`fprintf` 风格）移入 `ui` 或导出层，core 只产出数值。

### 6.8 `core/engine.py`

`SimulationEngine` 是 `runSimulation.m` 主循环的等价物：

```text
setup:
    workspace = load_workspace(config_name)
    embryos   = source.detect(...)          # random 或 yolo(占位)
    embryos   = mark_clustered(embryos)
    tool      = injected_tool              # 必填(kw-only)注入；如 config.tool.to_tool_head(workspace)
    log       = MotionLog(); log.record(tool)
    emit(phase="Initial workspace")

loop while has_free_embryos(embryos) and not stop:
    embryos = select_nearest_free(embryos, target_point)
    move_tool_to_embryo(...)          → emit(phase="Tool above selected embryo")
    grasp(...); log.record(tool)
    if not tool.has_embryo:
        raise_tool(...); continue
    emit(phase="Embryo grasped")
    moved = next_moved_position(embryos, workspace)
    move_tool_final(...)              → emit(phase="Tool above moved position")
    release(...); log.record(tool)
    emit(phase="Embryo released")

if stopped: return FinishReason.STOPPED        # 不回位、不产汇总（对齐 MATLAB）
return_home(...)
report = compute_summary(embryos, log)
return FinishReason.COMPLETED
```

引擎参数（`EngineParams`）：

| 参数 | 默认 | 对应 |
|---|---|---|
| `mode` | `simulation` | `hardware.isSimulation` |
| `num_steps` | 50 | `numSteps` |
| `target_point` | `[50, 50, 0.1]` | `targetPoint` |
| `phase_hold_seconds` | 0.2 | 阶段暂停 `pause(0.2)` |
| `show_ids` / `show_arrows` | False | 渲染选项（UI 侧消费） |
| `rng_seed` | None | 可复现实验 |
| `min_confidence` | 0.8 | YOLO 过滤 |

停止语义：`stop()` 置 `threading.Event`；`move_tool` 每个插值步检查（与 MATLAB 逐步检查一致），停止延迟 ≤ 1 步。

> ✅ 2026-10-04（M3）：已实装于 `core/engine.py`（`SimulationEngine` / `EngineParams` / `Snapshot` / `FinishReason`）与 `mrex_perception/cli.py`。停止检查点与 MATLAB 完全一致（仅循环顶 + 插值步内），停后当前迭代的抓取/释放仍会执行（见 §16-⑪）；暂停/单步留待 M4 worker 在 `on_step` 钩子处阻塞实现。构造器要求 keyword-only `tool` 注入（如 `ToolHead.for_workspace(workspace)`；实例原地使用，调用方负责初始化 `home_position`/`target_position`；缺省自建已移除）；`core/setup/tool.py` 已删，创建逻辑并入模型类方法。
>
> **M3 检视（2026-10-04）**：`_hooks()` 字典间接层改为 `_move()` 统一注入（删除 `typing.Any`）；`LoggableTool` 协议与 `getattr(..., "unknown")` 兜底删除，`MotionLog.record` 直接接收 `ToolHead`；选中胚查找统一为 `planner.find_selected`（motion/grasping 共用，行为同 MATLAB 首个匹配）；`move_tool_final` 参数序对齐为 `(embryos, tool, num_steps, motion_log, moved_position, ...)`；CLI 停止判定合并为单一 `summary is None` 分支。50 用例保持全绿。

---

## 7. 线程模型

仿真运行于 `SimulationWorker(QThread)`，渲染与全部 widget 操作固定在 UI 主线程；两线程之间只传**不可变快照**（latest-wins 覆盖式缓冲，而非逐事件信号），结果经信号送回。`core/**` 零 Qt 依赖，CLI 与 GUI 走同一代码路径。

线程边界、快照泵与节流、暂停/单步/停止、关窗流程等实现细节见 [`ui-architecture.md`](./ui-architecture.md) §7、§10。

---

## 8. 可视化层

三视图（Top/Front/Right 正交）与场景渲染由 `ui/viewport/` 实现，窗口与仪表盘布局由 `ui/main_window/`、`ui/dashboard/` 承载；布局速览、场景元素/状态颜色、渲染策略与截图导出全部见 [`ui-architecture.md`](./ui-architecture.md) §4。

---

## 9. 仪表盘与交互

运行控制、参数、遥测与图表控件见 `ui/dashboard/`；菜单动作、信号接线与状态栏见 `ui/main_window/`；完整控件清单与接线表在 [`ui-architecture.md`](./ui-architecture.md) §4.4、§7。

---

## 10. 检测接口（YOLO 占位）

### 10.1 接口定义

```python
# mrex_perception/detection/base.py
class EmbryoSource(Protocol):
    def detect(self, workspace: Workspace) -> list[Embryo]: ...
```

- `RandomSource(count, seed)`：**当前可用**，等价 `populateEmbryos.m`。
- `YoloSource(image_path)`：**占位**——构造函数接受路径，`detect()` 抛 `NotImplementedError("YOLO integration pending (M5)")`；UI 上以禁用态提示。

### 10.2 未来接入路径（M5 决策点）

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| A. 子进程 + CSV（对齐现状） | 移植 `runYOLO.m` 逻辑：调用 `python/` 下虚拟环境的 `extract_obb_data.py`，读回 CSV 交给 `from_detections` | 与 MATLAB 完全同构；YOLO 环境与主程序隔离 | 需管理外部解释器路径 |
| B. 同进程 `ultralytics` | 惰性 import + 启动预热；推理放独立 worker 线程 | 部署简单、无 IPC | 打包体积大；AGPL-3.0 许可需评估；GIL 影响需实测 |

CSV 契约（两种方案共用，保持与现有脚本一致）：

```text
image, image_width, image_height, class_id, confidence, x, y, width, height, theta
```

> 注：Ultralytics YOLOv8 为 **AGPL-3.0** 许可，若未来闭源分发需确认授权策略。

---

## 11. 硬件抽象

```python
# mrex_perception/hardware/base.py
class PumpDriver(Protocol):
    def flush(self) -> None: ...
    def command(self, text: str) -> None: ...        # 透传命令
    def dispense(self, volume_ml: float) -> None: ... # 注入（corresponds to releaseWithPump 前半段）
    def withdraw(self, volume_ml: float) -> None: ... # 回抽（后半段）
```

- `SimulatedPump`：空操作、**不做 sleep**（仿真模式不允许真实等待；对齐 MATLAB：仿真时不调用泵函数）。
- `SerialPump(port, baudrate=115200, terminator="\r", timeout=3)`：pyserial 实现；命令集与 `releaseWithPump.m` 一致：

```text
stop / cvolume / irate <r> ml/min / tvolume <v> ml / irun
stop / cvolume / wrate <r> ml/min / tvolume <v> ml / wrun
```

- 释放序列常量：`rate = 20 mL/min`、`release_volume = 2.7 mL`、等待 `move_time+1s` / `move_time+2s`（仅硬件模式）。
- 行为边界：所有阻塞等待只允许发生在 worker 线程；断线重连与错误提示列入 M6。

---

## 12. 配置系统

| 层 | 文件 | 内容 |
|---|---|---|
| 工作区 | `config/workspace/*.yaml` | §5.1 字段（snake_case 键） |
| 胚胎模板 | `config/embryo/*.yaml` | 批次几何（shape/width/length/height）+ detection/clustering/placement 阈值 → `EmbryoSpec` |
| 工具头 | `config/tool_head/*.yaml` | 本体/交互面几何、adhesion 抓取系数、clearance/home_offset 等 → `ToolHeadConfig` 工厂 |
| 应用默认 | `config/app.yaml`（新增，可选） | mode、source、num_steps、target_point、phase_hold、seed、主题 |
| 场景/回放 | `tests/fixtures/*.json`（已移除） | 原固定场景 JSON 随对照套件精简删除；如 UI 回放需要可另行重建 |

优先级：CLI/UI 显式传参 > `app.yaml` > 代码内默认值。YAML 解析用 PyYAML；工作区模型用 pydantic 校验（保证错误信息可读）。

聚合注入（2026-10-06 实装，2026-10-08 扩展）：`config/app.py::AppConfig`（A 方案）聚合已校验的三段——`workspace` / `embryo` 为 core 数据对象，`tool` 为 `ToolHeadConfig` 工厂（tool 有状态，运行时 `to_tool_head(workspace)` 现场构造单个实例）。入口层用 `load_app_config()` 装配后注入 `MainWindow`；`list_workspace_configs()` 枚举 `config/workspace/*.yaml`，GUI 的 Config 菜单据此支持运行时切换（`MainWindow.apply_config`；运行中禁用，切换后下一次运行生效）。读取载入的完整链路、约定与扩展指南见 [`config-system.md`](./config-system.md)。

---

## 13. 依赖清单

| 包 | 用途 | 许可证 | 备注 |
|---|---|---|---|
| `numpy` | 全部数值计算 | BSD | |
| `PySide6` | GUI 框架 | LGPL-3.0 | 商用友好 |
| `pyvista` | 3D 网格与场景 | MIT | 依赖 `vtk` |
| `pyvistaqt` | Qt 嵌入多视口 | MIT | |
| `pyqtgraph` | 实时曲线/图表 | MIT | 替代 matplotlib |
| `PyYAML` | 配置解析 | MIT | |
| `pydantic` | 配置校验 | MIT | 可降级为手写校验 |
| `pyserial` | 串口（M6） | BSD | |
| `ultralytics` + `torch`（M5） | YOLO | AGPL-3.0 | 仅 CV 构建包含 |
| 开发 | `pytest` / `pytest-qt` / `ruff` / `mypy` | | |

**Python 版本建议 3.12**（3.13 对 VTK/torch 轮子的兼容性需实测）。建议根目录建 `.venv`；`python/.venv`（YOLO 工具链）在 M5 再决定合并或保持独立。

---

## 14. 打包部署（概览，详见迁移计划 M7）

- 工具：PyInstaller `--onedir`（启动快、排查易）；收集规则：`--collect-all vtkmodules --collect-all pyvista --collect-all pyvistaqt --collect-all pyqtgraph`；CV 构建追加 `--collect-all ultralytics`（torch 需按其官方指引收集）。
- 构建分级：
  - **Sim 构建**（不含 torch/ultralytics）：预计 400–800 MB；
  - **Full-CV 构建**：预计 1.5–2.5 GB。
- macOS/Windows 分别出包；`models/` 与 `config/` 作为外部资源随包发布（便于替换模型与配置）。

---

## 15. 测试策略

| 层级 | 内容 |
|---|---|
| 单元测试 | 每个 `core` 模块；随机源用固定 seed；抓取成功/失败路径用可控 RNG（注入 stub generator 或 outcome provider 强制成功/失败） |
| 数值对齐 | 固定场景 fixture：MATLAB 与 Python 双端跑同一输入，输出 JSON 逐字段对比（容差 1e-9）；详见迁移计划 §7 |
| 引擎测试 | 无头跑通全流程；停止语义（在步间置停）、落位区满、无可用胚等边界 |
| UI 集成 | `pytest-qt`：worker 生命周期、GUI 结果 == 无头、截图导出等（详见 `ui-architecture.md` §12） |
| 性能预算 | 6–50 胚胎下 ≥ 50 FPS；Stop 响应 ≤ 200 ms；启动 ≤ 3 s（不含 YOLO） |

---

## 16. 已知行为与待确认项（移植保真清单）

| # | 现象 | 现行为 | 建议 |
|---|---|---|---|
| ① | `clustered` 胚胎永不参与选择 | 主循环只选 `free` | 确认是否符合实验意图；如需要"先处理聚类"另开需求 |
| ② | `moved_region` 越界 quirk：旧值 `[80,5,100,25]` 的 x 范围 80→180 超出 `size[0]=100`（MATLAB 默认值遗留） | 已消除（2026-10-06 起不再对齐 MATLAB 默认值，改为 `[40, 5, 45, 30]`，落在工作区内） | 完成 |
| ③ | `lowerTool.m` / `lowerToolMoved.m` 调用 `moveTool` 时参数错位（少传 `targetRotation`），且 `lowerTool.m` 还有拼写错误 `attaachedID`；主循环未调用 | 死代码，从未可运行 | 已删除（2026-10-04 M2 检视：修正版 Python 移植无调用方，连同 `record_tool_motion` 包装一并清理） |
| ④ | MATLAB `rand` 与 numpy RNG 序列不同 | — | 双端对齐只针对确定性部分；随机部分用"固定输入 fixture + 强制结果"策略 |
| ⑤ | 释放后胚胎朝向固定 `yaw=π/2`，不可配置 | 硬编码 | 先保真；后续提出可配置参数 |
| ⑥ | `success_rate` 分母是 `moved+failed`（不含 free/clustered 残留） | 对齐 `simulationSummary.m` | 保真；UI 上同时显示"剩余未处理"避免误读 |
| ⑦ | 工具初始位置由 `source_region` 推导（非工作区中心） | `[15, 17.5, 10]` | 保真 |
| ⑧ | `moveTool` 每步全量重绘（MATLAB `clf`） | 卡顿来源 | Python 端天然解耦，渲染在 UI 线程按帧率刷新 |
| ⑨ | `velocity/max_velocity/path` 字段存在但未参与运动学 | 预留 | 保留字段 |
| ⑩ | `contact_radius`、`surface_height`、材料参数未参与当前计算 | 预留 | 保留字段 |
| ⑪ | 停止请求只在主循环顶部与 `moveTool` 插值步内被检查 | 停后当前迭代仍会执行 grasp/release（剩余移动立即 break），随后返回 STOPPED | 保真（engine）；停后不回位、不产汇总，见 §6.8 |

---

## 17. 关键决策记录（ADR-lite）

| # | 决策 | 理由 |
|---|---|---|
| D1 | 采用 Python 全栈而非 MATLAB/混合 | 摆脱 MATLAB 运行时；与 YOLO 工具链同语言；可打包 |
| D2 | PySide6（Widgets）而非 QML | 与 VTK 嵌入/仪表盘开发成本最低；QML 动效非硬需求 |
| D3 | PyVista/VTK 而非 pyqtgraph.opengl | 多视口、正交投影、网格能力成熟；Rhino 式布局开箱即用 |
| D4 | 快照 + latest-wins 而非逐事件信号 | 杜绝队列积压；线程边界清晰 |
| D5 | `mrex_perception/core` 零 Qt 依赖 | 可无头测试、可换 UI、可被 CLI/批处理复用 |
| D6 | 工作区 YAML 键名统一 snake_case（不再与 MATLAB 共用同一文件） | Python 属性同名 + pydantic 原生校验；双端对照期已结束，无复用需求 |
| D7 | ID 保持 1-based | 与 MATLAB 日志/文档一致，减少对照成本 |
