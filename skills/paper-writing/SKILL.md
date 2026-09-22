---
name: paper-writing
description: 写论文与改论文的唯一入口，按节给出每一段该写什么的模板：标题、五步摘要、三段引言加三条一句贡献、相关工作一类一段、方法框架图、实验的设置段/表的分工/主表规范/数据呈现/消融/定性图/成本、结论、附录；四条铁律（先改大纲、每句有目的有依据、引用走 bibguard、结论从数据推）；只用领域通用词、数字进表正文写方向、caption 以结论开头、浮动体间距按规则设、不用 \vspace、正文写满页限末行；附带 paperlint 门禁。**凡是动 paper 正文，哪怕一个词：先改大纲，再逐句改正文，最后跑门。** 触发词：写论文、写 paper、改 paper、摘要、abstract、introduction、related work、method、实验、conclusion、附录、appendix、润色、精简、故事线、大纲、outline、paperlint、排版、页数、caption、间距、figure、table、贡献、contributions。
---

# 写 paper 的规矩（paper-writing）

写论文与改论文的唯一入口。动正文的任何一处，哪怕一个词：先改大纲，再逐句改正文，最后跑门。

## 铁律

1. **先改大纲。** `OUTLINE.md` 记故事线和 claim → 证据表；正文的每一处改动先落在大纲，没有证据的话不写。
2. **每句有目的、有依据，否则删。** 同一件事只说一次，短的写法胜出。
3. **引用只走 `bibguard`。** 不手写 bib，不凭记忆补出处。
4. **结论从数据推。** 既有结论可以被数据推翻；改结论先改大纲，不拿结论反推实验。

## 流程

1. 读 `OUTLINE.md` 和项目笔记，把这轮要改的点先写进大纲。
2. 逐句改正文，其余原文保留；不整篇重写；作者亲手写的句子逐字保留，只把数字换成同值的宏。
3. 编译门：0 error、0 undefined、0 overfull；bibtex 在编译目录内跑；`bibguard --uncited` 为 0；paperlint HARD 为 0。
4. 逐页看 PDF：间距、裁切、禁用词（pdftotext 扫）、每个 caption 单独可读。
5. 页数最后收：内容写完再按 §5 压页；删重复，不删事实和表。
6. 提交、推远端、同步 Overleaf；给用户的 diff 只留一份，而且能编译出 PDF。

## 1. 语言

- **读者**：没有本文以外先验的人逐句能懂；每张图表单独拿出来能读出结论。
- **术语**：只用领域通用词；自创词必须定义并说明为何需要，能不用就不用；型号名只在设置段写一次，图表里不写型号。本项目曾因此全文替换过的词：generator、protocol、host、suite、segment、arm、judge、install，换成 video model、benchmark、clip、setting、evaluator、load。
- **名词统一**：方法名全文 `\textsc{}`；基线叫 Base；缩写首次给全称；指标首次说明含义与方向。
- **句子**：平直的英语；不用冒号引出解释；少逗号，不写碎句和压缩省略句；前后句要承接；不写「Hence a design principle」这类空话。
- **语域**：各节用审稿人熟悉的常规写法（We propose… / Extensive experiments show…）；段落小标题短而平实。
- **符号**：使用前定义，用领域最常见的写法；多行推导收成命题，证明进附录。
- **不引用代码**：文件路径、脚本名、命令行参数不进正文；可复现性只写「发布了什么」。
- **自信**：局限只在结论段写；正文与附录不写削弱自己证据的话。

## 2. 数字与证据

- 数字进表，正文写方向：「在哪个基准上把哪个指标提高了多少点」；不写裸数字，不写「Δ [lo, hi]」。
- 所有数字来自生成的宏，不手抄；表里不放 n 之类没有信息量的列。
- 每个观点后面跟着依据：表号、命题号或引用。
- 摘要和贡献只放 2–3 个最能打的数字。
- 评价用两个不同权重家族的自动评委互证并报一致率，不做真人评分。

## 3. 逐节模板

**标题**：场景关键词 + 方法特点（如 training-free）+ 短而可记的方法名；不造名词。

**摘要**（≤ 300 词，顺序固定，无冒号）：① 这类系统怎么工作、做不到什么；② 由此带来的两个问题，一个随生成时间恶化，一个关于长程记忆；③ 提出 training-free 的 X，区别于主流的 Y；④ 用什么手段解决了什么，不展开机制；⑤ 在哪些基准、哪些模型上评测，2–3 个数字。

**引言**（三段 + 贡献 + 一张小图）：段 1 背景；段 2 把摘要的两个问题具象化；段 3 思路、动机、为什么这样做，段末一句结果总述。贡献写 `Our contributions are summarized as follows.` 加三条各一句，不加粗，不写 To our knowledge：① 第一个做到什么、为何重要；② 提出具体机制 A，解决具体问题 B；③ We evaluate X on … benchmarks and … models, achieving …。

**相关工作**：每类一段，段首一句说明类别及与本文的关系；主线按发展脉络从奠基工作讲到现状，每句对照所引论文的摘要核对；末段写最接近的工作与区别，对手的机制只在这里讲；配一张小图。

**方法**：首段一句定义问题与手段；一张框架图，真实画面加框架，核心决策在图里可见，每个字斟酌，详细流程图进附录；关键操作给公式，符号与图一致。

**实验**：
- 设置段：基模、基准、指标（定义、方向、出处）、评委、超参数进表；对比方法带引用。
- 表的分工：每张表证一个角度（画质、记忆召回、场景切换与更长视频、消融、成本），互不重复；对比只收已发表的同方向 SOTA，预印本进附录。
- 主表：Base 与 +Method 成对，+Method 行浅灰底；加粗 = 每列最优；完整评测，不留 N/A；各表格式一致，`\scriptsize`、自然宽度。
- 数据呈现：正文只放整体明显占优的表，个别格可以输；整列无优势才进附录；结果反常先查口径和实现，查实仍不利就如实进附录，不改数字。
- 每段一个短标题，段内写方向 + 表号 + 附录指针；对比段只写「与 X 比，结果 Y」。
- 消融：两块，把核心部件换成固定规则、逐一去掉部件；只用 † 标区间不含零的损失，不加粗。
- 定性大图：先按规则筛 case，再在印刷尺寸下肉眼定；一个模型至少两个不同角度的 case（如人物一致性和场景一致性）；画全部 clip，按评委记录画绿/红框；不用崩坏的 case。
- 成本：分清生成路径上的开销和能并行隐藏的开销，各给秒数；面向实时时写清哪部分藏在生成之后。

**结论**：方法与证据；为什么重要；局限与未来工作连写。正文恰好写满页限的最后一行。

**附录**：只做补充，正文不带附录也是完整论文；顺序服从正文，每节首句说明补充哪张表或哪一段；与正文重复的数字用同一个宏；删削弱正文的内容；≤ 20 页；`\clearpage` 另起一页，标题含论文标题（用与 `\title` 同一个宏）；图表按附录节重编号（`\counterwithin`）；每节前 `\FloatBarrier`，浮动体 `[htbp]`。

## 4. 图表

- **图**：画布 `\linewidth`；印刷尺寸下可读；每方法一色且全篇一致；对比图一眼看出谁好、越大还是越小更好；框架图用真实帧。
- **表**：沿某个轴变化的量画成曲线；小表用 wraptable 嵌在段首，离页底至少一个表高。
- **caption**：`\textbf{一句结论式 highlight.}` 加画的是什么、单位与方向、加粗/底色/符号的含义、附录指针；写具体，不写抽象标签。

## 5. 版面

- 模板的字体与间距不动；不用 `\vspace`。
- **浮动体间距是反复犯的错。** 默认值让 caption 贴死图表（表的 caption 到 `\toprule` 是 0 pt）而图表离正文 20 pt，看上去图表嵌在 caption 里、外面一片白。规则：caption 与图表之间 7 pt，图表与正文之间 10 pt，两者接近；表的 caption 在上、图的在下，wraptable 和 wrapfigure 要单独设，否则不生效：

```latex
\usepackage{etoolbox}
\setlength{\textfloatsep}{10pt plus 1pt minus 1pt}
\setlength{\floatsep}{9pt plus 1pt minus 1pt}
\setlength{\intextsep}{9pt plus 1pt minus 1pt}
\AtBeginEnvironment{table}{\setlength{\abovecaptionskip}{0pt}\setlength{\belowcaptionskip}{7pt}}
\AtBeginEnvironment{wraptable}{\setlength{\abovecaptionskip}{0pt}\setlength{\belowcaptionskip}{7pt}}
\AtBeginEnvironment{figure}{\setlength{\abovecaptionskip}{7pt}\setlength{\belowcaptionskip}{0pt}}
\AtBeginEnvironment{wrapfigure}{\setlength{\abovecaptionskip}{7pt}\setlength{\belowcaptionskip}{0pt}}
```

- 量而不猜：200 dpi 渲染后按行统计空白段长度核对间距；图宽和 trim 按墨迹范围量。
- 正文写满最后一行：用 `\raggedbottom` 副本量末行 y；末行只落在离散位置；图表高度一变就重填；跨页的末段会触发 widow 留一行空白，让它在页内结束。
- 差几行的收法按顺序：float 间距 → `\bibsep` → 删末行只有 1–5 个词的段落里的重复句；事实和表永远最后。先分清 text-bound 还是 float-bound：半空的 float 页吃掉删掉的散文时，收 float 或合并相邻图，删字没用。

## 6. 迭代

- 审稿意见先核实再接受；每条要么改，要么把反驳理由写清楚。
- 用户在 diff 上的批注逐条落实；每轮汇报改了什么、没改什么、为什么。
- 写作会话不跑新实验，先在已有数据里找可优化的呈现；数据、表、图由实验会话按生成器出，正文不手改生成文件。

## 7. 门与自检

```bash
P=.claude/skills/paper-writing/scripts/paperlint.py
python3 $P main.tex --outline OUTLINE.md --acronyms-ok .paperlint_acronyms   # 退出码 = HARD 条数，须 0
```

规则表见本目录的 `README.md`。写完前逐条过：

- [ ] 故事线一句话能说清；标题、摘要、贡献、方法首段、结论是同一条线。
- [ ] 每段能用一句话概括；每个观点后面有依据；正文数字只写方向，数字都在表里且来自宏。
- [ ] 无自造词、无未定义符号；pdftotext 逐页扫禁用词为零。
- [ ] 每张表分工不同、格式一致、无 N/A；每个 caption 以结论开头、单独可读。
- [ ] 图表间距按 §5 设过并量过；逐页看过 PDF。
- [ ] 附录顺序服从正文、数字与正文一致、无自贬；删掉附录，正文仍是完整论文。
- [ ] 正文写满页限末行；bibguard 退出码 0，`--uncited` 0；已推远端并同步 Overleaf；只有一份可编译的 diff。

`bibguard` 是引用的唯一入口；`iclr-paper-review` 的审稿意见回到本流程（先改大纲）落地。
