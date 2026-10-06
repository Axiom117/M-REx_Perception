# tests — 测试说明

> 单元测试套件（回归基线）。运行：`.venv/bin/python -m pytest`（`pyproject.toml` 配置 `testpaths = ["tests"]`）。

## 目录结构

```text
tests/
├── core/                # 与 mrex_perception/core 分层一一对应
│   ├── test_math.py     # rotation_z / make_pose / pixel_to_workspace
│   ├── test_models.py   # ToolHead.for_workspace 工厂 / pose
│   ├── test_setup.py    # 随机布置 / 检测转换 / 聚类
│   ├── test_motion.py   # move_tool 及包装函数 + MotionLog / ZYX 提取
│   ├── test_planner.py  # 选择与落位网格
│   ├── test_grasping.py # 抓取概率 / 成败路径 / 释放
│   ├── test_summary.py  # 统计汇总
│   └── test_engine.py   # 无头引擎：全流程 / 停止语义 / 落位区满 / 快照钩子
├── test_config.py       # config loader + workspace 校验 + AppConfig 聚合 / 配置枚举
├── test_cli.py          # 无头 CLI 端到端 + JSON 报告
└── test_ui.py           # M4：worker 生命周期 + 窗口运行集成（pytest-qt）
```

## 原则

- **一个行为一个测试**：同类断言合并到同一用例，只保留行为与关键边界（阈值、最短角、分支切换、报错消息）。
- 与 MATLAB 的数值对齐（1e-9）验证已于 M2 完成并固化在上述断言中；原双端对照套件（`tests/matlab/`、`test_parity.py`、`trace_m2.json`、`scenario_basic.json`）已按精简计划移除，如需找回见 git 历史（`15e2f7b`）。
