# tests — 测试说明

> 单元测试 + MATLAB 双端对齐测试。运行：`.venv/bin/python -m pytest`（`pyproject.toml` 已配置 `testpaths = ["tests"]`）。

## 目录结构

```text
tests/
├── core/                    # 与 mrex_perception/core 分层一一对应
│   ├── test_math.py         # 变换（rotation_z / make_pose）+ 像素→工作区映射
│   ├── test_setup.py        # 随机布置 / 检测转换 / 聚类标记 + 工具创建
│   ├── test_motion.py       # move_tool 及包装函数 + MotionLog / ZYX 提取
│   ├── test_planner.py      # 选择与落位网格（getMovedPosition）
│   ├── test_grasping.py     # 抓取概率 / 成败路径 / 释放
│   └── test_summary.py      # 统计汇总（对齐 simulationSummary.m）
├── fixtures/                # 固定场景（双端对照共用）
│   └── scenario_basic.json  # 默认工作区 + 显式 6 胚（位置/朝向/attempts 全部给定）
├── matlab/                  # MATLAB 侧 parity 工具（见下节）
├── test_config.py           # config loader + workspace YAML 校验
├── test_parity.py           # MATLAB ↔ Python 双端 1e-9 数值对齐
└── test_smoke.py            # 应用导入/启动冒烟
```

## `tests/matlab/` 是什么

M2 引入的**双端数值对照**基础设施：让 Python 移植代码与冻结的 MATLAB 参考实现（`src/**`）在同一输入上逐字段对齐（容差 1e-9）。

| 文件 | 作用 |
|---|---|
| `dumpFixture.m` | 读 `fixtures/scenario_basic.json`，用冻结的 `src/**` 逐步执行（轨迹 / 网格 / 抓取 / 释放 / 整段主循环），导出 `trace_m2.json`。抓取随机性通过种子搜索固定，并把实际消耗的 `rand` 值一并导出，供 Python 侧回放同一成败路径。 |
| `updateSimulation.m` | 渲染阴影：dump 时本目录排在 `src` 之前，把 `clf / drawnow / pause` 换成 no-op（可逐帧录制），保证无头运行。**不修改 `src/**`**。 |
| `trace_m2.json` | 生成的 MATLAB 参考 trace（已入库）；`tests/test_parity.py` 读取它逐字段对比。 |

重新生成（仅在 fixture 或对齐范围变化时）：

```bash
/Applications/MATLAB_R2026a.app/bin/matlab -batch "cd tests/matlab; dumpFixture"
```

> MATLAB 不在 PATH，需用完整路径（本机为 R2026a）；启动约 30–60 s。生成后连同 `trace_m2.json` 一起提交。
