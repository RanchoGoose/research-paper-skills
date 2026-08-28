---
name: paper-writing
description: 写论文与改论文的唯一入口——从大纲和故事线出发写摘要、引言、相关工作、方法、实验、结论与附录；每句话有目的、有依据；事实与观点分开；符号与缩写先定义后使用；摘要/引言/各章节按固定格式；实验数字一律进表格；正文不出现代码路径；附录另起一页、带自己的标题、图表按附录章节号重编、不超过 20 页；caption 与表图的间距按 float 类型分设。附带 paperlint 门禁把能量化的规则变成命令。**凡是动 paper 正文——哪怕一句话——都先过这个 skill：先改大纲，再改正文，最后跑 paperlint。** 触发词：写论文、写 paper、改 paper、写摘要、abstract、introduction、related work、method、实验章节、conclusion、附录、appendix、润色、精简、故事线、大纲、outline、paperlint、排版、页数、caption、间距、figure 太小。
---

# 写 paper 的总规矩（paper-writing）

**铁律一：改 paper 先改大纲。** 对 `main.tex` 的任何直接更改——一个小节、一句话的描述——
都先在 `OUTLINE.md` 里核对/修改故事线，从大纲出发确认叙事和宏观逻辑，再动正文。
paperlint 会拒绝「`main.tex` 改了、`OUTLINE.md` 没改」的工作区。

**铁律二：每句话有目的、有依据，否则删。** 写短，不写长。

**铁律三：引用一律走 `bibguard`。** 禁止任何形式的编造 reference。

## 0. 流程（每次写作都按这个顺序）

1. **故事线先行。** `OUTLINE.md` 里要有一节标题含「故事线」，下面是一张
   claim → 证据 表（表头含「证据」）。文章的每一个环节——背景、问题、方法、每条结论——
   在这张表里各占一行，证据列写明来自实验（哪张表）、理论（哪条定理）还是文献（哪个 key）。
   **没有证据的环节不写进 paper。**
2. **从大纲确认宏观逻辑。** 各 section 的观点串起来必须是一条清晰的线；开篇就快速呈现这条线。
3. **写/改正文。** 遵循叙事和大纲，同一内容不反复表达。
4. **跑门。** `paperlint`（本 skill）+ `bibguard`（引用）。HARD 全清零才算写完。
5. **推远端。** 改完没推等于没做。

## 1. 逐句适用的写作规则

- **目的驱动**：每句话有清晰的目的，否则删去。
- **依据驱动**：每句话有清晰的依据，否则删去。
- **事实与观点严格区分**：论文里所有观点都要有依据——来自实验、理论或参考文献。
- **不重复**：遵循文章叙事和大纲，不要反复表达同样的内容。
- **写短**：用最简短的表达；把文章尽量写短，而不是写长。
- **一段一意**：每个自然段只传递一个中心思想。如果没法用一句话或一个小标题概括本段，重新组织。
- **段首总结**：每个 section 的第一段总结本节的内容或作用。
- **脉络贯通**：各部分的观点联结起来要有清晰的故事脉络；在文章开始就快速、清晰地呈现本文的故事脉络。
- **术语**：paper 里出现的每一个术语，先确认它是自创的还是引用的——自创的要定义并说明为什么需要它，
  引用的要给出来源。任何读者都要能直接读懂。
- **符号与缩写**：任何数学符号、缩写，使用前都清楚明确地定义；不出现未定义的变量、字符；
  符号要足够通用（不确定就用领域内最常见的写法）。
- **数学**：多行推导浓缩成定理/命题，证明进附录；不要让数学过程打断流畅的表达。
- **正文禁止出现对代码的直接引用**：文件路径（`code/x.py`）、脚本名、命令行参数（`--audit`）
  一律不进正文。正文讲结果，不讲产生结果的工具；可复现性声明描述「发布了什么」，不列文件清单。

## 2. 各部分的固定格式

### 摘要（≤ 300 词，四段式，顺序固定）

| 句数 | 内容 |
|---|---|
| 3–5 句 | 背景，高度浓缩 |
| 2 句 | 核心问题与当前面临的困境 |
| 2–5 句 | 本文提出的方法与贡献，浓缩 |
| 2–5 句 | 实验结论——高维度、宏观视角，**避免实验细节**（不放区间、不放逐项数字） |

### Introduction（三段 + 贡献列表）

1. 第一段：背景。
2. 第二段：延续问题——当前 research 面临的问题是什么。
3. 第三段：本文如何解决：思路是什么、motivation 是什么、为什么这样做；然后列出核心贡献。
4. 配一张图（可以是小图，不必横跨整页），辅助解释宏观原理与动机。

### Related Work

- 每一个类别单独一段，段首一句说明这个类别是什么、和本文什么关系。
- 读完要能直接知道：这个领域的核心发展、当前状态、有几种方法/几个方向、各自做了什么、贡献是什么。
  领域外的读者也要能读懂。
- 引用严格走 `bibguard`；每条 reference 都有核对过的来源。
- 配一张图（可以是小图），例如按本文的分类轴把已有方法摆进去。

### Method

- **必须有一张宏观框架图**：清晰、简洁、完整地展示整个方法的框架与细节；颜色分明、有逻辑；
  符号通用。不确定怎么画，就去看同领域 paper 的图是怎么画的。
- 全文的图至少 3 张（引言、相关工作、方法各一张是下限）。

### Experiments

- **背景交代充分**：所有设置、超参数都写出来（表格化）。
- **所有实验结论和数字以表格呈现**；段落解释表格，不做数字的唯一载体。
- **必须包含 ablation study** 证明方法的有效性。
- 结论清晰；实验范围足够广；benchmark 标准、强、有说服力；metrics 说明清楚
  （公开的写明出处即可，自建的必须充分解释）；避免不通用的字符。
- **必须与其他方法对比**：引用近期 baseline，对比的方法是行业内的 SOTA；对比要能体现优越性，
  能论证文章的核心观点与贡献。

### Conclusion

一段：方法是什么、证据说明了什么、边界在哪。

### Appendix

- **不超过 20 页**（特殊情况除外）。
- **必须另起一页**（`\clearpage`）。否则它从参考文献恰好结束的地方开始——常常是共用页的第三条
  文献下面——第一个附录 section 读起来就像文献表的续篇。
- **必须有自己的标题，且标题里要含论文标题。** 补充材料会被单独打印、单独下载、单独送审，
  只写「Appendix」的话它说不出自己属于哪篇论文。**标题用和 `\title` 同一个宏**
  （`\newcommand{\papertitle}{...}`），否则两处早晚会对不上：

  ```latex
  \clearpage
  \appendix
  \begin{center}
  {\Large\sc Appendix}\\[7pt]
  {\large\papertitle}
  \end{center}
  ```
- **附录里的图表要按附录章节号重新编号，不要延续正文的计数。** 正文是 Figure 3 / Table 5，
  附录就该是 Figure A.1 / Table C.2，而不是接着数成 Figure 7 / Table 18。延续正文计数的编号
  不告诉读者去哪找——他得在一堆按字母编号的章节里往前数十八张表；`A.1` / `C.2` 直接说明
  开哪一节。`\counterwithin` 顺手把「每个 `\section` 归零」也做了，两套编号不会撞：

  ```latex
  \setcounter{figure}{0}\setcounter{table}{0}
  \counterwithin{figure}{section}
  \counterwithin{table}{section}
  ```
- 附录只做补充说明；**核心实验结论必须放在正文**。默认不带附录也是一篇完整、充分的优秀论文。

## 3. 门：paperlint

```bash
P=.claude/skills/paper-writing/scripts/paperlint.py

python3 $P main.tex --outline OUTLINE.md              # 完整门禁（先编译一次，它读 .log/.aux/.pdf）
python3 $P main.tex --outline OUTLINE.md --quiet-info # 只看 HARD/WARN
python3 $P main.tex --outline OUTLINE.md --json lint.json
python3 $P main.tex --no-git                           # 不在 git 仓库里时
python3 $P main.tex --acronyms-ok .paperlint_acronyms  # 不必定义的缩写（型号名等），一行一个
```

**退出码 = HARD 条数。** HARD 必须清零；WARN 是写完前要逐条过目的清单；INFO 是给你核对用的事实。

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
| WARN | `appendix-page` | `\appendix` 前面没有 `\clearpage`——附录没有另起一页 |
| WARN | `appendix-title` | 附录没有标题，或标题里不含论文标题 |
| WARN | `appendix-numbering` | 附录里有图表，但编号还在延续正文的计数 |
| WARN | `caption-skip` | 表的 caption 在上，而 `\belowcaptionskip` 从未设成非零——caption 会贴住表格 |
| WARN | `acronym` | 缩写在「全称 (缩写)」定义之前就用了 |
| WARN | `symbol` | 数学符号首次出现处附近没有定义句 |
| WARN | `repeat` | 两句话说的是同一件事 |
| WARN | `paragraph` | 一段超过 10 句或 260 词——一段一意 |
| WARN | `number-in-prose` | 实验章节的段落里出现结果数字——确认表里有 |
| INFO | `section-lead` | 每个 section 第一段的第一句——自问它是否总结了本节 |

paperlint 会内联 `\input{}` 和 `\IfFileExists{}{\input{}}{}`，所以生成到 `gen/` 里的表格也算数。
页数从编译产物读：`main.log` 给总页数，`main.aux` 给附录起始页，`pdftotext` 找正文结束页。

## 4. 排版：读者看到的是版面，不是源码

排版不是内容，但读者第一眼看到的是它。下面几条是反复踩出来的。

### caption 的间距必须按 float 类型分设

**表的 caption 在表上面，图的 caption 在图下面，所以同一对长度对两者意思相反，
一个全局设置不可能同时对。** `article` 的默认是 `\abovecaptionskip=10pt / \belowcaptionskip=0pt`：
对表来说 caption 最后一行直接压在 `\toprule` 上，而表和下面正文之间还有整整一个
`\textfloatsep`——**caption 看上去离自己的表比表离下一段还远。**

用 `etoolbox` 在每种 float 打开时设自己的值，在 float 自己的组里，互不泄漏：

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

经验值：正文表 8/5、附录表 5/3，图的 image→caption 6pt / 3pt。
**判断标准是「caption 离自己的表，要明显近于表离无关正文」。**

### 图：宽度和 trim 都要量，不要拍脑袋

- `0.8\textwidth` 这种随手写的宽度会白扔一大块版心。图不占满宽只应该有具体理由。
- 放大前先算**有效分辨率**：`源图内嵌位图的 ppi ÷ (排版宽度 ÷ 源图宽度)`。
  ≥300 ppi 就不会糊，够就放心占满宽。
- **`trim` 按源图自己的墨迹范围量出来，不要猜。** 把源图渲染成灰度位图、找出全白的行，
  就能读到每一行内容的精确边界；猜出来的 trim 很容易切进坐标轴框，或留下一圈死白。

### 正文/附录差几行时，按这个顺序收

1. **float 间距**（`\textfloatsep` / `\floatsep` / `\intextsep`），最划算，不动任何内容。
2. **`\bibsep`**——natbib 从 `\itemsep+\parsep` 取值。参考文献只多出几条到下一页时，
   把它调小 2pt 就能整页省下来，一个条目都不用动。
3. **负 `\vspace`**，只用在节标题前后这种明确的地方。
4. 最后才是删句子。**删事实和表格永远是最后手段。**

**先诊断是 text-bound 还是 float-bound。** 附录页数下不来时，常常是半空的 float 页在吃掉
删掉的散文——一页只排了 53 行而满页是 87 行，这时删字没有用。该做的是：收 float/caption 间距、
把长节移到参考材料前面让尾部的 float 页塌掉、把已经被正文逐字引用的表改成随 bundle 发布不排版、
把相邻的两张图合成一个 float 两个 caption。**用负 `\vspace` 收不掉 float 排布留下的缝隙**——
那不是显式跳距，硬压只会换来 overfull vbox。

### 随论文发布的源码和注释里，不要留内部迭代语汇

「Reviewer round 3 asked for…」「reviewer A2」「path-to-8」这类话进了 supplementary，
**在投稿期会被读成本届审稿人**，而且把内部迭代史一起发了出去。
**留原因，去出处**：「为什么这张表不排版」值得留，「谁要求的」不留。
指将来读稿的人的「a reviewer」可以留。

清理措辞时**顺手核对措辞指向的东西是否存在**——补充材料里指向的文件是否真的进了包、
正文引用的计划文件是不是恰好在打包 denylist 上。这类洞往往就是这么冒出来的。

## 5. 写完前的自检（机器查不了的部分）

- [ ] 故事线一句话能说清；摘要、引言、结论说的是同一条线。
- [ ] 每个 section 第一段就是本节的总结。
- [ ] 每个自然段能用一句话概括。
- [ ] 每一个观点后面跟着它的依据（表号 / 定理号 / 引用 key）。
- [ ] 每一个自创术语在首次出现处定义，并说明为什么需要它。
- [ ] 每一个符号在首次出现处定义；没有只在图里出现的符号。
- [ ] Related Work 每段一个类别；领域外读者能读懂。
- [ ] 方法图看一眼就知道框架；颜色有逻辑；符号和正文一致。
- [ ] 实验：设置与超参数表、主结果表、ablation 表、与 SOTA 的对比表；metrics 有出处。
- [ ] 附录 ≤ 20 页；另起一页；标题含论文标题；图表按附录章节号编号；把附录整个删掉，正文仍是一篇完整的论文。
- [ ] 逐页看过一遍 PDF：没有裁切、重叠、糊掉的图，caption 和它的表图之间有明确但更近的间距。
- [ ] `bibguard` 退出码 0；`--uncited` 0 条。

## 6. 与其他 skill 的关系

- `bibguard`：所有引用的唯一入口。本 skill 不查引用真伪，只要求引用必须经它写入。
- `iclr-paper-review`：审稿用。本 skill 是写作用；审稿意见回到本 skill 的流程（先改大纲）里落地。
