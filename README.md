# English Study Repository

这个项目用于存储和复习日常英语对话中的核心词汇、语法和实用句型。

## 目录
- [2026-02-07 复习计划](Review_Plan_2026-02-07.md): 聚焦技术与职场高频表达（bleeding edge / disclaimer / anomaly alerts / server-side logging）、餐厅全流程口语（reservation/host/menu/点餐与续水），以及主谓一致、介词搭配、时态与固定短语纠错。
- [2026-02-06 复习计划](Review_Plan_2026-02-06.md): 介词专项加强版，覆盖 16 大场景：在原有 12 个生活场景上新增动词+介词、形容词+介词、名词+介词、高频介词短语词库，并保留正确表达速记与 60 句场景口语模板（for/to、arrive at/in、pay for/by/with、log in to、recover from 等）。
- [2026-02-05 复习计划](Review_Plan_2026-02-05.md): 聚焦成就表达、楼层/电梯/扶梯与指路、过去式与序数词纠错、be interested in 结构、拍照与城市风景描述、餐饮饮品词汇及发音。
- [2026-02-04 复习计划](Review_Plan_2026-02-04.md): 聚焦小程序发布与里程碑表达、地铁换乘表达、私募/对冲/套利基金与潜在回报沟通，以及 get up/brush my teeth 等日常表达与发音纠错。
- [2026-02-03 复习计划](Review_Plan_2026-02-03.md): 聚焦 be familiar with 结构、report/reporter 区分、过去式 did/wrote、wait for、deadline/to-do list 等职场表达，并补充 UK 景点词汇（Big Ben/British Museum）。
- [2026-02-02 复习计划](Review_Plan_2026-02-02.md): 覆盖困倦表达（sleepy/beat/ready to crash）、口语对话造句、职场汇报与会议表达、商业竞争与定价（competitor/colleague/influence/one cent lower），以及结算状态表达（settlement/status/schedule），并复盘gonna/to+动词原形等语法与发音。
- [2026-02-01 复习计划](Review_Plan_2026-02-01.md): 涵盖了薄煎饼与配料词汇（pancakes / buttermilk pancakes / whipped cream / fresh berries）、职场沟通句（request parameters / provide additional information / wrap it up）、易混词辨析（propriety vs proprietary / swan vs duck）、调味与食材（green onion/scallion / coriander/cilantro），以及语法纠错（will go bad / nice and chunky / both vs neither）。
- [2026-01-31 复习计划](Review_Plan_2026-01-31.md): 涵盖了专有住宅面板表达（proprietary residential panels / residential wall panels / residential solar panels）、监控录像与真相揭露（reviewing the camera footage / reveal & uncover the truth / shocking truth）、动名词作主语与 footage 不可数用法，以及发音要点（proprietary / residential / footage）。
- [2026-01-30 复习计划](Review_Plan_2026-01-30.md): 涵盖了销售岗位表达（sales / salesperson / sales rep / I’m in sales）、车站与高铁提醒（get off / get back on / stop for 3 minutes / at this station）、口语时态与时间表达（right away vs right now / just + 过去式 / 现在完成时）、礼貌请求（get through / give me a sec / spare a minute）、点餐与夸赞表达（latte / roasted lamb / insanely beautiful），以及指路用法（turn left at + 距离）与发音易错点（hypocrites / cruel / gigawatt）。
- [2026-01-29 复习计划](Review_Plan_2026-01-29.md): 涵盖了日常寒暄与追问（What about you today? / What did you do today?）、销售岗位与发音（sales / salesperson / sales rep / I’m in sales）、手机与日常表达（install / lock screen / just saw）、高铁/车站表达（get off / get back on / stop for 3 minutes / at this station）、礼貌请求（get through / spare a minute / which one would you like）、问含义（What does it mean?）、导盲犬与训练表达（guide dog / in action / build trust）、猫咪与阳光（stretch out / soak up the warmth）、过去时纠错（started/went/watched/took），以及狗咬与医疗表达（bitten by a dog / in case of rabies / treatment）和安全应对不友好狗的表达（stick / keep ... away / back away slowly）。
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

