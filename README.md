# English Study Repository

这个项目用于存储和复习日常英语对话中的核心词汇、语法和实用句型。

## 目录
- [2026-01-29 复习计划](Review_Plan_2026-01-29.md): (TBD)
- [2026-01-28 复习计划](Review_Plan_2026-01-28.md): 涵盖了“把内容更新进文件”的地道表达（update the file with / put into / add to）、all of this vs all of these、wiring is a mess 的吐槽与追因、sub-workflow/show up/archived、owe vs own 与 do miss 的强调用法，以及 Starbucks 咖啡讲解口语（logo/worldwide/coffee bean/roast/caffeine/decaf/stopper/package/label/trace origin）。
- [2026-01-27 复习计划](Review_Plan_2026-01-27.md): 涵盖了工作流/Google Sheets 排错表达、status/update/sync 高频纠错、表单与文档沟通、点餐词汇与金额读法。
- [2026-01-26 复习计划](Review_Plan_2026-01-26.md): 涵盖了 API key 创建表达、错误排查、工作流与表格状态更新等场景。
- [2026-01-25 复习计划](Review_Plan_2026-01-25.md): 涵盖了探索表达、水果词汇、情绪表达、日常场景等。
- [2026-01-24 复习计划](Review_Plan_2026-01-24.md): 涵盖了 GS25 购物、微波炉使用、餐具索取等场景。
- [2026-01-23 复习计划](Review_Plan_2026-01-23.md): 涵盖了购物、问路、服装描述等核心场景。

## 学习建议
每天抽出 15-30 分钟朗读文档中的例句，并尝试在日常对话中运用。

## 自动化（不想每次都手动新建/更新）

### 方式 1：本地脚本（推荐）
在仓库根目录运行：

`powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\new-review-plan.ps1`

可选参数：
- `-Date 2026-01-29`（默认=今天）
- `-Summary "本次复盘内容摘要"`（默认写入 `(TBD)`）
- `-Commit` / `-Push`（自动提交并推送到 `main`）

### 方式 2：n8n 一键触发
1. 在 n8n 里导入工作流：`n8n/auto-create-review-plan.json`
2. 运行（Manual Trigger）即可生成当天的 `Review_Plan_YYYY-MM-DD.md` 并更新 README 目录
3. 如果你的仓库路径不同，修改工作流里 `Execute Command` 节点的脚本路径即可
