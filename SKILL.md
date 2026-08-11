---
name: ref-verify
description: 论文引用一条龙——核实每条引用真实存在、查出真正的会议/期刊出处、按统一格式(会议一律 "Proceedings of 全称")改写 .bib,并揪出被拒/仅 workshop 的论文。用于投稿前引文核查、补新引用、统一引用格式、或任何"这篇到底真不真/发在哪/该怎么写"的问题。触发词:引文核对、查 venue、references 核对、bib 更新、引用格式、统一格式、投稿前检查、citation check、verify references、bibliography。
---

# 论文引用核对与格式统一(ref-verify)

一个 skill 管三件事:**① 这篇论文真的存在吗 ② 它到底发在哪 ③ 全篇引用格式统一**。

```bash
S=.claude/skills/ref-verify/scripts/verify_refs.py

python3 $S references.bib                 # 核对 + 报告(默认读缓存,可安全重跑)
python3 $S references.bib --fix           # 顺便把出处和格式写回 .bib(自动存 .bak)
python3 $S references.bib --only k1,k2    # 只查这几条
python3 $S references.bib --refresh       # 忽略缓存重查(投稿前必做)
python3 $S references.bib --json r.json   # 机器可读输出
python3 $S references.bib --uncited main.tex   # 列出正文没引用的条目
python3 $S references.bib --pause 2       # 限流严重时在每个源的最小间隔上再加秒数
```

退出码 **0 = 无需改动;1 = 有条目待处理**,可直接当投稿前 gate。
缓存在 `.refcache.json`(与 .bib 同目录,记得 gitignore),中断重跑不会重复请求。

改脚本前先跑 `python3 tests/test_offline.py`(纯离线,不联网)。

## 铁律一:收录标准

默认口径:**只收两类 ①已在正式会议/期刊发表的 ②仍在正常评审中的 preprint。**
被拒、撤稿后无下文、只有 workshop poster 的一律不引。
(这是个可以按项目调整的编辑口径,脚本只负责把事实查清楚并标出来,删不删由人定。)

🚨 **判据只有一条:该论文有没有任何一个正会/期刊出处。不是"有没有出现拒/撤/workshop 字样"。**
下面这些**全都必须保留**:

| 论文 | 干扰记录 | 真实出处 |
|---|---|---|
| H2O | ES-FoMO 2023 Poster(workshop) | **NeurIPS 2023** |
| InfLLM | LCFM 2024(workshop) | **NeurIPS 2024** |
| StreamingT2V | ICLR 2025 Withdrawn Submission | **CVPR 2025**(撤稿后转投) |
| Sparse VideoGen | ICLR 2026 Desk Rejected | **ICML 2025**(被拒的是后续扩展投稿) |

## 铁律二:已经写对的出处不许改

**同一篇论文常同时有会议版和期刊版**(VBench 既是 CVPR 2024,也有 TPAMI 记录)。
脚本只在**当前写的是 arXiv preprint** 时才去建议列表里挑出处;
**bib 里已有一个能识别的正式 venue 时,只统一措辞,绝不换 venue。**

> 这条是踩出来的:早期版本按"建议列表第一条"改写,把 VBench 从 CVPR 2024 悄悄改成了 TPAMI 期刊。

同理,`note` 字段是**合并**不是覆盖——里面的 `spotlight` / `oral` / 人工批注 API 查不到,覆盖就没了。

## 铁律三:分清「验过了」和「没验成」

这是最容易骗过自己的地方。早期版本把 **API 报错**和**查过了没结果**缓存成同一种东西:
一条关键引用因为 arXiv 429 被缓存成 `PREPRINT`,报告里和一条真正核对过的 preprint
长得一模一样——**而它正是全文承重的对照引用**。

现在每条都会列出**独立锚点**(anchors):`arXiv:xxxx.xxxxx` / `doi:10.xxxx/...` /
`openreview` / `crossref` / `aminer`。**一个锚点都没有 = 谁也没验过它**,报告会打 🔴
要求人工核原文。带错误的缓存行会被自动重查,缓存有 schema 版本号,升级后旧行自动失效。

> 判断口径:锚点数 ≥1 才算"这篇确实存在且写法对得上";
> 锚点数 = 0 的条目,**没有任何机器证据**,只能人工打开原文确认。

## 格式统一规则

`--fix` 会把全篇改成一致写法:

| 类型 | 条目类型 | 字段 | 写法 |
|---|---|---|---|
| 会议 | `@inproceedings` | `booktitle` | `Proceedings of the <官方全称> (<缩写>)` |
| 期刊 | `@article` | `journal` | 官方刊名全称,如 `IEEE Transactions on Pattern Analysis and Machine Intelligence` |
| preprint | `@article` | `journal` | `arXiv preprint arXiv:XXXX.XXXXX` |

⚠️ **`booktitle` 里不要写 "In"**——`.bst` 自己会加,写了会变成 "In In Proceedings of..."。
全称表在 `scripts/venues.json`,新会议往里加一条即可(`match` 是小写匹配串,最长匹配优先)。

`note` 统一收 `spotlight/oral; doi:...; arXiv:...` 这类补充信息。

## 五个源的分工,以 AMiner 为主

| 源 | 端点 | 覆盖 | 不可替代之处 |
|---|---|---|---|
| **AMiner** ⭐主 | `datacenter.aminer.cn/.../paper/search` | 几乎所有 venue,含 CMT 系会议 | ⭐ **主出处源。** CVPR/ICCV 不进 OpenReview,proceedings 出版前也没有 DOI —— **有好几个月,只有它知道这篇中了**。云主机上通(实测 200),正好补上 DBLP 被封的那块。需免费 key |
| **arXiv API** | `export.arxiv.org/api/query` | title / authors / 日期 | 唯一权威的作者与标题来源,能发现论文改名 |
| **OpenReview API2** | `api2.openreview.net/notes/search` | **ICLR / ICML / NeurIPS / COLM** | ⭐ 这些会议**不发 DOI**,Crossref 和 OpenAlex 一律查不到;精确到 `ICLR 2026 Oral` |
| **Crossref** | `api.crossref.org/works` | 任何有 DOI 的 | 有 DOI 的都在这儿,顺带拿回 DOI |
| **doi.org 解析** | `doi.org` 内容协商 | **任何注册过 DOI 的东西** | ⭐ 不依赖出版商:按 DOI 直接向注册机构取回权威标题与出处。**没上过 arXiv、没走过 OpenReview 的论文,这是唯一的机器锚点** |
| **DBLP**(半个) | `dblp.org/search/publ/api` | 交叉复核 | 云主机上基本用不了,脚本探测一次就跳过;家用宽带/校园网会自动启用 |

arXiv / OpenReview / Crossref / doi.org 全部免 key 免注册;AMiner 需一个免费 key。
**全部**按标题相似度校验(>0.80)防错配。

**「以 AMiner 为主」是有边界的:它只决定选哪个 venue,不决定细节。**
选定 venue 之后,脚本会回头在**所有认同同一个 venue 的源**里捞:
DOI 从 Crossref 拿,录用等级(`Oral` / `spotlight`)从 OpenReview 拿。
**以某个源为主,不等于丢掉只有别的源才有的信息。**

**AMiner key 怎么给**(三选一,**绝不要写进仓库**——bib 是要进 git 的,key 一旦提交就留在历史里):

```bash
export AMINER_API_KEY='...'            # 1. 环境变量
echo '...' > ~/.claude/aminer_key      # 2. 家目录文件(chmod 600),脚本自动读
export AMINER_KEY_FILE=/path/to/key    # 3. 自定义路径
```

没有 key 就自动跳过,不报错、不影响其他四源。`--no-aminer` 可强制关闭。

⚠️ **AMiner 的请求格式很反直觉**:`title` / `page` / `size` 全部走 **query string**,
用 JSON body 会先报「必填字段 title 不存在」,而如果 body 和 query 混着传,
**它会返回一批完全不相干的论文**(实测第一条是材料学的 XPS 论文)——静默错配比报错危险得多。

## 不在 arXiv、也不在 OpenReview 的论文怎么办

按覆盖面依次落到下面几层,**层层都查不到才算无锚点**:

1. **AMiner 按标题查**。它对 CMT 系会议(CVPR/ICCV/ACM MM 等)覆盖最好,
   而这些会议在 proceedings 出版前既没有 DOI、也不在 OpenReview 上,别的源都是瞎的。
2. **有 DOI → doi.org 解析**。CVPR/ICCV/ECCV/ACL/SIGGRAPH/期刊/LNCS 都有 DOI,
   这一路和 arXiv、OpenReview 完全无关。脚本会从 `note`/`journal`/`doi` 字段里
   抓 `10.xxxx/...` 自动去解析,并校验返回的标题对得上(>0.80)。
3. **没 DOI 但进了正会 → Crossref / OpenReview 按标题反查**。ECCV 走 LNCS(book-chapter),
   ICLR/ICML/NeurIPS 没有 DOI 只能靠 OpenReview——这也是为什么这两个源缺一不可。
4. **上面全没有 → 🔴 无锚点,人工核原文**。典型是**厂商技术报告**(没有 venue、没有 DOI)。
   只能人工打开原文/官网确认,**并把确认结果写进 `note`**,让下一个人知道验过了。
5. **标题漂移是这一层最常见的坑**:论文改名后 arXiv 还是旧标题,或反过来。
   实测:很多文献表把 arXiv:2401.01256 引成 **VideoDrafter**,它的实际标题是
   **VideoStudio: Generating Consistent-Content and Multi-Scene Videos**。
   **只有按 arXiv id 反查标题才能发现。**
   → 所以宁可在 bib 里写上 arXiv id:它让这条从"标题查不到"变成"id 直接命中"。

## DBLP 为什么连不上(2026-08-11 实测)

**不是 SNI 审查,也不是 DNS,是 DBLP 自己在拒绝云主机出口 IP。** 证据:

- DNS 正常解析,**TCP 443/80 都能握手成功**;
- 但请求发出后 **0.22s** 被 RST,而 TCP 握手 RTT 是 **0.11s**——
  **RST 恰好在一个来回之后到达,说明它来自对端,不是本地中间盒**(本地拦截会是 ~0ms);
- 同机房的 `www.dagstuhl.de`(DBLP 就托管在 Dagstuhl)和 `www.uni-trier.de` **都返回 200**,
  所以不是链路问题;
- 三个域名(`dblp.org` / `dblp.uni-trier.de` / `dblp.dagstuhl.de`)**全部一样失败**;换 UA 无效。

→ 结论:**DBLP 屏蔽数据中心 IP 段**(反爬常规操作)。脚本每轮**探测一次**,不通就静默跳过。
**在家用宽带/校园网上跑,DBLP 会自动启用**,多一路交叉验证。

## 其他踩过的坑(改脚本前必读)

1. **OpenReview 搜索不能把整条长标题当 term**。20 词的完整标题会让相关性排序失效,
   返回一堆 `venue=None` 的空记录,真正的命中被挤出前 12 条 —— 表现为"这篇明明中了却查不到"。
   → 脚本改成**查询词截到 12 词**(标题头部若够长则只用头部),结果仍按全标题相似度校验。
2. **全局统一 sleep 挡不住限流**。五个源轮着打,arXiv 那边每几秒就来一次,跑到一半必 429。
   → 必须**按 host 分别限速**(arXiv ≥4s),并且认 `Retry-After`。
   实测:改之前 60 条跑一半就挂满 429;改之后零错误。
3. **Semantic Scholar 无 API key 恒 429**(共享出口 IP 打满),重试无用;要用得先申请 key。
4. **OpenAlex 对 CS 会议没用**:ICLR/ICML/NeurIPS 只返回 arXiv preprint 记录。故不用它。
5. **`.bib` 里 `%` 不是注释**。文件头注释块里若出现 `@inproceedings` / `@article` 字样,
   BibTeX 会当成条目开头 → `I'm skipping whatever remains of this entry`。**注释里不能有 `@`**。
6. **OpenReview 的 `CoRR` 记录是 DBLP 镜像的 preprint**,既不是发表也不是拒稿,必须完全忽略,
   否则会把纯 preprint 误判成 WORKSHOP_OR_REJECTED。
7. **Crossref 的会议名常以年份开头**(`2025 IEEE/CVF Conference on ... (CVPR)`),
   白名单正则必须允许前导年份。
8. **改 bib 的正则陷阱**:`(?=\n)` 匹配不到条目的**最后一个字段**(entry body 不含结尾换行),
   会导致 `year`/`note` 重复。按 depth-0 逗号切字段。
9. **`venues.json` 的 booktitle 必须能被 `canon_venue` 认回自己**,否则 `--fix` 每跑一次都
   "改"一遍同一条。测试里有这条不变量。

## 输出状态

| 状态 | 含义 | 该怎么办 |
|---|---|---|
| `PUBLISHED` | 找到正会/期刊出处 | bib 若还写 arXiv → `--fix` 自动改 |
| `PREPRINT` | 查不到任何 venue | 保持 `@article` + arXiv,正常 |
| `WORKSHOP_OR_REJECTED` | 只有 workshop / 拒稿 / 投稿中 | ⛔ 按收录标准处理 |
| `📝标题与 arXiv 官方不一致` | 标题写错 | `--fix` 按 arXiv 官方标题更正 |
| `⚠️ 写了正式出处但查不到` | 可能是 tech report | 人工确认 |
| `🔴无独立验证锚点` | **谁也没验过它** | 必须人工打开原文 |
| `🔧格式待统一` | venue 对但写法不统一 | `--fix` 归一 |

## 改完之后必须验

```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
grep -cE '^!' main.log                      # LaTeX 错误,须 0
grep -c 'Citation.*undefined' main.log      # 未定义引用,须 0
bibtex main 2>&1 | grep -i warning          # 重复字段之类,须空
python3 $S references.bib --uncited main.tex   # bib 里没被正文引用的条目
```

⚠️ **不要用 `grep` 查未引用条目**。`\citep{a,b,%` 换行续写的引用是跨行的,行式 grep
匹配不到,会把**已经引用的**条目误报成 UNCITED —— 照着删就会删掉正文在用的引用。
`--uncited` 是跨行匹配的,用它。

删除某条引用时,**同时删 bib 条目和正文的 `\citep{}`**,并检查删掉后那句话是否还通顺。

## 投稿前

新挂的 preprint 会陆续中会,**投稿前务必 `--refresh` 全量重跑一次**,把新中会的补成正式出处。
60 条约 20 分钟(按 host 限速,慢是故意的)。

## 装到别的项目 / 分享给别人

```bash
bash install.sh /path/to/other-project   # 装到某个项目
bash install.sh --user                   # 装到 ~/.claude/skills(全局可用)
```

只依赖 Python 3 标准库,无需 pip、无需 API key。
公开仓库:https://github.com/RanchoGoose/ref-verify
