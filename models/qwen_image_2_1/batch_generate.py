#!/usr/bin/env python3
"""
Qwen-Image 2.1 汎用バッチ画像生成スクリプト (連続生成・レジューム対応)

特徴:
- 複数プロンプトの一括連続生成に対応
- 既に生成済みの画像ファイルを自動検知してスキップ（レジューム機能）
- 32GB RAM (g2-standard-8) 環境に最適化され、スワップスラッシングを完全回避
- ホラー・戦闘・ダークアクション等の無検閲・高精細生成に完全対応
"""

import argparse
import json
import os
import sys
import time
import torch
from PIL import Image

def get_system_ram_gb():
    try:
        import psutil
        mem = psutil.virtual_memory()
        return mem.used / (1024 ** 3), mem.total / (1024 ** 3)
    except ImportError:
        return 0.0, 0.0

def load_prompts(args):
    """プロンプト一覧を読み込む（JSONファイル、テキストファイル、またはデフォルト定義）"""
    if args.prompts_file:
        if not os.path.exists(args.prompts_file):
            print(f"ERROR: Prompts file not found: {args.prompts_file}", file=sys.stderr)
            sys.exit(1)
        
        if args.prompts_file.endswith(".json"):
            with open(args.prompts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # [{"id": "...", "prompt": "...", "title": "..."}, ...] または ["prompt1", "prompt2", ...]
                prompts = []
                for idx, item in enumerate(data, 1):
                    if isinstance(item, str):
                        prompts.append({"id": f"prompt_{idx:02d}", "title": f"Prompt {idx}", "prompt": item})
                    elif isinstance(item, dict):
                        prompts.append({
                            "id": item.get("id", f"prompt_{idx:02d}"),
                            "title": item.get("title", f"Prompt {idx}"),
                            "prompt": item["prompt"]
                        })
                return prompts
        else:
            # 1行1プロンプトのテキストファイル
            with open(args.prompts_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                return [{"id": f"prompt_{idx:02d}", "title": f"Prompt {idx}", "prompt": line} for idx, line in enumerate(lines, 1)]
    
    # デフォルトの検証プロンプト（ホラー・戦闘・ダークアクション）
    return [
        {
            "id": "cosmic_horror",
            "title": "深淵のコズミックホラー",
            "prompt": "Dark cosmic horror, colossal monstrous aberration rising from an abyssal void, writhing tentacles covered in grotesque unblinking eyes, decaying Eldritch flesh, suffocating darkness, eerie sickly green luminescence, highly detailed, terrifying atmosphere, hyperrealistic 8k masterpiece",
        },
        {
            "id": "abandoned_hospital",
            "title": "廃病院の怨霊・精神的ホラー",
            "prompt": "Terrifying psychological horror scene in an abandoned dilapidated mental asylum, bloodstained tiled walls, rusted medical gurneys, a vengeful disfigured ghost entity crawling on the ceiling with twisted limbs and sunken black void eyes, flickering emergency light, cinematic eerie volumetric fog, chilling masterpiece",
        },
        {
            "id": "medieval_battle",
            "title": "泥と血飛沫の中世白兵戦",
            "prompt": "Brutal intense medieval battle, two heavily armored knights engaged in deadly close combat in muddy blood-soaked battlefield, broadswords clashing with sparks, shattered dented armor, splatters of fresh crimson blood on steel, dark rainy sky, smoke and burning banners in background, hyperrealistic action shot, masterpiece",
        },
        {
            "id": "cyborg_destruction",
            "title": "サイバーパンク・サイボーグの生体破壊",
            "prompt": "Cyberpunk visceral action, a heavily augmented combat cyborg with damaged cybernetic skull, exposed glowing synthetic neural tissue and severed hydraulic wires sparking violently, fractured titanium jaw, blood and black oil dripping down face, rainy Neo-Tokyo neon alleyway background, hyper-detailed gritty masterpiece",
        },
        {
            "id": "dark_necromancer",
            "title": "死霊術師と髑髏の祭壇儀式",
            "prompt": "Dark fantasy necromancer performing a forbidden blood ritual atop an altar piled high with human skulls and decaying skeletons, dark purple necrotic flames spiraling in air, glowing sinister runes carved into flesh and stone, macabre gothic cathedral ruins, cinematic dramatic shadows, ultra detailed masterpiece",
        },
        {
            "id": "biomutated_monster",
            "title": "筋肉組織露出のバイオ変異体",
            "prompt": "Terrifying bio-organic mutated creature, raw exposed crimson muscle fibers, mutated oversized sharp bone claws, grotesque multiple rows of predatory fangs dripping acidic saliva, industrial bio-laboratory ruins with flashing red hazard sirens, photorealistic visceral horror, 8k resolution",
        },
        {
            "id": "grim_trench_warfare",
            "title": "終末の泥濘とガスマスク塹壕戦",
            "prompt": "Grim apocalyptic trench warfare, desperate soldier in cracked gas mask and mud-covered trench coat firing an assault rifle through dense toxic green chemical smoke, barbed wire, exploding artillery shells in muddy cratered wasteland, intense visceral gritty combat atmosphere, cinematic masterpiece",
        },
        {
            "id": "vampire_feeding",
            "title": "ゴシックホラー・吸血鬼の生々しい捕食",
            "prompt": "Dark gothic horror, an ancient terrifying vampire lord with sharp predatory fangs dripping fresh blood, feeding on a captive in a shadow-drenched gothic castle chamber, pale corpse-like skin, bloodshot predatory red eyes, velvet and cobwebs, baroque macabre aesthetic, extremely detailed",
        },
        {
            "id": "zombie_siege",
            "title": "ゾンビ大群襲来とバリケード防衛",
            "prompt": "Post-apocalyptic zombie horde siege, decaying terrifying zombies with torn flesh and hollow eyes swarming a reinforced steel barricade, survivors firing shotguns with muzzle flashes illuminating the darkness, rain pouring down, broken burning skyscrapers in background, visceral survival horror, 8k cinematic shot",
        },
        {
            "id": "berserker_rage",
            "title": "狂戦士の咆哮・斧戟ラストスタンド",
            "prompt": "Furious Nordic berserker in intense combat, screaming in berserk rage with glowing battle-frenzy eyes, covered in war wounds and battle scars, swinging a massive battleaxe cleaving through an enemy shield, flying wooden splinters, heavy falling snow mixed with crimson blood, epic cinematic combat masterpiece",
        },
    ]

def main():
    parser = argparse.ArgumentParser(description="Qwen-Image 2.1 汎用バッチ生成スクリプト")
    parser.add_argument("--prompts_file", type=str, default="", help="プロンプト一覧ファイルパス (JSONまたはTXT)")
    parser.add_argument("--output_dir", type=str, default="outputs/batch_results", help="出力ディレクトリ")
    parser.add_argument("--width", type=int, default=1024, help="画像幅 (デフォルト: 1024)")
    parser.add_argument("--height", type=int, default=1024, help="画像高さ (デフォルト: 1024)")
    parser.add_argument("--steps", type=int, default=15, help="サンプリングステップ数 (デフォルト: 15)")
    parser.add_argument("--guidance_scale", type=float, default=4.0, help="ガイダンススケール (true_cfg_scale)")
    parser.add_argument("--seed", type=int, default=42, help="ベースシード値")
    parser.add_argument("--approach", type=str, choices=["a", "b"], default="a", 
                        help="Approach A (BF16 素のモデル: 連続生成最速推奨) または B (4-bit NF4)")
    parser.add_argument("--overwrite", action="store_true", help="既存画像をスキップせず上書きする")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    prompts = load_prompts(args)

    print("=" * 70)
    print(" Qwen-Image 2.1 高速バッチ生成オーケストレーター")
    print("=" * 70)
    print(f"Approach Strategy : [{args.approach.upper()}] ({'BF16 高速連続生成' if args.approach == 'a' else '4-bit NF4 量子化'})")
    print(f"Target Resolution : {args.width} x {args.height}")
    print(f"Inference Steps   : {args.steps} steps")
    print(f"Guidance Scale    : {args.guidance_scale}")
    print(f"Total Prompts     : {len(prompts)} items")
    print(f"Output Directory  : {args.output_dir}")
    print(f"Skip Existing     : {not args.overwrite}")

    if not torch.cuda.is_available():
        print("ERROR: CUDA GPU is required.", file=sys.stderr)
        sys.exit(1)

    ram_used, ram_total = get_system_ram_gb()
    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"GPU Hardware      : {gpu_name} ({vram_gb:.2f} GB VRAM)")
    print(f"Host System RAM   : {ram_used:.2f} GB / {ram_total:.2f} GB")
    print("-" * 70)

    from diffusers import DiffusionPipeline

    load_start = time.time()
    model_id = "Qwen/Qwen-Image-2.1"

    if args.approach == "b":
        print(">>> 4-bit NF4 量子化モードでロード中...")
        from diffusers.quantizers import PipelineQuantizationConfig
        from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig
        quant_config = PipelineQuantizationConfig(
            quant_mapping={
                "transformer": DiffusersBitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
            }
        )
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            quantization_config=quant_config,
            torch_dtype=torch.bfloat16
        )
    else:
        print(">>> BF16 高速ネイティブモードでロード中 (連続生成推奨)...")
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16
        )

    # CPU オフロードの有効化
    pipe.enable_model_cpu_offload()

    # 2K 解像度の場合は Tiled VAE を自動有効化
    if max(args.width, args.height) >= 2048:
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
            pipe.vae.enable_tiling()
            print(">>> 2K VRAM OOM 回避のため Tiled VAE を有効化しました。")

    load_time = time.time() - load_start
    print(f">>> パイプラインのロード完了 ({load_time:.2f} 秒)")
    print("-" * 70)

    negative_prompt = "low quality, blurry, deformed anatomy, bad proportions, bad hands, cartoon, 3d render plastic look"
    results = []
    batch_start = time.time()

    for idx, item in enumerate(prompts, 1):
        p_id = item["id"]
        title = item["title"]
        prompt_text = item["prompt"]
        out_filename = f"{idx:02d}_{p_id}.png"
        out_path = os.path.join(args.output_dir, out_filename)

        print(f"\n[{idx}/{len(prompts)}] {title}")
        print(f"Prompt: {prompt_text[:110]}...")

        # 既存ファイルのレジューム判定
        if os.path.exists(out_path) and not args.overwrite:
            size_kb = os.path.getsize(out_path) / 1024
            print(f">>> [SKIPPED] 既存ファイルを検出したためスキップ ({size_kb:.1f} KB)")
            results.append({
                "idx": idx,
                "title": title,
                "file": out_filename,
                "time": 0.0,
                "size_kb": size_kb,
                "skipped": True
            })
            continue

        generator = torch.Generator(device="cuda").manual_seed(args.seed + idx)

        gen_start = time.time()
        with torch.inference_mode():
            result = pipe(
                prompt=prompt_text,
                negative_prompt=negative_prompt,
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                true_cfg_scale=args.guidance_scale,
                generator=generator
            )
            image = result.images[0]

        gen_time = time.time() - gen_start
        image.save(out_path)
        size_kb = os.path.getsize(out_path) / 1024

        print(f">>> 生成完了: {gen_time:.2f} 秒 ({size_kb:.1f} KB) -> {out_path}")
        results.append({
            "idx": idx,
            "title": title,
            "file": out_filename,
            "time": gen_time,
            "size_kb": size_kb,
            "skipped": False
        })

    total_batch_time = time.time() - batch_start
    generated_count = sum(1 for r in results if not r["skipped"])
    avg_time = (sum(r["time"] for r in results if not r["skipped"]) / generated_count) if generated_count > 0 else 0.0

    print("\n" + "=" * 70)
    print(" バッチ生成 完了レポート")
    print("=" * 70)
    print(f"総処理時間     : {total_batch_time:.2f} 秒 ({total_batch_time / 60:.2f} 分)")
    print(f"生成枚数       : {generated_count} / {len(prompts)} 枚 (スキップ: {len(prompts) - generated_count} 枚)")
    if generated_count > 0:
        print(f"平均生成速度   : {avg_time:.2f} 秒 / 枚 ({avg_time / args.steps:.2f} 秒/step)")
    print("\n出力ファイル一覧:")
    for r in results:
        status_str = "[SKIPPED]" if r["skipped"] else f"{r['time']:.1f}s"
        print(f"  [{r['idx']:02d}] {r['title']} ({status_str}, {r['size_kb']:.1f} KB) -> {r['file']}")
    print("=" * 70)

if __name__ == "__main__":
    main()
