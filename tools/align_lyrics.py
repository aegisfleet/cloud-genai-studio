"""
Whisper-based Vocal Alignment & LRC Generator for JIZURA

ffmpeg 不要（soundfile + scipy 直接読み込み）で音声ファイルから
ボーカル発声タイミング（ミリ秒単位）を抽出し、JSON および JIZURA 用 LRC を生成する。
"""

import argparse
import json
from pathlib import Path
import numpy as np
import scipy.signal
import soundfile as sf
import whisper

def parse_args():
    parser = argparse.ArgumentParser(description="Extract word-level timestamps using Whisper and generate JIZURA-ready LRC")
    parser.add_argument("--audio", type=str, default="outputs/10deg_take3_expressive.wav", help="Input audio file (.wav or .flac)")
    parser.add_argument("--model", type=str, default="base", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--language", type=str, default="ja", help="Language code")
    parser.add_argument("--output", type=str, default="outputs/whisper_alignment.json", help="Output JSON path")
    parser.add_argument("--lrc", type=str, default=None, help="Optional output LRC path (auto-generates draft timestamped lyrics)")
    return parser.parse_args()

def main():
    args = parse_args()
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: {audio_path} not found.")
        return

    print(f"Loading audio from {audio_path}...")
    data, sr = sf.read(str(audio_path))
    if data.ndim > 1:
        data = data.mean(axis=1)

    # 16kHz にリサンプリングして Whisper に直接渡す（ffmpeg 依存を完全回避）
    target_sr = 16000
    num_samples = int(len(data) * target_sr / sr)
    audio_16k = scipy.signal.resample(data, num_samples).astype(np.float32)

    print(f"Loading Whisper model ({args.model})...")
    model = whisper.load_model(args.model)

    print("Transcribing and extracting timestamps...")
    result = model.transcribe(
        audio_16k,
        language=args.language,
        word_timestamps=True,
        verbose=False
    )

    print("\n=== Detected Segments ===")
    lrc_lines = []
    for seg in result["segments"]:
        start_m, start_s = divmod(seg["start"], 60)
        end_m, end_s = divmod(seg["end"], 60)
        text = seg["text"].strip()
        timestamp_str = f"[{int(start_m):02d}:{start_s:05.2f}]"
        print(f"{timestamp_str} --> [{int(end_m):02d}:{end_s:05.2f}] {text}")
        if text:
            lrc_lines.append(f"{timestamp_str}{text}")

    # JSON 保存
    out_file = Path(args.output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result["segments"], f, ensure_ascii=False, indent=2)
    print(f"\nAlignment JSON saved to: {out_file}")

    # LRC 保存（指定時）
    if args.lrc:
        lrc_file = Path(args.lrc)
        lrc_file.parent.mkdir(parents=True, exist_ok=True)
        with open(lrc_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lrc_lines) + "\n")
        print(f"Draft LRC saved to: {lrc_file}")

if __name__ == "__main__":
    main()
