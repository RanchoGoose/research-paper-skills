# Research Paper Skills

三个相互独立的 Agent Skill，覆盖一篇论文里真正可以被检查的部分：参考文献、正文、审稿。

| Skill | 做什么 |
|---|---|
| [**bibguard**](skills/bibguard/) | 核实每条引用真实存在、查出真正的发表出处、新增条目一律先查证后写入、把全篇 `.bib` 统一成一种格式。 |
| [**iclr-paper-review**](skills/iclr-paper-review/) | 按严格 ICLR 标准审稿：创新性、论据链、公式与参数、每一张图表、实验充分性、附录长度，并给出单一 1–10 分。 |
| [**paper-writing**](skills/paper-writing/) | 写论文的逐节模板——先改大纲再改正文、数字进表、每条结论都有证据——外加 `paperlint`，把能量化的规则变成一条带退出码的命令。 |

三个 skill 各自自包含，可以单独安装，彼此不调用、不依赖。

[English](README.md) · [MIT](LICENSE)

## 安装

全部装到 Codex：

```bash
npx skills add RanchoGoose/research-paper-skills --skill '*' -g -a codex -y
```

只装其中一个，或者先看看有哪些：

```bash
npx skills add RanchoGoose/research-paper-skills --skill bibguard -g -a codex -y
npx skills add RanchoGoose/research-paper-skills --list
```

用 Claude Code 就把 `codex` 换成 `claude-code`。也可以从克隆安装，或只装进某个项目：

```bash
git clone https://github.com/RanchoGoose/research-paper-skills.git
cd research-paper-skills
bash install.sh all --claude --user
bash install.sh bibguard --claude /path/to/paper
```

两个 CLI 都只依赖 Python 3.8+ 标准库，不装 pip 包，不需要 API key 就能跑。

## bibguard

**核实 `.bib` 里每篇论文真实存在、查出它真正发表在哪、并把全篇格式统一。**
引用是在写进去之前查证的，不是之后。参考文献表会出三种错，它三种都管：

- **论文根本不存在**：模型编了个像模像样的标题，或者你从一篇本身就编错了的论文里抄了引用。
- **出处写错了**：你引的是预印本，它其实已经中了 NeurIPS；或者论文改了名，你写的还是旧标题。
- **格式不统一**：一半写 `CVPR 2025`，一半写会议全称，还有一条渲染出来是 "In In Proceedings of"。

最要紧的一点是它会告诉你**哪些条目没能验证**，而不是把它们悄悄报成没问题。
每条都会列出自己的独立锚点（arXiv ID / DOI / OpenReview / Crossref / AMiner），
一个锚点都没有的条目会被标出来要求人工核原文。`--add` 查不到就拒绝写入，绝不编一条看起来很像真的。

```bash
S=skills/bibguard/scripts/bibguard.py

python3 $S references.bib --add "论文标题"     # 先查证，再追加
python3 $S references.bib                     # 核对 + 报告（读缓存，可安全重跑）
python3 $S references.bib --fix               # 把出处和统一格式写回 .bib
python3 $S references.bib --refresh           # 忽略缓存重查（投稿前必做）
python3 $S references.bib --uncited main.tex  # 列出正文没引用的条目
```

退出码 **0 = 无需改动，1 = 有条目待处理**，可以直接当投稿前的 gate。
完整参数、报告格式、数据源和 `--fix` 的格式规则见
[`skills/bibguard/README.md`](skills/bibguard/README.md)。

## iclr-paper-review

把论文当成一个完整的科学论证来审，而不是一堆关键词和 benchmark 数字：

- 与最接近的概念替代方案做语义创新性对比；
- 贯穿正文与附录的 claim → 证据 台账；
- 摘要审计：清晰度、精简度、覆盖全文、细节取舍；
- 正文自足性闸，以及对每一张正文/附录图表及其交叉引用的逐个审计；
- 参数、记号、公式台账，含数学、类型、形状、量纲与逻辑检查；
- 实验充分性：baseline 公平性、数字清晰度、普适性、规模、可复现性；
- 明确的附录长度结论：默认标准下目标 20 页、硬上限 30 页；
- 写作、术语、定义、引用与叙事逻辑审查；
- 单一的 1–10 校准分，其中 8 分保留给 Strong Accept；
- 可选的、需显式授权的 Git/Overleaf 迭代审稿循环。

安装后这样调用：

```text
用 $iclr-paper-review 审这篇论文和补充材料，逐条核对公式、参数、图表，
评估实验充分性与附录长度，并给出一个校准过的 ICLR 分数。
```

评分标准与各项专门审计流程见
[`skills/iclr-paper-review/references/`](skills/iclr-paper-review/references/)。

## paper-writing

审稿 skill 的写作对应物：一份逐节的写稿模板，加上一个把能量化的那一半变成命令的 linter。

- **先改大纲。** 对正文的任何更改——哪怕一个词——都先核对并修改大纲。
  大纲里带一条故事线和一张 claim → 证据 表，没有证据的环节不写进论文。
- **结论从数据推。** 已有结论不一定对；idea 和核心结论都可以改，但改动先落到大纲。
- 每句话有目的、有依据；同一件事不说两遍；短的那版胜出。逐句改，不整篇重写；
  作者亲手写的句子逐字保留。
- 面向没有先验的读者：只用领域通用词，不造名词；符号和缩写先定义后使用；
  句子平直、不用冒号；各节用审稿人熟悉的语域。
- 数字进表、来自生成的宏；正文只写结果的方向和它在哪张表里。
  不写裸数字，不写「Δ [lo, hi]」区间。
- 逐节模板：五步摘要；三段引言加三条各一句的贡献；相关工作一类一段；
  方法节一张框架图；实验节有设置段、每张表各证一个角度、两块消融、
  肉眼选定的定性大图和成本表。
- 图表：Base 与 +Method 成对、方法行浅底、每列最优加粗、不留 N/A；
  小表 wrap 在正文旁；沿某个轴变化的量画成曲线而不是表；
  每个 caption 以一句加粗的结论式 highlight 开头。
- 正文不出现代码路径、脚本名和命令行参数。附录顺序服从正文，每节首句说明补充什么，
  与正文重复的数字必须是同一个宏；不超过 20 页，另起一页，标题里带论文自己的标题，
  图表按附录章节号重编。
- 排版：模板自带的字体与间距，不用 `\vspace`；caption 间距按 float 类型分设；
  图宽和 trim 要量不要猜；压页先 float 间距，再 `\bibsep`，再删重复句；
  正文写满页限的最后一行。

`paperlint` 把能查的查掉，退出码就是 HARD 的条数：

```bash
python3 skills/paper-writing/scripts/paperlint.py main.tex --outline OUTLINE.md
```

HARD 覆盖大纲闸、摘要长度、引言结构、图表覆盖、页数上限和正文里的代码路径；
WARN 与 INFO 覆盖偏软的规则。它会内联 `\input{}` 让生成的表格也算进去，
页数从编译产物 `.log`、`.aux` 和 PDF 里读。完整规则表见
[`skills/paper-writing/README.md`](skills/paper-writing/README.md)，
规矩原文见 [`skills/paper-writing/SKILL.md`](skills/paper-writing/SKILL.md)。

## 测试

全部离线，不需要网络和 key：

```bash
python3 tests/test_skill_layout.py
python3 skills/bibguard/tests/test_offline.py
python3 skills/paper-writing/tests/test_offline.py
```
