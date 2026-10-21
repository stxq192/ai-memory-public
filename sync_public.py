# -*- coding: utf-8 -*-
"""把私有记忆库的规则层同步到公开快照仓（带脱敏）。

设计要点（2026-10-22 立）：
- **不是复制粘贴**：公开仓有一层脱敏替换（本机路径 / 客户端具体版本号），
  直接覆盖 core 会把 `C:\\Users\\admin`、`V5.8.2` 这类本机痕迹泄露出去。
- 替换规则集中在 `SCRUB`，一行一条，可审可加。
- `04-focus.md` 是**人工抽象版**（core/04-tasks.md 含项目细节），本脚本**不自动生成**，
  只在缺失时告警；需要改就手改。
- 默认 dry-run，`--write` 才落盘；`--push` 才 commit + push。

用法：
    python sync_public.py              # 只报差异
    python sync_public.py --write      # 落盘（脱敏后）
    python sync_public.py --write --push   # 落盘 + 提交 + 推送 + 写 .last_sync
"""
from __future__ import annotations

import argparse
import datetime as _dt
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PRIVATE_CORE = os.path.normpath(os.path.join(ROOT, "..", "github-ai-profile", "core"))
RULES = os.path.join(ROOT, "rules")
LAST_SYNC = os.path.join(ROOT, ".last_sync")

# 直通映射：core 文件名 -> rules 文件名（04-tasks 不在内：它是私有版，公开侧是 04-focus 抽象版）
PAIRS = [
    ("01-preferences.md", "01-preferences.md"),
    ("02-skills.md", "02-skills.md"),
    ("03-taboos.md", "03-taboos.md"),
    ("05-lessons.md", "05-lessons.md"),
]

# 脱敏规则：(正则, 替换)。顺序有意义，先具体后宽泛。
SCRUB = [
    (r"C:\\Users\\[A-Za-z0-9_\-]+\\ObsidianVault", r"<本机>\\<记忆库>"),
    (r"C:\\Users\\[A-Za-z0-9_\-]+", r"<本机>"),
    (r"[A-Za-z]:\\WorkBuddy\\[^\s`'\"]*", r"<工作区>"),
    (r"WorkBuddy\s*V\d+(?:\.\d+)+", "客户端当前基线版本"),
    (r"\bV\d+\.\d+\.\d+\b", "当前版本"),
    (r"stxq192", "<账号>"),
    (r"1[3-9]\d{9}", "<手机号>"),
]

# 脱敏后仍不该出现的词（命中即判失败，不落盘）
FORBIDDEN = ["C:\\Users\\", "ObsidianVault", "stxq192", "账号2", "muyou", "quant-lab", "涨停猎手"]


def scrub(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    for pat, rep in SCRUB:
        new, n = re.subn(pat, rep, text)
        if n:
            hits.append("%s -> %s ×%d" % (pat, rep, n))
        text = new
    return text, hits


def read(p: str) -> str:
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(PRIVATE_CORE):
        print("[FAIL] 私有 core 不存在：%s" % PRIVATE_CORE)
        return 2

    changed = []
    for src_name, dst_name in PAIRS:
        src = os.path.join(PRIVATE_CORE, src_name)
        dst = os.path.join(RULES, dst_name)
        if not os.path.isfile(src):
            print("[WARN] 缺源文件 %s（跳过）" % src)
            continue
        cleaned, hits = scrub(read(src))
        old = read(dst) if os.path.isfile(dst) else ""
        if cleaned == old:
            print("[SAME] %s" % dst_name)
            continue
        bad = [w for w in FORBIDDEN if w in cleaned]
        if bad:
            print("[FAIL] %s 脱敏后仍含敏感词 %s —— 拒绝写入" % (dst_name, bad))
            return 3
        changed.append(dst_name)
        print("[DIFF] %s  (+%d 行)" % (dst_name, cleaned.count("\n") - old.count("\n")))
        for h in hits:
            print("        脱敏 %s" % h)
        if args.write:
            with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
                f.write(cleaned)

    if not os.path.isfile(os.path.join(RULES, "04-focus.md")):
        print("[WARN] 缺 rules/04-focus.md（人工抽象版，需手写，不由本脚本生成）")

    if not changed:
        print("\n无变更。")
        return 0
    if not args.write:
        print("\n[DRY-RUN] %d 个文件待更新，加 --write 落盘。" % len(changed))
        return 0

    if not args.push:
        print("\n已落盘 %d 个文件（未提交，未推送）。" % len(changed))
        return 0

    day = _dt.date.today().isoformat()
    cmds = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", "mem(sync): 规则层同步 %s" % day],
        ["git", "push"],
    ]
    for c in cmds:
        r = subprocess.run(c, cwd=ROOT, capture_output=True)
        out = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
        print("$ %s -> rc=%d %s" % (" ".join(c), r.returncode, out.splitlines()[-1] if out else ""))
        if r.returncode != 0:
            print("[FAIL] 中止，未写 .last_sync")
            return 4
    with io.open(LAST_SYNC, "w", encoding="utf-8", newline="\n") as f:
        f.write(day + "\n")
    print("完成：%d 个文件已推送，.last_sync = %s" % (len(changed), day))
    return 0


if __name__ == "__main__":
    sys.exit(main())
