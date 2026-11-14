# book80

[English](./README.md) | **中文**

一个 agent skill：把一本 EPUB 或 PDF 压成 30 秒、3 分钟、10 分钟三档 briefing，每个关键结论都能追溯回书里原来的位置。

目标是单位时间的理解量，而非逐页覆盖率：快速拿到一本书价值最高的 80%，同时随时能查证原文。

## 它做什么

- 支持 EPUB、文字版或扫描版 PDF、纯文本、Markdown、HTML 和 DOCX。
- 提取文本时保留**稳定定位符**（页码、章节加小标题、EPUB spine 序号），briefing 里的每条结论都能指回出处。提取不到的部分会明确报告，绝不悄悄糊弄过去。
- 按阅读目标调整：快速理解、工作应用、批判性阅读、内容创作、备考学习。
- 输出三档深度（30 秒、3 分钟、10 分钟），另可生成一个独立的交互式 HTML 阅读器。
- 只给书名不给文件时，它会说明情况，改为从公开资料做综述，并明确标注这不是基于原文的提取。

## 安装

```bash
git clone https://github.com/qianquandong/book80-skill.git ~/.claude/skills/book80-skill
```

Claude Code 和 Codex 都能用。EPUB 提取器是纯 Python 脚本，零第三方依赖：

```bash
python3 scripts/extract_epub.py BOOK.epub --output-dir extracted/
```

## 使用

把书的文件丢给它：

> 帮我拆 ~/Books/thinking-fast-and-slow.epub，我要 3 分钟版，偏工作应用。

或者直接要一份书籍摘要。skill 默认走快速理解模式，只有答案会实质影响结果时才多问一句。

## 文件

| 路径 | 是什么 |
|------|--------|
| `SKILL.md` | agent 遵循的完整流程 |
| `scripts/extract_epub.py` | EPUB 拆章节加 manifest，只用标准库 |
| `scripts/build_html_report.py` | 生成可选的交互式 HTML 阅读器 |
| `references/` | 配套参考资料 |

## License

MIT
