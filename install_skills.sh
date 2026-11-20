#!/usr/bin/env bash
# 安裝所有 skills 至目標主機（可重現）
# 用法: bash install_skills.sh [TARGET_DIR]
# TARGET_DIR 預設為當前目錄
# 來源：本腳本所在目錄

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

echo "=== 安裝 skills 至 $TARGET_DIR ==="
echo "來源: $SCRIPT_DIR"

# 1. 本專案內建 skills
mkdir -p "$TARGET_DIR/.opencode/skills"
for skill in refactor quantum-cryogenic-cable; do
    if [ -d "$SCRIPT_DIR/.opencode/skills/$skill" ]; then
        rm -rf "$TARGET_DIR/.opencode/skills/$skill"
        cp -r "$SCRIPT_DIR/.opencode/skills/$skill" "$TARGET_DIR/.opencode/skills/"
        echo "已複製 skill: $skill"
    fi
done

# 2. 安裝 superpowers（obra）
echo "=== 安裝 obra/superpowers ==="
npx skills add https://github.com/obra/superpowers -g -y 2>&1 | tail -3 || echo "superpowers 安裝失敗，請手動執行"

# 3. 驗證
echo "=== 驗證 ==="
ls "$TARGET_DIR/.opencode/skills/"
echo "完成。請執行 /reload 載入新 skills。"
PY