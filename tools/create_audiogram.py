"""
Remotion を用いた高品質オーディオグラム（波形アニメーション・字幕・話者表示付き動画）生成スクリプト
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path


def get_audio_duration(file_path: Path) -> float:
    """音声ファイルの秒数を取得する。"""
    try:
        with wave.open(str(file_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        pass

    # wave で開けない場合は ffprobe を試みる
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        pass

    # 取得失敗時はデフォルト10秒とする
    return 10.0


def main():
    parser = argparse.ArgumentParser(
        description="Remotion を使って音声から高品質なSNS向け波形動画(MP4)を生成する"
    )
    parser.add_argument(
        "--audio",
        "-a",
        type=str,
        required=True,
        help="入力音声ファイル (WAV/MP3)",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        default="初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。",
        help="動画内に表示するセリフ・字幕テキスト",
    )
    parser.add_argument(
        "--speaker",
        "-s",
        type=str,
        default="Ono Anna (小野 アンナ)",
        help="話者名",
    )
    parser.add_argument(
        "--role",
        "-r",
        type=str,
        default="AI音声キャラクター / 日本語ネイティブ話者",
        help="話者の役割・肩書",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Qwen3-TTS 日本語音声合成",
        help="上部に表示するタイトル",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default="QWEN3-TTS 1.7B",
        help="右上バッジタグ",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["square", "vertical", "horizontal"],
        default="square",
        help="動画アスペクト比: square (1:1, X/Insta), vertical (9:16, TikTok/Shorts), horizontal (16:9, YouTube)",
    )
    parser.add_argument(
        "--primary-color",
        type=str,
        default="#38bdf8",
        help="プライマリカラー (HEX)",
    )
    parser.add_argument(
        "--secondary-color",
        type=str,
        default="#818cf8",
        help="セカンダリカラー (HEX)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="出力先 MP4 ファイルパス",
    )

    args = parser.parse_args()

    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        print(f"エラー: 音声ファイルが見つかりません: {audio_path}", file=sys.stderr)
        sys.exit(1)

    # ツールディレクトリ
    script_dir = Path(__file__).parent.resolve()
    audiogram_dir = script_dir / "audiogram"
    public_dir = audiogram_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # 音声の長さを取得
    duration_sec = get_audio_duration(audio_path)
    print(f"[*] 音声長: {duration_sec:.2f} 秒")

    # 音声ファイルを public フォルダにコピー（安全な一意名）
    audio_ext = audio_path.suffix.lower()
    temp_audio_name = f"input_audio{audio_ext}"
    dest_audio_path = public_dir / temp_audio_name
    shutil.copy2(audio_path, dest_audio_path)

    # 出力パスの決定
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        root_dir = script_dir.parent
        outputs_dir = root_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        output_path = outputs_dir / f"{audio_path.stem}_{args.format}.mp4"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Composition ID の選択
    comp_map = {
        "square": "AudiogramSquare",
        "vertical": "AudiogramVertical",
        "horizontal": "AudiogramHorizontal",
    }
    comp_id = comp_map[args.format]

    # Props JSON の作成
    props = {
        "audioSrc": temp_audio_name,
        "title": args.title,
        "speaker": args.speaker,
        "speakerRole": args.role,
        "speechText": args.text,
        "tag": args.tag,
        "durationInSeconds": duration_sec,
        "primaryColor": args.primary_color,
        "secondaryColor": args.secondary_color,
    }

    props_file = audiogram_dir / "props_temp.json"
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    print(f"[*] レンダリングを開始します:")
    print(f"    - Composition : {comp_id} ({args.format})")
    print(f"    - 話者        : {args.speaker}")
    print(f"    - テキスト    : {args.text}")
    print(f"    - 出力先      : {output_path}")

    # npx remotion render コマンド構築
    # Windows 環境のため npx.cmd を探索
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"

    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.ts",
        comp_id,
        str(output_path),
        f"--props={str(props_file)}",
        "--overwrite",
    ]

    try:
        env = os.environ.copy()
        # UTF-8 出力を確実に
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.run(
            cmd,
            cwd=str(audiogram_dir),
            check=True,
            text=True,
            shell=(sys.platform == "win32"),
        )
        print(f"\n[+] 動画生成が完了しました！ -> {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] レンダリング中にエラーが発生しました (exit code: {e.returncode})", file=sys.stderr)
        sys.exit(1)
    finally:
        # 一時ファイルのクリーンアップ
        if props_file.exists():
            try:
                props_file.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()
