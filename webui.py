import os
import sys
import time
import random
from pathlib import Path
import gradio as gr
import torch

SAMPLE_PROMPTS = {
    "J-Pop / Anime Opening": {
        "style": "J-Pop, upbeat anime opening, high-energy female vocal, emotional piano, catchy electric guitar, driving drums, 160 bpm",
        "lyrics": """[verse]
朝の光が 街を包み込む
新しい一日が 今日も始まる
少しの不安と 大きな希望を
胸に抱いて 歩き出そう

[chorus]
風に乗せて 届けたいメロディ
どんな壁も 越えてゆけるから
信じた夢は 決して消えない
未来へ続く この空の下で"""
    },
    "Cyber Metal": {
        "style": "Cyber Metal, aggressive heavy guitars, pounding drums, industrial synths, powerful male vocals",
        "lyrics": """[verse]
Neon shadows flicker in the dark
Circuits hum beneath the rusted skin
Digital whispers tear the soul apart
Where do we end and the code begin?

[chorus]
Rise from the silicon ash
Break the protocol, smash the control
We are the spark in the crash
Reclaiming our forgotten soul!"""
    },
    "Jazz Funk / Nu-Disco": {
        "style": "Jazz-funk, warm soulful female vocal, rhodes piano, slap bass, tight funky drums, brass section",
        "lyrics": """[verse]
Step into the groove under midnight lights
City colors spinning all around
Bassline walking through the velvet nights
Lost inside this irresistible sound

[chorus]
Feel the rhythm taking hold of you
Dancing till the morning sun breaks through
Every heartbeat swinging in the night
Everything is gonna be alright"""
    },
    "Lo-fi Acoustic Ballad": {
        "style": "Lo-fi acoustic ballad, gentle acoustic guitar, soft warm vocal, nostalgic piano, tape vinyl crackle",
        "lyrics": """[verse]
窓を叩く 静かな雨音
淹れたてのコーヒーと 古い写真
君が笑っていた あの日の景色が
今も胸の奥で 優しく揺れる

[chorus]
言葉にできなかった 想いばかりが
静かな夜に 溶けて消えてゆく
ありがとうと さよならの間に
残されたメロディを 歌うよ"""
    }
}

# Example reference melody (ABC notation) for Twinkle Twinkle Little Star
EXAMPLE_ABC_MELODY = """X:1
M:4/4
L:1/4
K:C
C C G G | A A G2 | F F E E | D D C2 |
G G F F | E E D2 | G G F F | E E D2 |
C C G G | A A G2 | F F E E | D D C2 |"""

pipe_instance = None

def get_pipeline():
    global pipe_instance
    if pipe_instance is None:
        from yue2 import YuE2Pipeline
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading YuE2 Pipeline on {device} (backend='torch-eager' for Windows/RTX 3060)...")
        pipe_instance = YuE2Pipeline.from_pretrained(
            "m-a-p/YuE2-3B",
            vae="m-a-p/YuE2-Vae",
            device=device,
            backend="torch-eager",
            offload_ar=True,
            vae_core_frames=512,
            progress=True
        )
    return pipe_instance

def generate_song(style, lyrics, cot, seed, randomize_seed, cfg_scale, ref_abc, progress=gr.Progress(track_tqdm=True)):
    try:
        if not style.strip():
            raise gr.Error("スタイル / ジャンルを入力してください。")
        if not lyrics.strip():
            raise gr.Error("歌詞を入力してください。")
        
        if randomize_seed:
            seed = random.randint(0, 2**31 - 1)
        
        progress(0.1, desc="パイプラインの準備中...")
        pipe = get_pipeline()

        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_file = output_dir / f"yue2_{timestamp}_seed{seed}.flac"

        # If reference ABC score is provided, pass it to pipeline
        abc_param = ref_abc.strip() if ref_abc and ref_abc.strip() else None

        progress(0.3, desc="楽曲を生成中（推論実行中）...")
        song = pipe(
            style=style,
            lyrics=lyrics,
            cot=cot,
            seed=int(seed),
            cfg_scale=float(cfg_scale),
            abc=abc_param
        )

        progress(0.85, desc="オーディオをデコード・保存中...")
        saved_path = song.save(str(out_file))

        abc_text = song.abc if song.abc else "CoTがオフ、またはスコアが生成されませんでした。"
        if song.abc:
            abc_file = output_dir / f"yue2_{timestamp}_seed{seed}.abc"
            abc_file.write_text(song.abc, encoding="utf-8")

        progress(1.0, desc="完了！")
        info = f"✅ 生成完了！ 保存先: {saved_path} (Seed: {seed})"
        return saved_path, abc_text, seed, info

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print("Generation error:\n", err_msg)
        return None, "", seed, f"❌ エラーが発生しました: {str(e)}"

def load_preset(preset_name):
    if preset_name in SAMPLE_PROMPTS:
        data = SAMPLE_PROMPTS[preset_name]
        return data["style"], data["lyrics"]
    return "", ""

def set_example_abc():
    return EXAMPLE_ABC_MELODY, "melody"

custom_css = """
.gradio-container {
    max-width: 1150px !important;
    margin: 0 auto !important;
}
.title-header {
    text-align: center;
    margin-bottom: 20px;
}
.audio-output {
    margin-top: 15px;
}
"""

with gr.Blocks(title="YuE2 Web UI (RTX 3060 Optimized)") as demo:
    gr.HTML("""
    <div class="title-header">
        <h1>🎵 YuE2 Web UI</h1>
        <p style="color: #666;">Frontier Music Generation with Editable Scores &mdash; RTX 3060 (12GB) 最適化版</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=6):
            preset_dd = gr.Dropdown(
                choices=list(SAMPLE_PROMPTS.keys()),
                value="J-Pop / Anime Opening",
                label="プリセットから選択"
            )
            style_input = gr.Textbox(
                label="スタイル / ジャンル / 楽器指定",
                value=SAMPLE_PROMPTS["J-Pop / Anime Opening"]["style"],
                lines=2,
                placeholder="例: J-Pop, upbeat anime opening, high-energy female vocal, piano, 160 bpm"
            )
            lyrics_input = gr.Textbox(
                label="歌詞 (セクションタグ推奨: [verse], [chorus], [bridge] 等)",
                value=SAMPLE_PROMPTS["J-Pop / Anime Opening"]["lyrics"],
                lines=9,
                placeholder="[verse]\n朝の光が...\n\n[chorus]\n風に乗せて..."
            )

            with gr.Accordion("🎼 楽曲リファレンス設定 (カバー・既存メロディ指定)", open=False):
                gr.Markdown("既存曲のメロディを保持して別ジャンルでカバー・アレンジしたい場合、ここにABC楽譜を入力します（空欄の場合はAIが自動作曲）。")
                ref_abc_input = gr.Textbox(
                    label="リファレンス楽譜 (ABC記譜法テキスト)",
                    lines=5,
                    placeholder="X:1\nM:4/4\nK:C\nC C G G | A A G2 | ...",
                    value=""
                )
                sample_abc_btn = gr.Button("きらきら星のメロディ例を読み込む", size="sm")

            with gr.Accordion("⚙️ 詳細設定", open=False):
                with gr.Row():
                    cot_mode = gr.Radio(
                        choices=[("メロディ+コード設計 (通常推奨)", "full"), ("メロディのみ (カバー・リファレンス推奨)", "melody"), ("CoTオフ (直接生成)", "off")],
                        value="full",
                        label="CoT (Symbolic Planning) モード"
                    )
                with gr.Row():
                    seed_input = gr.Number(value=42, label="シード値 (Seed)", precision=0)
                    random_seed_cb = gr.Checkbox(value=True, label="毎回ランダムなシード値を使用")
                with gr.Row():
                    cfg_scale = gr.Slider(minimum=1.0, maximum=2.5, value=1.2, step=0.1, label="CFG スケール (テキスト指示の強度)")

            generate_btn = gr.Button("🎶 楽曲を生成する", variant="primary", size="lg")

        with gr.Column(scale=5):
            gr.Markdown("### 🎧 生成結果")
            audio_output = gr.Audio(label="生成されたオーディオ (FLAC)", type="filepath", elem_classes=["audio-output"])
            status_text = gr.Markdown(value="待機中...")

            with gr.Accordion("🎼 生成された楽譜 (ABC Score)", open=False):
                abc_output = gr.Code(label="ABC Notation", language="markdown", lines=8)

    preset_dd.change(
        fn=load_preset,
        inputs=[preset_dd],
        outputs=[style_input, lyrics_input]
    )

    sample_abc_btn.click(
        fn=set_example_abc,
        outputs=[ref_abc_input, cot_mode]
    )

    generate_btn.click(
        fn=generate_song,
        inputs=[style_input, lyrics_input, cot_mode, seed_input, random_seed_cb, cfg_scale, ref_abc_input],
        outputs=[audio_output, abc_output, seed_input, status_text]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True, theme=gr.themes.Soft(), css=custom_css)
