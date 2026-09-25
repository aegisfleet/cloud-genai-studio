import os
import time
import torch
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel

os.makedirs("outputs", exist_ok=True)

print("=== Qwen3-TTS 複数話者 & 余韻検証 ===")

model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
model = Qwen3TTSModel.from_pretrained(
    model_id,
    device_map="cuda:0",
    dtype=torch.bfloat16,
    attn_implementation="sdpa",
)

text_raw = "初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。Google CloudのL4インスタンスで快適に動作しています。"

# テストケース: 各話者 + 余韻アプローチ
test_cases = [
    {
        "speaker": "ono_anna",
        "instruct": "語尾の余韻を大切に、優しく落ち着いた日本語で話してください",
        "text": text_raw.rstrip("。") + "……。",
        "add_silence_sec": 0.6,
        "name": "ono_anna_with_silence_pad",
        "desc": "ono_anna (余韻指示 + 0.6秒パディング付与)",
    },
    {
        "speaker": "serena",
        "instruct": "優しく温かみのある日本語で話してください",
        "text": text_raw.rstrip("。") + "……。",
        "add_silence_sec": 0.4,
        "name": "serena_japanese",
        "desc": "serena (温かみのある女性話者)",
    },
    {
        "speaker": "sohee",
        "instruct": "落ち着いたトーンの自然な日本語で話してください",
        "text": text_raw.rstrip("。") + "……。",
        "add_silence_sec": 0.4,
        "name": "sohee_japanese",
        "desc": "sohee (落ち着いた女性話者)",
    },
    {
        "speaker": "uncle_fu",
        "instruct": "深みのある落ち着いた声で、語尾までしっかりと話してください",
        "text": text_raw.rstrip("。") + "……。",
        "add_silence_sec": 0.4,
        "name": "uncle_fu_japanese",
        "desc": "uncle_fu (渋い男性話者)",
    },
    {
        "speaker": "ryan",
        "instruct": "明るく爽やかな日本語で話してください",
        "text": text_raw.rstrip("。") + "……。",
        "add_silence_sec": 0.4,
        "name": "ryan_japanese",
        "desc": "ryan (爽やかな青年男性話者)",
    },
]

for tc in test_cases:
    print(f"\n--- 生成中: {tc['desc']} ---")
    t0 = time.time()
    wavs, sr = model.generate_custom_voice(
        text=tc["text"],
        language="Japanese",
        speaker=tc["speaker"],
        instruct=tc["instruct"],
        temperature=0.9,
    )
    t_gen = time.time() - t0
    
    audio = wavs[0]
    # 後処理: 末尾に自然な無音マージンを追加 (オーディオ波形の末尾パディング)
    if tc.get("add_silence_sec", 0) > 0:
        pad_len = int(sr * tc["add_silence_sec"])
        silence = np.zeros(pad_len, dtype=audio.dtype)
        audio = np.concatenate([audio, silence])
        
    out_path = os.path.join("outputs", f"{tc['name']}.wav")
    sf.write(out_path, audio, sr)
    duration = len(audio) / sr
    print(f"保存完了: {out_path} (音声長: {duration:.2f}秒, 生成所要時間: {t_gen:.2f}秒)")

print("\n=== 全話者の検証音声生成が完了 ===")
