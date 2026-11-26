"""Ovoz plaginining komanda satri interfeysi.

  python -m voice doctor
  python -m voice catalog
  python -m voice speak "Salom dunyo" --category qiz --out salom.wav
  python -m voice clone "Salom" namuna.wav --category child --out klon.wav
  python -m voice convert namuna.wav boy --out bola.wav
  python -m voice stream "Uzun matn ..." --out-dir chunks
  python -m voice serve --port 8765
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .engine import VoiceEngine


def _print(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m voice", description="Lokal ovoz plagi")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Diagnostika")
    sub.add_parser("catalog", help="Modellar va toifalar")

    speak = sub.add_parser("speak", help="Matndan WAV yaratish")
    speak.add_argument("text")
    speak.add_argument("--category", default="neutral")
    speak.add_argument("--language", default="auto")
    speak.add_argument("--voice", default=None)
    speak.add_argument("--out", default=None)

    clone = sub.add_parser("clone", help="Namunadan uslub ko'chirish")
    clone.add_argument("text")
    clone.add_argument("reference")
    clone.add_argument("--category", default="neutral")
    clone.add_argument("--out", default=None)
    clone.add_argument("--consent", action="store_true",
                       help="Namuna egasining roziligi tasdiqlanadi")
    clone.add_argument("--consent-id", default=None,
                       help="Rozilik yozuvi identifikatori (mas. consent_001)")

    convert = sub.add_parser("convert", help="WAV ovozini toifaga o'tkazish")
    convert.add_argument("input")
    convert.add_argument("category")
    convert.add_argument("--out", default=None)

    stream = sub.add_parser("stream", help="Matnni WAV bo'laklariga oqitish")
    stream.add_argument("text")
    stream.add_argument("--category", default="neutral")
    stream.add_argument("--language", default="auto")
    stream.add_argument("--chunk-ms", type=int, default=250)
    stream.add_argument("--out-dir", default=None)

    serve = sub.add_parser("serve", help="Lokal HTTP ovoz API'si")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    return parser


def _make_handler(engine: VoiceEngine) -> type[BaseHTTPRequestHandler]:
    class VoiceHandler(BaseHTTPRequestHandler):
        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/api/voice/catalog"):
                self._json(200, {
                    "success": True, "models": engine.list_models(),
                    "categories": engine.list_categories(),
                })
            elif self.path.startswith("/api/voice/doctor"):
                self._json(200, engine.doctor())
            else:
                self._json(404, {"success": False, "error": "Topilmadi"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path not in ("/api/voice/speak", "/api/voice/clone", "/api/voice/stream"):
                self._json(404, {"success": False, "error": "Topilmadi"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                text = str(payload.get("text", ""))
                category = str(payload.get("category", "neutral"))
                language = str(payload.get("language", "auto"))
                if not text:
                    self._json(400, {"success": False, "error": "text shart"})
                    return
                if self.path == "/api/voice/speak":
                    result = engine.synthesize(text, category=category, language=language)
                    data = Path(result.wav_path).read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("X-Voice-Model", result.model)
                    self.send_header("X-Voice-Category", result.category)
                    self.end_headers()
                    self.wfile.write(data)
                elif self.path == "/api/voice/clone":
                    reference = str(payload.get("reference", ""))
                    if payload.get("consent") is not True or not payload.get("consent_id"):
                        error = b'{"success":false,"error_code":"CONSENT_REQUIRED","error":"consent=true va consent_id shart"}'
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(error)))
                        self.end_headers()
                        self.wfile.write(error)
                        return
                    result = engine.clone(
                        text, reference, category=category,
                        consent=True, consent_id=str(payload["consent_id"]),
                    )
                    data = Path(result.wav_path).read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    chunks = list(engine.stream(text, category, language))
                    if not chunks:
                        raise ValueError("Stream bo'sh")
                    # Har chunk o'z WAV sarlavhasi bilan keladi. Bitta to'g'ri
                    # WAV yaratish uchun faqat birinchi sarlavha saqlanadi,
                    # qolganlarining PCM ma'lumoti qo'shiladi.
                    header = chunks[0][:44]
                    pcm_parts = [c[44:] if len(c) >= 44 else b"" for c in chunks]
                    pcm = b"".join(pcm_parts)
                    data_size = len(pcm)
                    data = header[:40] + data_size.to_bytes(4, "little") + pcm
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as exc:
                self._json(500, {"success": False, "error": f"{type(exc).__name__}: {exc}"})

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("voice HTTP %s - %s\n" % (self.address_string(), fmt % args))

    return VoiceHandler


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = VoiceEngine()
    try:
        if args.command == "doctor":
            report = engine.doctor()
            _print(report)
            return 0 if report["ok"] else 1
        if args.command == "catalog":
            _print({"success": True, "models": engine.list_models(),
                    "categories": engine.list_categories()})
            return 0
        if args.command == "speak":
            _print(engine.synthesize(
                args.text, category=args.category, language=args.language,
                voice=args.voice, out_path=args.out,
            ).as_dict())
            return 0
        if args.command == "clone":
            if not args.consent or not args.consent_id:
                _print({"success": False, "error_code": "CONSENT_REQUIRED",
                        "error": "Klonlash uchun --consent va --consent-id shart."})
                return 2
            _print(engine.clone(
                args.text, args.reference, category=args.category, out_path=args.out,
                consent=True, consent_id=args.consent_id,
            ).as_dict())
            return 0
        if args.command == "convert":
            _print(engine.convert(args.input, args.category, out_path=args.out).as_dict())
            return 0
        if args.command == "stream":
            out_dir = Path(args.out_dir) if args.out_dir else engine.output_dir / "stream"
            out_dir.mkdir(parents=True, exist_ok=True)
            count = 0
            total = 0
            for index, chunk in enumerate(engine.stream(
                args.text, args.category, args.language, chunk_ms=args.chunk_ms
            )):
                path = out_dir / f"chunk_{index:04d}.wav"
                path.write_bytes(chunk)
                count += 1
                total += len(chunk)
            _print({"success": True, "chunks": count, "bytes": total,
                    "out_dir": str(out_dir)})
            return 0
        if args.command == "serve":
            server = ThreadingHTTPServer(
                (args.host, args.port), _make_handler(engine)
            )
            _print({"success": True, "url": f"http://{args.host}:{args.port}"})
            server.serve_forever()
            return 0
    except Exception as exc:
        _print({"success": False, "error": f"{type(exc).__name__}: {exc}"})
        return 1
    return 1
