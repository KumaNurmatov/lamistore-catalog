#!/usr/bin/env python3
"""Заливает текстуры по подписанным ссылкам media_upload и копит media_id.

Ответ media_upload огромный из-за подписанных ссылок, поэтому разбираем его
файлом, а не глазами. Имена файлов в ответе идут в том же порядке, что и в запросе.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "textures"
MAP = ROOT / "data" / "media_ids.json"

def main():
    resp_file, names_json = sys.argv[1], sys.argv[2]
    names = json.loads(names_json)
    uploads = json.loads(pathlib.Path(resp_file).read_text(encoding="utf-8"))["uploads"]
    assert len(uploads) == len(names), f"{len(uploads)} ссылок на {len(names)} файлов"

    ids = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    ok, bad = [], []
    for name, up in zip(names, uploads):
        src = TEX / name
        if not src.exists():
            bad.append((name, "нет файла")); continue
        r = subprocess.run(["curl", "-sS", "-X", "PUT", "-m", "180",
                            "-H", f"Content-Type: {up['content_type']}",
                            "--upload-file", str(src), up["upload_url"],
                            "-o", "/dev/null", "-w", "%{http_code}"],
                           capture_output=True, text=True)
        code = r.stdout.strip()
        if code == "200":
            ids[name] = up["media_id"]; ok.append(up["media_id"])
        else:
            bad.append((name, f"HTTP {code}"))
    MAP.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"залито: {len(ok)}   ошибок: {len(bad)}")
    for n, why in bad:
        print(f"   {n}: {why}")
    print("ПОДТВЕРДИТЬ:", json.dumps(ok))

if __name__ == "__main__":
    main()
