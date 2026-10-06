# TaskDescriptor 导出通道 —— 工程实装说明

> 版本: v0.1（草案） · 日期: 2026-10-06 · 状态: 待实装
>
> 上游规范（数据契约权威）: 工程院 Vault《3. TaskDescriptor 数据接口规范》v0.2.0
> 下游用途: A 段 → B 段的型综合输入（螺旋系 + 量化指标）
> 相关: [`python-architecture.md`](./python-architecture.md) · [`migration-plan.md`](./migration-plan.md) · Vault《4. 任务-机构自动生成最小技术展示规划（MVP）》§3–S1

本文档把 Vault 中的数据契约落地为 `mrex_perception` 的**可编码规格**：新增一个导出适配器，把引擎产物转成符合 v0.2.0 schema 的 `TaskDescriptor` JSON。它是 A↔B 段的边界层，不属于 `core/`。

---

## 1. 定位与依赖方向

| 项 | 约定 |
|---|---|
| 模块路径 | `mrex_perception/export/task_descriptor.py`（与 `config/` 同级，边界层） |
| 依赖方向 | `export → core`（只读消费）；`export` 不依赖 Qt / VTK；`core` 不反向依赖 `export` |
| 数据契约 | 输出符合 Vault《3. TaskDescriptor 数据接口规范》§7 的 JSON Schema 0.2.0 |
| 校验 | `jsonschema` 校验；失败抛 `ValueError`（错误信息含首个不合规路径） |
| 版本常量 | `TASK_DESCRIPTOR_SCHEMA_VERSION = "0.2.0"` |

理由：`core` 零 Qt、可无头；导出器只读 `EngineResult`，天然可被 CLI 与批处理复用（与 `cli.py` 同层）。

---

## 2. 前置改造：引擎暴露阶段时间线（G6）

现状：`core/engine.py::SimulationEngine._set_phase(title)` 只回调 `on_phase(title)`，无索引；导出器无法定位「第 k 帧属于哪个 phase」。

改动（最小侵入）：

```text
# core/engine.py
class EngineResult:            # 新增字段
    ...
    phase_timeline: list[tuple[str, int]]   # [(phase_title, step_index), ...]

class SimulationEngine:
    def __init__(...):
        self._phase_timeline: list[tuple[str, int]] = []

    def _set_phase(self, title: str) -> None:
        self._phase = title
        self._phase_timeline.append((title, self._step_index))   # 新增
        if self._on_phase is not None:
            self._on_phase(title)
        self._publish()
```

不改动既有行为与快照语义；单测补充 `phase_timeline` 断言。

---

## 3. 导出器 API

```python
# mrex_perception/export/task_descriptor.py
TASK_DESCRIPTOR_SCHEMA_VERSION = "0.2.0"

def build_task_descriptor(
    result: EngineResult,
    workspace: Workspace,
    *,
    task_id: str,
    config_name: str,
    seed: int | None = None,
    task_class: str = "orient",
    step_seconds: float = 1.0 / 60.0,   # 时间基（G7 占位）
) -> dict:
    """把一次引擎运行转成 TaskDescriptor JSON 可序列化字典。"""

def validate_descriptor(descriptor: dict) -> None:
    """对照 schema 0.2.0 校验；不合规抛 ValueError。"""
```

`build_task_descriptor` 内部步骤：

1. `frames` ← 常量 + `workspace` 派生（`world="workspace"`, `ee_frame="tool_tip"`）。
2. `trajectory` ← 遍历 `MotionLog` 采样，逐帧组装 `t / T_ee / object_pose / phase / contact_state / is_essential / required_wrench`。
3. `segments` ← 由 `phase_timeline` 生成（每个 phase 一段）。
4. `task` ← `{class, granularity_level: 2, phases_order: 去重顺序}`。
5. `meta` ← `schema_version / task_id / source="sim" / provenance / units`。
6. `validate_descriptor(...)`；返回。

---

## 4. 字段映射表（core → descriptor）

| descriptor 字段 | 来源 | 状态 |
|---|---|---|
| `meta.provenance.finish_reason` | `EngineResult.finish_reason` | ✅ |
| `meta.provenance.seed` / `config_name` | 入口层透传 | ✅ |
| `frames.*` | 常量 | ✅ |
| `task.phases_order` | `phase_timeline` 去重 | ✅（依赖 §2） |
| `trajectory.t` | 采样序号 × `step_seconds` | ⚠ 时间基占位 |
| `trajectory.T_ee` | `ToolHead.pose`（`position` + `orientation`） | ❗ 现仅 yaw（G1） |
| `trajectory.object_pose` | `Embryo.pose` | ✅ |
| `trajectory.contact_state` | `ToolState` / `EmbryoState` 推导 | ✅ |
| `trajectory.required_wrench` | 按 phase 注入（§6 表） | ❗ 需求口径（G2） |
| `trajectory.is_essential` | 按 phase 规则（§5 表） | ✅ |
| `trajectory.phase` | `phase_timeline` → phase 映射（§5 表） | ✅ |
| `segments` | `phase_timeline` | ✅ |
| `metrics` | 下游螺旋工具链回填 | ❗ 不在本模块 |

---

## 5. phase 与 is_essential 规则

| mrex 阶段 / 工具态 | descriptor phase | is_essential |
|---|---|---|
| `Initial workspace` / `move_tool_to_embryo` → `aboveEmbryo` | `approach` | false |
| `grasp()` | `grasp` | true |
| `Embryo grasped` → `move_tool_final` | `transfer` | false |
| `Embryo released` / `release()` | `place` | true |
| `return_home` → `home` | `home` | false |
| （扩展）`reorient` | `reorient` | true |
| （扩展）`puncture` / `dispense` | 同名 | true |

> `mrex_perception` 无独立 `lift` / `reorient`，`move_tool_final` 合并了「抬升 + 平移」为 `transfer`。见 Vault 规范 §5.2。

---

## 6. required_wrench 注入表（G2 占位）

| phase | `required_wrench`（局部系） | 备注 |
|---|---|---|
| `grasp` | `[0,0,-f_adh,0,0,0]` | `f_adh` 取 `adhesion_model` 参数（占位） |
| `puncture` | `[0,0,-f_p,0,0,0]` | 穿刺轴阻力（占位） |
| `dispense` | `[0,0,-f_d,0,0,0]` | 注液反力（占位） |
| `free` / 过渡 | `null` | — |

> ⚠ 这是**任务需求口径**，非物理仿真实测。文档、日志与答辩必须明示；物理化需引入参数化接触模型（后续）。

---

## 7. CLI 与批处理集成（G8）

```bash
# 单次导出
python -m mrex_perception.cli run --config default --count 6 --seed 42 \
    --export-task-descriptor out/td_orient_seed42.json

# 批量任务族（S3+）
python -m mrex_perception.cli batch --tasks orient,inject --seeds 1,2,3 \
    --out-dir out/task_descriptors/
```

`--export-task-descriptor` 在 `run` 结束后调用 `build_task_descriptor` 并落盘；`batch` 为新增子命令（可后置）。

---

## 8. 测试约定

| 用例 | 内容 |
|---|---|
| schema 合规 | 导出实例过 0.2.0 schema |
| 往返 | `to_dict → 再校验` 逐字段一致 |
| 总账一致 | `trajectory` 中 moved 数 == `summary.moved`；段数 == 阶段事件数 |
| 真值分离 | `is_essential=True` 帧集合 == 确定性 phase 集合 |
| 无头 | `import mrex_perception.export` 不引入 Qt / VTK |

---

## 9. 里程碑衔接

| 阶段 | 本模块相关交付 |
|---|---|
| **S1** | 本模块 + 引擎阶段时间线；用现有 3-DOF 数据先跑通「导出 → 校验」 |
| **S2** | `T_ee` 升级为 6-DOF（`core/sim/motion.py` 四元数插值）后，本模块无需改接口 |
| **S3** | 新增 `inject` 任务类；`required_wrench` 注入表扩充 |

> 详见 Vault《4. 任务-机构自动生成最小技术展示规划（MVP）》§3、§5。
