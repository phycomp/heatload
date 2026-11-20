from pathlib import Path
from typing import Dict, Optional

# =============== 新增 + 原有 的最常用 magic 表 ===============
MAGIC_MAP: Dict[bytes, str] = {
    # ========= 圖片 =========
    b"\x89PNG": "image/png",
    b"\xFF\xD8\xFF": "image/jpeg",  # JPEG/JFIF
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"BM": "image/bmp",
    b"RIFF": "image/webp",  # WebP 以 RIFF 開頭
    b"\x00\x00\x01\x00": "image/x-icon",  # .ico

    # ========= 視頻 =========
    b"\x00\x00\x00\x18ftypmp42": "video/mp4",  # MP4 (iso)
    b"\x00\x00\x00\x20ftypiso2": "video/mp4",  # MP4 (iso2)
    b"\x1A\x45\xDF\xA3": "video/webm",  # WebM
    b"ftypisom": "video/mp4",  # 短前綴兜底 MP4
    b"ftypMSNV": "video/mp4",  # MP4 (MS)

    # ========= 文檔 =========
    b"PK\x03\x04": "application/zip",  # 通用 ZIP（含 docx/xlsx/pptx）
    b"PK\x05\x06": "application/zip",  # 空 ZIP
    b"%PDF": "application/pdf",
    b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1": "application/vnd.ms-excel",  # .xls
    b"SQLite format 3\x00": "application/x-sqlite3",

    # ========= 新增：PowerPoint / Office =========
    b"PK\x03\x04\x14\x00\x06\x00": "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
    b"PK\x03\x04\x14\x00\x08\x00": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    b"PK\x03\x04\x14\x00\x09\x00": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx

    # ========= 新增：HTML =========
    b"<!DOCTYPE html": "text/html",
    b"<html": "text/html",
    b"<HTML": "text/html",
    b"<head": "text/html",
    b"<HEAD": "text/html",

    # ========= 新增：Markdown =========
    b"# ": "text/markdown",  # 以 # 開頭的文本文件
    b"## ": "text/markdown",
    b"- ": "text/markdown",
    b"* ": "text/markdown",
    b"---": "text/markdown",  # 分隔符

    # ========= 壓縮包 =========
    b"\x1f\x8b\x08": "application/gzip",
    b"7z\xBC\xAF\x27\x1C": "application/x-7z-compressed",
    b"Rar!\x1A\x07\x00": "application/x-rar-compressed",

    # ========= 可執行 / 二進制 =========
    b"MZ": "application/x-dosexec",  # PE/EXE/DLL
    b"\x7FELF": "application/x-elf",  # ELF
}

# 最長匹配長度
MAX_LEN = max(len(m) for m in MAGIC_MAP)


def 麥魔(檔徑: Path) -> Optional[str]:
    """
    讀取文件頭 magic bytes 返回 MIME 類型
    返回 None 表示未命中任何已知 magic（可能是純文本或未知二進制）
    """
    if not 檔徑.is_file():
        return None

    with 檔徑.open("rb") as f:
        head = f.read(MAX_LEN)

    # 最長匹配優先
    for magic, mime in MAGIC_MAP.items():
        if head.startswith(magic):
            return mime
    return 檔徑.suffix


# ==================== CLI 演示 ====================
if __name__ == "__main__":
    import sys
    for path_str in sys.argv[1:]:
        p = Path(path_str)
        mime = mime_from_magic(p)
        print(f"{p}\t{mime or 'unknown/unknown'}")
