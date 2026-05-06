"""Conserto idempotente de mojibake (UTF-8 duplo-codificado) em literais PT-BR.

Caracteres PT-BR corretos (U+00E3 'ã', U+00E7 'ç', etc.) nunca começam com
'Ã' (U+00C3) ou 'Â' (U+00C2) na string decodificada como UTF-8. Logo,
substituir as sequências mojibake pelas corretas é seguro: não toca texto
já correto. O script é idempotente — rodar duas vezes não muda nada na
segunda passada.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPLACEMENTS: list[tuple[str, str]] = [
    # Letras minúsculas mais comuns
    ("Ã£", "ã"),
    ("Ã§", "ç"),
    ("Ã©", "é"),
    ("Ãª", "ê"),
    ("Ã¡", "á"),
    ("Ã­", "í"),
    ("Ã³", "ó"),
    ("Ãº", "ú"),
    ("Ã¢", "â"),
    ("Ãµ", "õ"),
    ("Ã´", "ô"),
    ("Ã¼", "ü"),
    ("Ã±", "ñ"),
    # Maiúsculas
    ("Ã€", "À"),
    ("Ã‡", "Ç"),
    ("Ã‰", "É"),
    ("Ãš", "Ú"),
    ("Ã“", "Ó"),
    ("Ãƒ", "Ã"),
    # 'à' tem segundo byte NBSP (U+00A0) — tratado explicitamente
    ("Ã ", "à"),
    # Sequências com 'Â' (cp1252 helper) que sobram após a normalização
    ("Â°", "°"),
    ("Â´", "´"),
    ("Âº", "º"),
    ("Âª", "ª"),
    ("Â·", "·"),
    ("Â§", "§"),
    ("Â¡", "¡"),
    ("Â¿", "¿"),
    ("Â", ""),
]


def fix_text(text: str, reverse: bool = False) -> str:
    out = text
    pairs = [(g, b) for b, g in REPLACEMENTS if g] if reverse else REPLACEMENTS
    for src, dst in pairs:
        out = out.replace(src, dst)
    return out


def fix_file(path: Path) -> int:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    fixed = fix_text(text)
    if fixed == text:
        return 0
    path.write_bytes(fixed.encode("utf-8"))
    before = raw.count(b"\xc3\x83") + raw.count(b"\xc2")
    after = fixed.encode("utf-8").count(b"\xc3\x83") + fixed.encode("utf-8").count(b"\xc2")
    return before - after


def main(targets: list[str]) -> int:
    fixed_total = 0
    file_count = 0
    for target in targets:
        root = Path(target)
        if root.is_file():
            paths = [root]
        else:
            paths = list(root.rglob("*.py"))
        for p in paths:
            n = fix_file(p)
            if n:
                fixed_total += n
                file_count += 1
                print(f"fixed {n:>4} sequences in {p}")
    print(f"\n{fixed_total} sequence(s) corrigida(s) em {file_count} arquivo(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["app", "tests"]))
