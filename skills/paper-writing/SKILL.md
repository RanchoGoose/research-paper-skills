---
name: paper-writing
description: 写论文与改论文的唯一入口——一份逐节模板：标题、五步摘要、三段引言加三条一句贡献、相关工作一类一段、方法框架图、实验的设置段/表的分工/主表规范/数据呈现原则/消融/定性图/成本、结论与附录，每段该写什么都有明确指导；四条铁律（先改大纲、每句有目的有依据、引用走 bibguard、结论从数据推）；只用领域通用词、数字进表正文写方向、caption 以结论式 highlight 开头、+Method 行浅底、不用 \vspace、正文写满页限末行；附带 paperlint 门禁。**凡是动 paper 正文——哪怕一个词——都先过这个 skill：先改大纲，再逐句改正文，最后跑 paperlint。** 触发词：写论文、写 paper、改 paper、写摘要、abstract、introduction、related work、method、实验章节、conclusion、附录、appendix、润色、精简、故事线、大纲、outline、paperlint、排版、页数、caption、间距、figure、table、贡献、contributions。
---

# 写 paper 的总规矩（paper-writing）

四条铁律，其余都是它们的展开。

- **铁律一：改 paper 先改大纲。** 对 `main.tex` 的任何改动——一节、一句、一个词——先在 `OUTLINE.md` 核对或修改故事线，再动正文。paperlint 拒绝「`main.tex` 改了、`OUTLINE.md` 没改」的工作区。
- **铁律二：每句话有目的、有依据，否则删。** 写短，不写长；同一内容只说一次。
- **铁律三：引用一律走 `bibguard`。** 任何形式的编造 reference 都禁止。
- **铁律四：结论从数据推。** 已有结论不一定对，不能拿结论反推实验；idea 和核心结论都可以改，但改动先落到大纲。

## 0. 流程（每次写作按此顺序）

1. **故事线先行。** `OUTLINE.md` 里有一节标题含「故事线」，其下一张 claim → 证据表（表头含「证据」）：背景、问题、方法、每条结论各占一行，证据列写来自哪张表、哪条定理或哪个引用 key。没有证据的环节不写进 paper。
2. **从大纲确认宏观逻辑。** 各节观点串成一条线，开篇就把这条线亮出来。
3. **改正文：逐节、逐句、逐词。** 每轮只动要改的句子，其余原样保留；**不要整篇重写**——整篇重写会把已经改好的东西弄丢，用户也无法对着 diff 审。用户亲手改过的句子（摘要等）逐字保留，只把数字换成同值的宏。
4. **跑门。** `paperlint`（本 skill）+ `bibguard --uncited` + 编译门：0 error、0 undefined、0 overfull、未引用条目 0。bibtex 要在编译目录内跑，别让 `-output-directory` 回退读仓库根的旧 `.bbl`。
5. **推远端并同步 Overleaf。** 改完没推等于没做。给用户看的 diff 只留一份：最新版对用户批注版，必须能编译出 PDF。
6. **页数最后收。** 先把完整正文写好，再按 §5 压到页限；删重复，不删事实和表。

## 1. 读者与语言（逐句规则）

- **读者模型**：没有任何本文以外先验知识的人，逐句都能懂；每张图、每张表单独拿出来也能读出明确结论。
- **术语只用领域通用词。** 每个术语先问「自创的还是引用的」：引用的给出处，自创的必须定义并说明为何需要，能不用就不用。拿不准就查同类论文怎么叫。本项目被判为自造词而全部替换过的：page、generator、protocol、host、suite、segment、arm、judge、install、held open（→ state / video model / benchmark / clip / setting / evaluator / load）。
- **名词统一**：方法名全文 `\textsc{}`（含标题）；基线行叫 Base；缩写首次出现给全称和含义；每个指标首次出现处说清含义与方向；模型型号只在设置段写一次，图表里不写型号、不写 frozen。
- **句子**：简单直白的英语；不用冒号引出解释；少逗号、不写碎句、不用压缩省略句；前后句要承接，不突兀；不写「Hence a design principle」这类空话。
- **语域**：各节用审稿人熟悉的常规写法（We propose… / Extensive experiments show…），句式照同领域强论文；段落小标题短而平实，不用整句 highlight。
- **符号与数学**：符号使用前定义，用领域最常见写法；多行推导浓缩成定理或命题，证明进附录。
- **正文不引用代码**：文件路径、脚本名、命令行参数一律不进正文；可复现性只写「发布了什么」。
- **自信，不自贬**：局限集中在结论段写；正文和附录不写削弱自己证据的话，也不写「我们两者都报了」这类自评。

## 2. 数字与证据

- **数字进表，正文写方向。** 段落只写「在哪个基准上把哪个指标提高/降低了多少点或百分比」；禁止裸数字（−0.030）、禁止「Δ [lo, hi]」区间写法（正文和附录表都禁）；区间在表里用一列 Δ 表示，加粗或 † 表示区间不含零。
- **所有数字来自生成的宏或表**，不手抄；表里的 n 之类没有信息量的列不放。
- **每个观点跟着依据**：表号、定理号或引用 key。
- **摘要和贡献只放 2–3 个最能打的数字。**
- **评价**：不做真人评分；用两个不同权重家族的自动评委重复每个判定，报告一致率。

## 3. 逐节模板（每一段写什么）

### 标题
关键词进标题：要解决的场景（如 unbounded streaming）+ 方法特点（如 training-free）；方法名短、可记、能概括；不造名词。

### 摘要（≤ 250–300 词，顺序固定，无冒号）
1. 这类系统怎么工作、做不到什么（1–2 句）。
2. 由此带来的两个普遍且难解的问题（各 1 句：一个随生成时间累积而恶化，一个关于长程记忆——忘掉或错认已出现的内容）。
3. 我们提出 training-free 的 X，区别于主流的 Y（1 句）。
4. 通过什么手段解决了什么（1–2 句；不展开机制细节）。
5. 在哪些基准、哪些基模上评测，得到什么结果（1–2 句，2–3 个惊艳数字）。

### 引言（三段 + 贡献列表 + 一张小图）
- 段 1 背景。段 2 延续问题：把摘要里的两个问题具象化（一分钟前的脸或街道已不是原来的）。段 3 我们怎么解决：思路、motivation、为什么这样做；段末一句结果总述（几个模型、几个基准、整体结论）。
- 贡献：`Our contributions are summarized as follows.` + 三条，每条一句，不加粗、不写 To our knowledge：
  1. 第一个做到什么——针对上面两个局限说明为何特别、为何重要；
  2. 具体机制：我们提出了具体的 A，解决了具体的 B（novelty 与两个局限一一对应）；
  3. We evaluate X on … benchmarks and … models, achieving …（两个最惊艳的数字）。
- 小图辅助宏观原理与动机，不必横跨整页。

### 相关工作
- 每类一段，段首一句说明这个类别是什么、与本文什么关系。
- 主线类别按领域发展脉络从奠基工作讲到现状，每句话对照所引论文的摘要核对。
- 末段写最接近的工作和本文的区别；对手的机制只在这里讲，实验节不重复。
- 配一张小图，例如按本文的分类轴摆放已有方法。

### 方法
- 首段一句话定义问题：解决什么问题、用什么手段（几个手段就列几个）。
- 一张宏观框架图：真实画面 + 框架，颜色分明、有逻辑，符号通用，图里每个字都要斟酌；方法的核心决策部分要在图里看得见；详细 workflow 图放附录。
- 关键操作给公式；符号先定义；符号与图一致。

### 实验
- **设置段**：基模（引用）、基准（引用；自建的充分解释）、指标（定义、方向、出处）、评委、超参数进表；表里每个对比方法带引用。
- **表的分工**：每张表证明一个不同角度，互不重复——画质 / 记忆召回 / 场景切换与更长视频 / 消融 / 成本。对比对象是同类已发表的 SOTA（同一方向的方法），只收已发表工作；预印本进附录。
- **主表规范**：Base 与 +Method 成对，+Method 行浅灰底；加粗 = 每列最优；横向排版，各表格式一致；完整评测（所有指标），不留 N/A（补齐或删列）；数字宏生成。
- **数据呈现原则**：正文只放方法整体明显占优的表；个别格可以输；整列没有优势或对半开的列进附录。结果与预期相反先查评测口径与方法实现（本项目两次是读法或口径错），查实仍不利就如实进附录，不改数字。
- **每段一个短小标题**，段内写方向 + 表号 + 附录指针；对比段只写「与 X 比，结果 Y」。
- **消融**：两块——把核心部件换成固定规则、逐一去掉部件；标出区间不含零的损失；不放 only 一类冗余行。
- **定性大图**：多基线截图对比，一眼看出谁好谁坏。先按规则筛 case（主体是人、评委记录对比鲜明），再按印刷尺寸肉眼定；画全部 clip；按评委记录画绿/红框；不用画面崩坏的模型或 case；caption 说清比的是什么。
- **成本**：同一机器同测的秒数与倍率；省时的设置保住多少增益。

### 结论、局限与未来工作
每段一个中心思想：方法是什么、证据说明什么；为什么重要、对社区的意义；局限与未来工作连写。正文恰好写满页限的最后一行。

### 附录
- 只做补充：完整评测、补充实验、补充证明；正文不带附录也是一篇完整论文；核心证据不因页数搬进附录。
- 顺序服从正文；方法框架、伪代码、决策记录靠前；每节首句写「本节补充正文哪张表或哪一段」。
- 与正文重复的数字必须逐格一致（同一宏），否则不放；删掉削弱正文可信度或方法优势的内容。
- ≤ 20 页（特批 24）；`\clearpage` 另起一页；标题含论文标题（用与 `\title` 同一个宏）；图表按附录节重编号（`\counterwithin`）；每节前 `\FloatBarrier`，浮动体 `[htbp]`。

```latex
\clearpage
\appendix
\begin{center}
{\Large\sc Appendix}\\[7pt]
{\large\papertitle}
\end{center}
\setcounter{figure}{0}\setcounter{table}{0}
\counterwithin{figure}{section}
\counterwithin{table}{section}
```

## 4. 图表规范

- **Figure**：画布 `\linewidth`（不留两侧空白）；印刷尺寸下可读；每方法一色且全篇一致；箭头、线、字不重叠；框架图用真实帧；对比图一眼看出谁好、越大还是越小更好；拿不准就照同领域强论文的图画。
- **Table**：数字表能画成图就画图（随距离或位置变化的曲线）；小表用 wraptable 嵌在正文旁把空白用满，wrap 只放段首、离页底至少一个表高；避免既挤又空的排版。
- **Caption 模板**：`\textbf{一句结论式 highlight.}` + 画的是什么、单位与方向、加粗/底色/符号含义、附录指针。写具体（在哪个基准上提高多少），不写抽象标签。
- 所有图表章节用 `\ref` 可跳转。

## 5. 版面：读者看到的是版面

- 标准模板字体与间距；不用 `\vspace` 调页。
- **caption 间距按 float 类型分设**：表 caption 在上、图在下，一个全局值不可能两者都对：

```latex
\usepackage{etoolbox}
\newlength{\tabcapabove}\newlength{\tabcapbelow}
\newlength{\figcapabove}\newlength{\figcapbelow}
\setlength{\tabcapabove}{8pt}\setlength{\tabcapbelow}{5pt}
\setlength{\figcapabove}{6pt}\setlength{\figcapbelow}{0pt}
\AtBeginEnvironment{table}{%
  \setlength{\abovecaptionskip}{\tabcapabove}\setlength{\belowcaptionskip}{\tabcapbelow}}
\AtBeginEnvironment{figure}{%
  \setlength{\abovecaptionskip}{\figcapabove}\setlength{\belowcaptionskip}{\figcapbelow}}
```

- **差几行的收法**，按顺序：float 间距 → `\bibsep` → 删重复句（末行只有 1–5 个词的段最划算）。删事实和表格永远是最后手段。
- **正文写满最后一行**：用 `\raggedbottom` 副本量末行 y；末行只能落在离散位置；图表高度一变就重填；跨页的末段会触发 widow 留一行空白，让它在本页内结束。
- 先诊断 text-bound 还是 float-bound：半空的 float 页吃掉删掉的散文时，删字没用，该收 float、合并相邻图、把已被逐字引用的表改为随包发布。
- 图宽和 trim 量出来，不猜；随论文发布的源码注释不留内部迭代语汇（留原因，去出处）。

## 6. 迭代与审稿

- 审稿意见先核实再接受；每条要么改，要么把反驳理由写清楚到审稿人不再揪。
- 每轮汇报：改了什么、没改什么、为什么；改动要能在 diff 上看出来。
- 用户在 diff 上的批注逐条落实，不脱离用户逐字改过的句子。
- 写作与实验分工：写作会话不跑新实验，先在已有数据里找可优化的呈现；数据、表、图由实验会话按生成器出，正文不手改生成文件。

## 7. 门：paperlint

```bash
P=.claude/skills/paper-writing/scripts/paperlint.py

python3 $P main.tex --outline OUTLINE.md              # 完整门禁（先编译一次，它读 .log/.aux/.pdf）
python3 $P main.tex --outline OUTLINE.md --quiet-info # 只看 HARD/WARN
python3 $P main.tex --outline OUTLINE.md --json lint.json
python3 $P main.tex --no-git                           # 不在 git 仓库里时
python3 $P main.tex --acronyms-ok .paperlint_acronyms  # 不必定义的缩写（型号名等），一行一个
```

**退出码 = HARD 条数。** HARD 必须清零；WARN 逐条过目；INFO 供核对。

| 级别 | 代码 | 查什么 |
|---|---|---|
| HARD | `outline-first` | `main.tex` 改了而 `OUTLINE.md` 没改 |
| HARD | `outline-story` / `outline-ledger` | 大纲没有「故事线」一节，或其下没有 claim→证据 表 |
| HARD/WARN | `outline-cover` | 正文某个 `\section`（HARD）/ `\subsection`（WARN）在大纲里从未出现 |
| HARD | `abstract-length` | 摘要超过 300 词 |
| WARN | `abstract-shape` / `abstract-detail` | 句数不在 9–17；摘要里塞了数字、区间、宏 |
| HARD/WARN | `intro-shape` | 引言少于 3 段（HARD）；多于 6 段（WARN） |
| HARD | `figures-count` / `figure-intro` / `figure-related` / `figure-method` | 正文图少于 3 张；引言/相关工作/方法没有图 |
| HARD | `tables-count` / `ablation` | 实验章节没有表；全文没有 ablation |
| HARD | `pages-main` / `pages-appendix` | 正文超 9 页；附录超 20 页 |
| HARD | `code-ref` | 正文出现代码路径、脚本名或命令行参数 |
| WARN | `appendix-page` | `\appendix` 前面没有 `\clearpage` |
| WARN | `appendix-title` | 附录没有标题，或标题里不含论文标题 |
| WARN | `appendix-numbering` | 附录里有图表，但编号还在延续正文的计数 |
| WARN | `caption-skip` | 表的 caption 在上，而 `\belowcaptionskip` 从未设成非零 |
| WARN | `acronym` | 缩写在「全称 (缩写)」定义之前就用了 |
| WARN | `symbol` | 数学符号首次出现处附近没有定义句 |
| WARN | `repeat` | 两句话说的是同一件事 |
| WARN | `paragraph` | 一段超过 10 句或 260 词 |
| WARN | `number-in-prose` | 实验章节的段落里出现结果数字——确认表里有 |
| INFO | `section-lead` | 每个 section 第一段的第一句——自问它是否总结了本节 |

paperlint 会内联 `\input{}` 和 `\IfFileExists{}{\input{}}{}`，生成到 `gen/` 里的表格也算数。页数从编译产物读。

## 8. 写完前的自检

- [ ] 故事线一句话能说清；标题、摘要、贡献、方法首段、结论说的是同一条线，两个局限与两个手段一一对应。
- [ ] 每个 section 第一段是本节的总结；每个自然段能用一句话概括。
- [ ] 每个观点后面跟着依据；正文数字只写方向，数字都在表里且来自宏。
- [ ] 全文无自造术语、无未定义符号和缩写；用 pdftotext 对整本 PDF 逐页扫禁用词，须为零。
- [ ] 每张表分工不同、格式一致、+Method 行有底色、加粗正确、无 N/A；每个 caption 以结论式 highlight 开头，单独可读。
- [ ] 方法图看一眼知道框架；定性大图一眼看出谁好；图无裁切、重叠、糊掉。
- [ ] 附录顺序服从正文、每节首句说明补充什么、重复数字与正文一致、无自贬内容；把附录整个删掉，正文仍是完整论文。
- [ ] 正文写满页限最后一行；`bibguard` 退出码 0，`--uncited` 0；已推远端并同步 Overleaf；只有一份可编译的 diff。

## 9. 与其他 skill 的关系

- `bibguard`：所有引用的唯一入口。本 skill 不查引用真伪，只要求引用必须经它写入。
- `iclr-paper-review`：审稿用。审稿意见回到本 skill 的流程（先改大纲）里落地。
