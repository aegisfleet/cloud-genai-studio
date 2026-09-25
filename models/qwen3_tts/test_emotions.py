import os
import time
import torch
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel
from generate import normalize_text_for_tts

os.makedirs("outputs", exist_ok=True)

print("=== Qwen3-TTS ono_anna 感情・話速・スタイル検証 ===")

model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
model = Qwen3TTSModel.from_pretrained(
    model_id,
    device_map="cuda:0",
    dtype=torch.bfloat16,
    attn_implementation="sdpa",
)

test_cases = [
    {
        "name": "anna_1_happy_fast",
        "text": "やったー！ついにモデルの検証が成功したよ！本当に嬉しい！",
        "instruct": "飛び上がるほど嬉しそうに、明るく元気いっぱいの早口で話してください",
        "desc": "喜び・明るい・早口 (Happy / Fast)",
    },
    {
        "name": "anna_2_whisper_slow",
        "text": "ねえ、ここだけの秘密なんだけど……誰にも言わないでね。",
        "instruct": "耳元で内緒話をするように、静かに囁くような声でゆっくりと話してください",
        "desc": "囁き声・内緒話・スロー (Whisper / Slow)",
    },
    {
        "name": "anna_3_news_calm",
        "text": "本日の主要な経済ニュースをお伝えいたします。最新の市場動向です。",
        "instruct": "ニュースキャスターのように、落ち着いて明瞭かつ正確なペースで話してください",
        "desc": "ニュース調・明瞭・落ち着き (News / Professional)",
    },
    {
        "name": "anna_4_angry_intense",
        "text": "もういい加減にして！何度同じことを言わせるの！",
        "instruct": "とても怒った口調で、語気を強めて厳しく話してください",
        "desc": "怒り・強い語気 (Angry / Intense)",
    },
    {
        "name": "anna_5_sad_slow",
        "text": "そんな……信じられない……どうしてこんなことになっちゃったんだろう……",
        "instruct": "悲しそうに、消え入りそうな声でゆっくりと話してください",
        "desc": "悲哀・消え入りそうな声・スロー (Sad / Slow)",
    },
]

for tc in test_cases:
    print(f"\n--- 生成中: {tc['desc']} ---")
    proc_text = normalize_text_for_tts(tc["text"], apply_pronounce=True, apply_tail_padding=True)
    print(f"入力テキスト: '{tc['text']}'")
    print(f"指示 (instruct): '{tc['instruct']}'")
    
    t0 = time.time()
    wavs, sr = model.generate_custom_voice(
        text=proc_text,
        language="Japanese",
        speaker="ono_anna",
        instruct=tc["instruct"],
        temperature=0.9,
    )
    t_gen = time.time() - t0
    
    # 0.5s 無音パディング付加
    audio = wavs[0]
    silence = np.zeros(int(sr * 0.5), dtype=audio.dtype)
    audio = np.concatenate([audio, silence])
    
    out_path = os.path.join("outputs", f"{tc['name']}.wav")
    sf.write(out_path, audio, sr)
    duration = len(audio) / sr
    print(f"保存完了: {out_path} (音声長: {duration:.2f}秒, 生成時間: {t_gen:.2f}秒)")

print("\n=== 全感情パターンの検証音声生成が完了 ===")
