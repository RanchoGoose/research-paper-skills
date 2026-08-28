---
name: bibguard
description: 写 paper 时所有 reference 与 citation 的唯一入口——新增一条引用(查证后自动生成格式正确的 bib 条目)、核实每条引用真实存在、查出真正的会议/期刊出处、按统一格式(会议一律 "Proceedings of 全称")改写 .bib、揪出被拒/仅 workshop 以及正文没引用的条目。**写论文时凡涉及引用一律走这个 skill,不要凭记忆手写 bib 条目。** 触发词:加引用、补引用、引用这篇、这篇发在哪、引文核对、查 venue、references、参考文献、bib、citation、cite、bibliography、引用格式、投稿前检查。
---

# 写 paper 的引用总管(bibguard)

**一条铁律:凡是往 `.bib` 里写东西,都走这个 skill,不要凭记忆手写条目。**
模型记忆里的引用有相当比例是错的——标题对但作者错、年份错、会议错,甚至整篇不存在。
这个 skill 的全部意义就是让每一条引用都有来源可查。

一个 skill 管四件事:**① 加引用 ② 这篇论文真的存在吗 ③ 它到底发在哪 ④ 全篇格式统一**。

Resolve this installed skill's own directory first; do not assume a Claude- or Codex-specific install path. In the examples below, `S` is the absolute path to this skill's `scripts/bibguard.py`:

```bash
S=/absolute/path/to/bibguard/scripts/bibguard.py

python3 $S references.bib --add "<论文标题>"    # 查证后生成并追加一条(查不到就拒绝)
python3 $S references.bib --add 2506.08009     # 也能直接给 arXiv id 或 DOI
python3 $S references.bib                      # 核对 + 报告(读缓存,可安全重跑)
python3 $S references.bib --fix                # 把出处和格式写回 .bib(自动存 .bak)
python3 $S references.bib --only k1,k2         # 只查这几条
python3 $S references.bib --refresh            # 忽略缓存重查(投稿前必做)
python3 $S references.bib --uncited main.tex   # 列出正文没引用的条目
python3 $S references.bib --json r.json        # 机器可读输出
python3 $S references.bib --pause 2            # 限流严重时在每个源的最小间隔上再加秒数
```

退出码 **0 = 无需改动;1 = 有条目待处理**,可直接当投稿前 gate。
缓存在 `.refcache.json`(与 .bib 同目录,记得 gitignore),中断重跑不会重复请求。
`--refresh` 只是「不信我这次要查的那几条的缓存」,**不会删掉它没碰的行**——
配合 `--only` 时尤其重要:一次 `--only X --refresh` 曾把 63 行缓存清成 4 行,
下一次全量因此要重查所有条目,直接撞上限流,把几分钟前刚验过的条目报成未验证。

改脚本前先跑 `python3 /absolute/path/to/bibguard/tests/test_offline.py`（纯离线，不联网）。

## 加一条引用:`--add`

给标题、arXiv id 或 DOI 都行。它会先把这篇论文查证一遍,再生成条目:

```bash
$ python3 $S references.bib --add "LongLive: Real-time Interactive Long Video Generation"

标题  : LongLive: Real-time Interactive Long Video Generation
出处  : Proceedings of the International Conference on Learning Representations (ICLR)
锚点  : arXiv:2509.22622, openreview, aminer
证据  : OR:ICLR 2026 Poster || AMINER:ICLR 2026 (2026) [proceedings-article]

@inproceedings{longlive2026,
  title     = {{LongLive}: Real-time Interactive Long Video Generation},
  author    = {Yang, Shuai and Huang, Wei and ... and Chen, Yukang},
  booktitle = {Proceedings of the International Conference on Learning Representations (ICLR)},
  year      = {2026},
  note      = {Poster; arXiv:2509.22622}
}
```

生成时自动处理掉几个手写必错的细节:

- **作者名反转**成 BibTeX 要的 `Last, First`,小写介词跟着姓走(`van den Berg, Rianne`)。
- **缩写加花括号**:`{MuKV}` / `{KV}` / `{NVFP4}`,否则某些 `.bst` 会渲染成 `Mukv`。
  连字符词按普通标题大小写处理,`Multi-Grained`、`Train-Test` 不会被多余地括起来。
- **citation key** 跟全篇同一套写法:标题冒号前的短名 + 年份 → `longlive2026`、`mukv2026`;
  撞 key 自动加后缀。
- **标题、作者、年份全部取自权威记录**,不用你提供的那一版(你给的可能是旧名)。

三种它会**拒绝写入**的情况(这是 guard 的部分):

| 情况 | 行为 |
|---|---|
| 查不到这篇 | ✗ 拒绝,提示换个标题或给 id。**绝不编一条看起来很像真的** |
| 查到标题但没有任何独立锚点 | ✗ 拒绝,要求人工核原文后手写 |
| 这篇已经在 .bib 里了 | · 提示已存在的 key,并告诉你用 `--only <key> --fix` 更新出处 |

`--dry-run` 只打印不写文件。写入前自动存 `.bak`。

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
`openreview` / `crossref` / `aminer`。**一个锚点都没有 = 谁也没验过它**。
带错误的缓存行会被自动重查,缓存有 schema 版本号,升级后旧行自动失效。

> 判断口径:锚点数 ≥1 才算"这篇确实存在且写法对得上";
> 锚点数 = 0 的条目,**没有任何机器证据**,只能人工打开原文确认。

**但零锚点有两种,报告必须分开说。**「查过了、都没命中」和「根本没查成」在锚点这一层
长得一模一样:429 或超时会让三个源同时空手而归。混为一谈是危险的——它把一条**正确的**
条目报成「查无此文」,而读到这句话的下一步动作是去改它。实测:一轮 63 条的全量重查里
4 条标了红,四条的 `errs` 全是 429、`arxiv_title` 全是 `None`,查询压根没发出去。

- 🔴 **无独立验证锚点**:三个源都答了,都没命中 → 人工打开原文。
- 🟡 **本轮未验证**:源被限流/超时 → 不是查无此文,**单独 `--only <key> --refresh` 重跑**。

两种都算「需处理」(没验过就是没过,退出码仍是 1),但结论不同,动作也不同。
全量 `--refresh` 很容易撞限流,所以收尾那一遍看到 🟡 先重跑,不要照着改 `.bib`。

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
4. **上面全没有 → 先看 `API错误` 那行**。有 429/超时就是 🟡 本轮没查成,重跑本条;
   真的三源都答了还没命中才是 🔴,人工核原文。典型的 🔴 是**厂商技术报告**(没有
   venue、没有 DOI):只能人工打开原文/官网确认,**并把确认结果写进 `note`**,
   让下一个人知道验过了。
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
| `🔴无独立验证锚点` | 三源都答了、都没命中 | 必须人工打开原文 |
| `🟡本轮未验证` | 源被限流/超时,**查询没发出去** | `--only <key> --refresh` 重跑,别改 bib |
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
npx skills add RanchoGoose/research-paper-skills --skill bibguard -g -a codex -y
npx skills add RanchoGoose/research-paper-skills --skill bibguard -g -a claude-code -y
```

只依赖 Python 3 标准库，无需 pip、无需 API key。
公开仓库：https://github.com/RanchoGoose/research-paper-skills
