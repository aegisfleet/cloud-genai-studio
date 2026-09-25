"""
5つの小野アンナ感情別音声を一括で正方形オーディオグラム動画(MP4)にレンダリングするスクリプト
"""

import subprocess
import sys
from pathlib import Path

ITEMS = [
    {
        "audio": "outputs/anna_1_happy_fast.wav",
        "output": "outputs/anna_1_happy_fast_square.mp4",
        "speaker": "Ono Anna (小野 アンナ)",
        "role": "喜び・明るい・早口 (Happy / Fast)",
        "text": "やったー！ついにモデルの検証が成功したよ！本当に嬉しい！",
        "tag": "HAPPY & FAST",
        "primary": "#38bdf8",
        "secondary": "#f472b6",
    },
    {
        "audio": "outputs/anna_2_whisper_slow.wav",
        "output": "outputs/anna_2_whisper_slow_square.mp4",
        "speaker": "Ono Anna (小野 アンナ)",
        "role": "囁き声・内緒話・スロー (Whisper / Slow)",
        "text": "ねえ、ここだけの秘密なんだけど……誰にも言わないでね。",
        "tag": "WHISPER & SLOW",
        "primary": "#c084fc",
        "secondary": "#818cf8",
    },
    {
        "audio": "outputs/anna_3_news_calm.wav",
        "output": "outputs/anna_3_news_calm_square.mp4",
        "speaker": "Ono Anna (小野 アンナ)",
        "role": "ニュース調・明瞭・落ち着き (News / Professional)",
        "text": "本日の主要な経済ニュースをお伝えいたします。最新の市場動向です。",
        "tag": "NEWS & CALM",
        "primary": "#38bdf8",
        "secondary": "#2dd4bf",
    },
    {
        "audio": "outputs/anna_4_angry_intense.wav",
        "output": "outputs/anna_4_angry_intense_square.mp4",
        "speaker": "Ono Anna (小野 アンナ)",
        "role": "怒り・強い語気 (Angry / Intense)",
        "text": "もういい加減にして！何度同じことを言わせるの！",
        "tag": "ANGRY & INTENSE",
        "primary": "#f87171",
        "secondary": "#fb923c",
    },
    {
        "audio": "outputs/anna_5_sad_slow.wav",
        "output": "outputs/anna_5_sad_slow_square.mp4",
        "speaker": "Ono Anna (小野 アンナ)",
        "role": "悲哀・消え入りそうな声・スロー (Sad / Slow)",
        "text": "そんな……信じられない……どうしてこんなことになっちゃったんだろう……",
        "tag": "SAD & SLOW",
        "primary": "#60a5fa",
        "secondary": "#94a3b8",
    },
]

def main():
    root = Path(__file__).resolve().parent.parent
    create_script = root / "tools" / "create_audiogram.py"

    print("==================================================")
    print(" 5つの音声のオーディオグラム一括レンダリング開始 ")
    print("==================================================")

    for i, item in enumerate(ITEMS, start=1):
        print(f"\n[{i}/5] レンダリング中: {item['tag']} ({item['audio']})")
        audio_file = root / item["audio"]
        if not audio_file.exists():
            print(f"[!] 音声ファイルが存在しません: {audio_file}", file=sys.stderr)
            continue

        cmd = [
            sys.executable,
            str(create_script),
            "--audio", str(audio_file),
            "--output", str(root / item["output"]),
            "--speaker", item["speaker"],
            "--role", item["role"],
            "--text", item["text"],
            "--tag", item["tag"],
            "--format", "square",
            "--primary-color", item["primary"],
            "--secondary-color", item["secondary"],
        ]

        result = subprocess.run(cmd, cwd=str(root))
        if result.returncode != 0:
            print(f"[!] エラーが発生しました: {item['audio']}", file=sys.stderr)
            sys.exit(1)

    print("\n==================================================")
    print(" [SUCCESS] 全5つの動画レンダリングが完了しました！")
    print("==================================================")

if __name__ == "__main__":
    main()
