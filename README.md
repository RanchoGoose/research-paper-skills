# bibguard

**Your `.bib`, guarded.** Add a citation and it gets verified before it is written.
Check the ones already there, find where each was really published, and make the
whole bibliography use one format.

One Python file, standard library only. No `pip install`, no API key required.
Works as a plain CLI, as a pre-submission CI gate, or as a [Claude Code](https://claude.com/claude-code) skill.

[中文说明](#中文) ·  [MIT](LICENSE)

---

## Why

Three things go wrong in a bibliography, and they fail in different ways:

| Failure | How it usually reaches the reviewer |
|---|---|
| **The paper does not exist** | An LLM invented a plausible title, or you copied a citation from a paper that had itself invented it. |
| **The venue is wrong** | You cited the arXiv preprint. It has since been published at NeurIPS. Or it was renamed, and your title is the old one. |
| **The format is inconsistent** | Half the entries say `CVPR 2025`, half say `Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition`, one says `In Proceedings of...` and renders as "In In". |

`bibguard` handles all three, and — the part that matters most — it tells you
**which entries it could not verify**, instead of quietly reporting them as fine.

The name is the design: nothing gets into your bibliography that no source could
confirm. `--add` will refuse to write an entry rather than invent a plausible one.

## Install

```bash
git clone https://github.com/RanchoGoose/bibguard.git
cd bibguard
bash install.sh --user            # → ~/.claude/skills/bibguard (all projects)
bash install.sh /path/to/paper    # → that project's .claude/skills/
```

Or just run it in place — it is one self-contained script:

```bash
python3 scripts/bibguard.py references.bib
```

Requires Python 3.7+. Nothing else.

## Use

```bash
S=scripts/bibguard.py

python3 $S references.bib --add "Attention Is All You Need"   # verify, then append
python3 $S references.bib --add 2506.08009                    # arXiv id or DOI works too
python3 $S references.bib                 # report (uses cache, safe to re-run)
python3 $S references.bib --fix           # write venues + uniform format back (.bak first)
python3 $S references.bib --only k1,k2    # just these keys
python3 $S references.bib --refresh       # ignore cache, re-query everything
python3 $S references.bib --json out.json # machine-readable
python3 $S references.bib --uncited main.tex   # entries your paper never cites
python3 $S references.bib --pause 2       # go slower if you are being rate-limited
```

**Exit code 0 = nothing to do, 1 = something needs attention.** Drop it in CI:

```yaml
- run: python3 scripts/bibguard.py references.bib --refresh
```

Results are cached in `.refcache.json` next to the `.bib`, so an interrupted run
resumes without re-querying. Add it to `.gitignore`.

## Adding a citation

Give it a title, an arXiv id, or a DOI. It verifies the paper first, then writes
the entry:

```
$ python3 scripts/bibguard.py references.bib --add "LongLive: Real-time Interactive Long Video Generation"

标题  : LongLive: Real-time Interactive Long Video Generation
出处  : Proceedings of the International Conference on Learning Representations (ICLR)
锚点  : arXiv:2509.22622, openreview, aminer

@inproceedings{longlive2026,
  title     = {{LongLive}: Real-time Interactive Long Video Generation},
  author    = {Yang, Shuai and Huang, Wei and ... and Chen, Yukang},
  booktitle = {Proceedings of the International Conference on Learning Representations (ICLR)},
  year      = {2026},
  note      = {Poster; arXiv:2509.22622}
}
```

It handles the details that are easy to get wrong by hand:

- **Author names inverted** to BibTeX's `Last, First`, with lowercase particles
  kept on the surname (`van den Berg, Rianne`).
- **Acronyms braced** — `{MuKV}`, `{KV}`, `{NVFP4}` — or a lowercasing `.bst`
  renders "MuKV" as "Mukv". Hyphenated title case (`Multi-Grained`, `Train-Test`)
  is left alone.
- **Citation key in your bibliography's own shape**: the short name before the
  colon plus the year, `longlive2026`. Collisions get a suffix.
- **Title, authors and year come from the authoritative record**, not from what
  you typed — the name you know a paper by is often its old one.

And three cases where it refuses to write, which is the whole point of the name:

| Situation | What happens |
|---|---|
| The paper cannot be found | ✗ Refused. **It will not invent a plausible entry.** |
| Found, but no independent anchor | ✗ Refused; check the paper yourself and write it by hand. |
| Already in your `.bib` | · Tells you the existing key and how to update its venue instead. |

`--dry-run` prints without writing. A `.bak` is saved before any write.

## What it reports

```
[07] selfforcing2025        PUBLISHED
     bib now : arXiv preprint arXiv:2506.08009
     title   : Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion
     建议    : NeurIPS 2025 spotlight; NeurIPS 2025|2025|doi:10.52202/085713-5576
     锚点    : arXiv:2506.08009, openreview, crossref, aminer
     证据    : OR:NeurIPS 2025 spotlight || AMINER:NeurIPS 2025 (2025) || CR:Advances in NeurIPS 38 (2025)
```

| Status | Meaning | What to do |
|---|---|---|
| `PUBLISHED` | A real conference/journal record was found | If the bib still says arXiv → `--fix` |
| `PREPRINT` | Exists, no venue found | Keep `@article` + arXiv. Normal. |
| `WORKSHOP_OR_REJECTED` | Only workshop / rejected / under-review records | Decide whether your venue standard allows it |
| 🔴 **no anchor** | **Nothing could confirm this entry at all** | Open the paper yourself. See below. |

### The part that matters: verified vs. unverifiable

The easiest way to fool yourself is to treat *"I asked and got nothing"* and
*"my request failed"* as the same result. They are not. An HTTP 429 cached as a
clean `PREPRINT` looks exactly like a genuinely-checked preprint in the report.

So every entry lists its **independent anchors** — `arXiv:xxxx.xxxxx`,
`doi:10.xxxx/...`, `openreview`, `crossref`, `aminer`. **Zero anchors means
nothing verified it**, and the report flags it 🔴 for you to check by hand.
Rows carrying an API error are never cached as findings; they are re-queried.

## Sources

| Source | Covers | Why it is not replaceable |
|---|---|---|
| **AMiner** ⭐ | Venue for almost everything, incl. CMT-run conferences | **Primary venue source.** CVPR/ICCV are not on OpenReview and have no DOI until proceedings ship — for months, this is the *only* source that knows the paper was accepted. Needs a free key. |
| **arXiv** | Title, authors, dates | The authoritative title. Catches renamed papers. |
| **OpenReview** | ICLR / ICML / NeurIPS / COLM | Those venues issue **no DOI**, so Crossref and OpenAlex cannot see them. Also gives the decision: `ICLR 2026 Oral`. |
| **Crossref** | Anything with a DOI | Returns the DOI itself. |
| **doi.org** | Anything registered anywhere | Publisher-independent content negotiation. The only machine anchor for a paper that was never on arXiv and never went through OpenReview. |
| **DBLP** | Cross-check | Blocked from most datacenter IPs — probed once, skipped silently. Works from home/campus networks. |

All four of arXiv / OpenReview / Crossref / doi.org need **no key and no
registration**. AMiner needs a free key; without one it is skipped and the other
four still work. Every source is gated on **>0.80 title similarity** so a
near-miss never gets silently attributed.

**AMiner is the primary decider of *which venue*, but never of the details:**
the DOI is still harvested from Crossref and the acceptance grade (`Oral`,
`spotlight`) from OpenReview whenever they agree on the same venue. Preferring
one source must not cost you what only another source has.

```bash
export AMINER_API_KEY='...'          # or
echo '...' > ~/.claude/aminer_key    # chmod 600 — read automatically
```

> ⚠️ **Never put the key in your repo.** A `.bib` lives in git; a key committed
> once stays in the history forever.

## Format rules `--fix` enforces

| Kind | Entry type | Field | Written as |
|---|---|---|---|
| Conference | `@inproceedings` | `booktitle` | `Proceedings of the <official name> (<ABBR>)` |
| Journal | `@article` | `journal` | Official journal name in full |
| Preprint | `@article` | `journal` | `arXiv preprint arXiv:XXXX.XXXXX` |

⚠️ `booktitle` must **not** start with "In" — the `.bst` adds it, and you get
"In In Proceedings of...".

Add a venue by editing [`scripts/venues.json`](scripts/venues.json):

```json
"SIGIR": {
  "kind": "conf",
  "book": "Proceedings of the International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR)",
  "match": ["sigir", "research and development in information retrieval"]
}
```

`match` entries are lowercase substrings; the longest match wins, so `naacl`
beats a bare `acl`.

## Two mistakes it will not make

**It will not re-point a venue you already got right.** Many papers have both a
conference and a journal record (VBench is CVPR 2024 *and* has a TPAMI entry).
The script only consults the suggestion list when the bib currently says arXiv;
when a recognizable venue is already there, it normalizes the wording and
nothing else. *This rule exists because an early version silently moved VBench
from CVPR 2024 to TPAMI.*

**It will not overwrite your `note`.** `spotlight`, `oral`, and your own
annotations are merged, not replaced — no API can give them back to you.

## After `--fix`, verify

```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
grep -cE '^!' main.log                        # LaTeX errors — must be 0
grep -c 'Citation.*undefined' main.log        # undefined citations — must be 0
python3 scripts/bibguard.py references.bib --uncited main.tex
```

⚠️ **Do not grep for uncited entries.** `\citep{a,b,%` continued across lines is
a multi-line construct; a line-based grep misses it and reports entries that
*are* cited as unused. Deleting those breaks your paper. `--uncited` matches
across lines.

## Tests

```bash
python3 tests/test_offline.py     # no network required
```

## Notes from actually using this

Collected while checking a 60-entry bibliography. Read before modifying the script.

1. **Never send a long title to OpenReview as the search term.** A 20-word
   title destroys relevance ranking and returns records with `venue=None`; the
   real hit falls outside the top 12. Symptom: "this paper obviously got in, why
   can't it be found?" Fix: query the head of the title (up to the colon, ≤12
   words), then still gate results on full-title similarity.
2. **Title drift is real and only an ID lookup catches it.** arXiv:2401.01256 is
   filed as *VideoDrafter* in many bibliographies; its actual title is
   *VideoStudio: Generating Consistent-Content and Multi-Scene Videos*. Searching
   by title finds nothing; looking up the ID finds it instantly. **Put the arXiv
   ID in your bib.**
3. **A `%` is not a comment in `.bib`.** If a header comment block contains the
   text `@inproceedings`, BibTeX treats it as an entry start and skips the rest.
   Keep `@` out of comments.
4. **OpenReview `CoRR` records are DBLP preprint mirrors** — neither published
   nor rejected. Counting them turns a clean preprint into a false
   `WORKSHOP_OR_REJECTED`.
5. **Crossref conference names often start with the year**
   (`2025 IEEE/CVF Conference on ... (CVPR)`), so a venue whitelist regex has to
   allow a leading year.
6. **Rewriting a `.bib` with `(?=\n)` will duplicate the last field**, because
   an entry body does not include its trailing newline. Split fields on depth-0
   commas instead.
7. **A workshop record does not mean the paper is a workshop paper.** H2O has an
   ES-FoMO poster *and* NeurIPS 2023. StreamingT2V was withdrawn from ICLR 2025
   *and* published at CVPR 2025. Judge on "is there any main-venue record", never
   on "does the string contain reject/withdrawn/workshop".
8. **AMiner's request format is counterintuitive**: `title`, `page`, `size` all
   go in the **query string**. A JSON body first errors with
   「必填字段 title 不存在」, and if you mix body and query it **silently returns
   unrelated papers** — the first hit in one test was a materials-science XPS
   paper. A silent mismatch is far more dangerous than an error.
9. **A flat global sleep does not prevent rate limiting.** With five sources per
   entry, arXiv still sees a request every few seconds and 429s mid-sweep. Space
   requests **per host** and honour `Retry-After`.
10. **Semantic Scholar without a key is a permanent 429** (shared egress IPs are
    saturated); **OpenAlex is useless for CS conferences** — ICLR/ICML/NeurIPS
    return only preprint records.

## Why DBLP is skipped on servers

Measured on an AWS box, 2026-08-11: DNS resolves, the TCP handshake to
`dblp.org:443` succeeds, then the request is reset **0.22s** later — while the
handshake RTT is **0.11s**. The reset arrives exactly one round trip after the
request, so it comes from the far end, not a local middlebox. Other hosts in the
same datacenter answer 200, including `www.dagstuhl.de`, where DBLP itself is
hosted. All three DBLP hostnames fail identically.

Conclusion: **DBLP blocks datacenter IP ranges.** The script probes once per run
and falls through silently rather than burning a timeout on every entry. On a
home or campus connection it enables itself.

---

<a name="中文"></a>

# 中文说明

**核实 `.bib` 里每篇论文真实存在、查出它真正发表在哪、并把全篇引用格式统一。**

一个 Python 文件,只用标准库。不装 pip 包,不需要 API key。
可以当命令行工具、当投稿前的 CI gate,也可以当 [Claude Code](https://claude.com/claude-code) 的 skill。

## 解决三件事

| 问题 | 通常怎么送到审稿人面前的 |
|---|---|
| **论文根本不存在** | LLM 编了个像模像样的标题,或者你从一篇本身就编错了的论文里抄了引用。 |
| **出处写错了** | 你引的是 arXiv 预印本,它其实已经中了 NeurIPS;或者论文改了名,你写的还是旧标题。 |
| **格式不统一** | 一半写 `CVPR 2025`,一半写会议全称,还有一条写了 `In Proceedings of`,渲染出来是 "In In"。 |

一遍跑完全部三件,并且——**最要紧的一点**——它会告诉你**哪些条目它没能验证**,
而不是把它们悄悄报成没问题。

## 装

```bash
git clone https://github.com/RanchoGoose/bibguard.git
cd bibguard
bash install.sh --user            # → ~/.claude/skills/bibguard(全局)
bash install.sh /path/to/paper    # → 装到某个项目
```

或者直接跑,它就是一个自包含脚本:

```bash
python3 scripts/bibguard.py references.bib
```

## 用

```bash
S=scripts/bibguard.py

python3 $S references.bib                 # 核对 + 报告(读缓存,可安全重跑)
python3 $S references.bib --fix           # 把出处和统一格式写回 .bib(先存 .bak)
python3 $S references.bib --only k1,k2    # 只查这几条
python3 $S references.bib --refresh       # 忽略缓存重查(投稿前必做)
python3 $S references.bib --uncited main.tex   # 列出正文没引用的条目
```

退出码 **0 = 无需改动,1 = 有条目待处理**,可直接当投稿前 gate。

## 加一条引用：`--add`

给标题、arXiv id 或 DOI 都行。它会先把这篇论文查证一遍，再生成条目：

```bash
python3 scripts/bibguard.py references.bib --add "LongLive: Real-time Interactive Long Video Generation"
```

生成时自动处理掉几个手写必错的细节：

- **作者名反转**成 BibTeX 要的 `Last, First`，小写介词跟着姓走（`van den Berg, Rianne`）。
- **缩写加花括号**：`{MuKV}` / `{KV}` / `{NVFP4}`，否则某些 `.bst` 会渲染成 `Mukv`。
  连字符词按普通标题大小写处理，`Multi-Grained` 不会被多余地括起来。
- **citation key** 跟全篇同一套写法：标题冒号前的短名 + 年份 → `longlive2026`。
- **标题、作者、年份全部取自权威记录**，不用你提供的那一版（你给的可能是旧名）。

三种它会**拒绝写入**的情况——这就是 guard 的意思：

| 情况 | 行为 |
|---|---|
| 查不到这篇 | ✗ 拒绝。**绝不编一条看起来很像真的** |
| 查到标题但没有任何独立锚点 | ✗ 拒绝，要求人工核原文后手写 |
| 这篇已经在 .bib 里了 | · 提示已存在的 key，并告诉你用 `--only <key> --fix` 更新出处 |

`--dry-run` 只打印不写文件。写入前自动存 `.bak`。

## 最关键的设计:分清「验过了」和「没验成」

最容易骗过自己的地方,是把**「查了,没有结果」**和**「请求失败了」**当成同一件事。
一个 429 被缓存成干净的 `PREPRINT`,在报告里和一条真正核对过的预印本长得一模一样。

所以每条都会列出它的**独立锚点**:`arXiv:xxxx.xxxxx` / `doi:10.xxxx/...` /
`openreview` / `crossref` / `aminer`。**一个锚点都没有 = 谁也没验过它**,
报告打 🔴 要求人工核原文。带 API 错误的结果永远不会被当成结论缓存,下次会重查。

## 数据源

| 源 | 覆盖 | 不可替代之处 |
|---|---|---|
| **AMiner** ⭐ | 几乎所有 venue,含 CMT 系会议 | **主出处源。** CVPR/ICCV 不在 OpenReview、proceedings 出版前也没有 DOI —— 有好几个月,只有它知道这篇中了。需免费 key |
| **arXiv** | 标题 / 作者 / 日期 | 唯一权威的标题来源,能发现论文改名 |
| **OpenReview** | ICLR / ICML / NeurIPS / COLM | 这些会议**不发 DOI**,Crossref 和 OpenAlex 一律查不到;还能精确到 `ICLR 2026 Oral` |
| **Crossref** | 任何有 DOI 的 | 顺带把 DOI 拿回来 |
| **doi.org** | 任何注册过 DOI 的东西 | 不依赖出版商的内容协商。**没上过 arXiv、没走过 OpenReview 的论文,这是唯一的机器锚点** |
| **DBLP** | 交叉复核 | 屏蔽数据中心 IP,探测一次不通就跳过。家用宽带/校园网上会自动启用 |

arXiv / OpenReview / Crossref / doi.org 全部免 key 免注册;AMiner 需一个免费 key,
没有就自动跳过,不影响其他四源。所有源都按**标题相似度 >0.80** 校验,防止错配。

**AMiner 只决定「选哪个 venue」,不决定细节**:DOI 仍从 Crossref 回填,
录用等级(`Oral` / `spotlight`)仍从 OpenReview 回填。
以某一个源为主,不等于丢掉只有别的源才有的信息。

```bash
export AMINER_API_KEY='...'          # 或
echo '...' > ~/.claude/aminer_key    # chmod 600,脚本自动读
```

> ⚠️ **绝不要把 key 写进仓库。** `.bib` 是要进 git 的,key 一旦提交就永远留在历史里。

## 两个它不会犯的错

**不会把你已经写对的出处改错。** 同一篇论文常同时有会议版和期刊版(VBench 既是
CVPR 2024,也有 TPAMI 记录)。只有当前写着 arXiv 时才去建议列表里挑出处;
已有能识别的正式 venue 时,只统一措辞,绝不换 venue。
*这条是踩出来的:早期版本把 VBench 从 CVPR 2024 悄悄改成了 TPAMI。*

**不会覆盖你的 `note`。** `spotlight` / `oral` / 人工批注是**合并**不是覆盖——
这些 API 查不到,覆盖了就再也回不来。

## 改完之后必须验

```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
grep -cE '^!' main.log                        # LaTeX 错误,须 0
grep -c 'Citation.*undefined' main.log        # 未定义引用,须 0
python3 scripts/bibguard.py references.bib --uncited main.tex
```

⚠️ **不要用 grep 查未引用条目。** `\citep{a,b,%` 换行续写的引用是跨行的,
行式 grep 匹配不到,会把**已经引用的**条目误报成未引用——照着删就会删掉正文在用的引用。
`--uncited` 是跨行匹配的。

## 踩过的坑

在核对一个 60 条的参考文献表时攒下来的。改脚本前先读。

1. **OpenReview 搜索绝不能把整条长标题当 term。** 20 词的完整标题会让相关性排序失效,
   返回一堆 `venue=None` 的空记录,真正的命中被挤出前 12 条 —— 表现为
   "这篇明明中了却查不到"。改成先用冒号前的头部(≤12 词)查,结果仍按全标题相似度校验。
2. **标题漂移只有按 ID 反查才能发现。** arXiv:2401.01256 在很多文献表里叫
   *VideoDrafter*,它的实际标题是 *VideoStudio: Generating Consistent-Content and
   Multi-Scene Videos*。按标题查一无所获,按 ID 查一击命中。**bib 里请写上 arXiv ID。**
3. **`.bib` 里 `%` 不是注释。** 文件头注释块里若出现 `@inproceedings` 字样,
   BibTeX 会当成条目开头,后面整段被跳过。**注释里不能有 `@`。**
4. **OpenReview 的 `CoRR` 记录是 DBLP 镜像的预印本**,既不是发表也不是拒稿。
   算进去会把纯 preprint 误判成 `WORKSHOP_OR_REJECTED`。
5. **Crossref 的会议名常以年份开头**(`2025 IEEE/CVF Conference on ... (CVPR)`),
   venue 白名单正则必须允许前导年份。
6. **用 `(?=\n)` 改写 .bib 会让最后一个字段重复**,因为 entry body 不含结尾换行。
   要按 depth-0 逗号切字段。
7. **有 workshop 记录不等于它是 workshop 论文。** H2O 有 ES-FoMO poster,
   也有 NeurIPS 2023;StreamingT2V 从 ICLR 2025 撤稿,又中了 CVPR 2025。
   判据只能是"有没有任何一个正会记录",绝不能是"字符串里有没有 拒/撤/workshop"。
8. **AMiner 的请求格式很反直觉**:`title` / `page` / `size` 全部走 **query string**。
   用 JSON body 会先报「必填字段 title 不存在」,而如果 body 和 query 混着传,
   **它会静默返回一批完全不相干的论文**(实测第一条是材料学的 XPS 论文)。
   静默错配比报错危险得多。
9. **全局统一 sleep 挡不住限流。** 五个源轮着打,arXiv 那边几秒就来一次,
   跑到一半必 429。要**按 host 分别限速**,并且认 `Retry-After`。
10. **Semantic Scholar 无 key 恒 429**(共享出口 IP 打满);
    **OpenAlex 对 CS 会议没用**——ICLR/ICML/NeurIPS 只返回预印本记录。

## DBLP 为什么在服务器上连不上

2026-08-11 实测(AWS 机器):DNS 正常解析,TCP 443 握手成功,
然后请求在 **0.22s** 后被 RST —— 而握手 RTT 是 **0.11s**。
**RST 恰好在一个来回之后到达,说明它来自对端,不是本地中间盒。**
同机房其他站点都返回 200,包括 DBLP 自己的托管方 `www.dagstuhl.de`。
三个 DBLP 域名表现完全一致。

→ 结论:**DBLP 屏蔽数据中心 IP 段。** 脚本每轮探测一次,不通就静默跳过,
不会在每条引用上白等超时。在家用宽带/校园网上跑会自动启用。
