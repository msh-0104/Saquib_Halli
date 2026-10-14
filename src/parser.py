import subprocess
import re

SECRET_PATTERNS = [
    re.compile(r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{16,}['\"]?", re.IGNORECASE),
    re.compile(r"password['\"]?\s*[:=]\s*['\"]?[^'\"]{6,}['\"]?", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE)
]

def get_git_diff():
    try:
        result = subprocess.run(["git", "diff", "HEAD~1", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return ""

def sanitize_diff(diff_text):
    sanitized = diff_text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized

def parse_diff_summary(diff_text):
    lines = diff_text.splitlines()
    modified_files = []
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split("b/")
            if len(parts) > 1:
                modified_files.append(parts[1])
    return list(set(modified_files))
