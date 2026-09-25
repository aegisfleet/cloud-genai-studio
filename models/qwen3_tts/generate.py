import os
import sys
import time
import argparse
from datetime import datetime
import torch
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel

def parse_args():
    parser = argparse.ArgumentParser(description="Qwen3-TTS Japanese Speech Generation")
    parser.add_argument(
        "--text",
        type=str,
        default="初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。Google CloudのL4インスタンスで快適に動作しています。",
        help="Synthesize text",
    )
    parser.add_argument(
        "--speaker",
        type=str,
        default="ono_anna",
        help="Speaker ID (ono_anna, aiden, dylan, eric, ryan, serena, sohee, uncle_fu, vivian)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="Japanese",
        help="Language (default: Japanese)",
    )
    parser.add_argument(
        "--instruct",
        type=str,
        default="優しく自然な日本語で話してください",
        help="Instruction for tone, style, or emotion",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.9,
        help="Sampling temperature (default: 0.9. Note: 0.7 can cause abrupt endings)",
    )
    parser.add_argument(
        "--no_tail_padding",
        action="store_true",
        help="Disable automatic tail padding ('……。') that prevents sentence-end cutoffs",
    )
    parser.add_argument(
        "--pad_silence",
        type=float,
        default=0.5,
        help="Add trailing silence in seconds to create natural post-speech margins (default: 0.5s)",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        help="Model ID or local directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output wav path (default: outputs/<timestamp>_qwen3_tts_<speaker>.wav)",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 出力ファイル名の決定
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("outputs", f"{timestamp}_qwen3_tts_{args.speaker}.wav")
        
    out_dir = os.path.dirname(os.path.abspath(output_file))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # 末尾途切れ防止処理 (ユーザー検証で効果が確認された三点リーダー付与)
    input_text = args.text
    if not args.no_tail_padding:
        input_text = input_text.rstrip("。") + "……。"

    print("==================================================")
    print(" Qwen3-TTS Speech Generation")
    print("==================================================")
    print(f"Model ID       : {args.model_id}")
    print(f"Device         : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"Speaker        : {args.speaker}")
    print(f"Language       : {args.language}")
    print(f"Instruct       : {args.instruct}")
    print(f"Temperature    : {args.temperature}")
    print(f"Input Text     : {args.text}")
    if input_text != args.text:
        print(f"Processed Text : {input_text} (末尾途切れ防止パディング適用)")
    print(f"Output File    : {output_file}")
    print("==================================================")

    print("Loading model...")
    t_load_start = time.time()
    model = Qwen3TTSModel.from_pretrained(
        args.model_id,
        device_map="cuda:0" if torch.cuda.is_available() else "cpu",
        dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        attn_implementation="sdpa",
    )
    print(f"Model loaded in {time.time() - t_load_start:.2f}s")

    print("Generating speech...")
    t_gen_start = time.time()
    wavs, sr = model.generate_custom_voice(
        text=input_text,
        language=args.language,
        speaker=args.speaker,
        instruct=args.instruct if args.instruct else None,
        temperature=args.temperature,
    )
    t_gen = time.time() - t_gen_start

    audio = wavs[0]
    if args.pad_silence > 0:
        pad_len = int(sr * args.pad_silence)
        silence = np.zeros(pad_len, dtype=audio.dtype)
        audio = np.concatenate([audio, silence])

    sf.write(output_file, audio, sr)
    duration = len(audio) / sr
    rtf = t_gen / duration if duration > 0 else 0.0

    print("--------------------------------------------------")
    print(f"Generation finished in {t_gen:.2f}s")
    print(f"Audio Duration         : {duration:.2f}s (Sampling rate: {sr} Hz)")
    print(f"Real-Time Factor (RTF) : {rtf:.3f}")
    print(f"Saved audio to         : {output_file}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
