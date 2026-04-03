---
inclusion: always
---

# 文件编码安全规范

## 背景
本项目曾多次出现 UTF-8 编码损坏问题：中文三字节字符的第三个字节被截断为 `?`（0x3F），
导致后端无法启动（UnicodeDecodeError / SyntaxError）。

## 写入文件时的强制规则

1. 写入包含中文的 Python 文件后，必须用 `getDiagnostics` 验证文件无语法错误
2. 如果单次写入内容超过 40 行且包含中文，拆分为多次小写入（fsWrite + fsAppend）
3. 中文注释和字符串中，确保所有引号正确闭合：
   - `comment="xxx"` 不能写成 `comment="xxx`
   - `"""docstring"""` 不能写成 `"""docstring""`
4. 写入后如果发现 UnicodeDecodeError 或 SyntaxError: unterminated string，立即修复

## 编码损坏的典型症状
- `UnicodeDecodeError: 'utf-8' codec can't decode bytes`
- `SyntaxError: unterminated string literal`
- `SyntaxError: unterminated triple-quoted string literal`
- 中文字符显示为 `�` 或末尾被截断（如 "角色表" 变成 "角色"）
