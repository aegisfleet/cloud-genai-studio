import argparse
import os
import time
import torch
from PIL import Image

PROMPTS = [
    {
        "id": "01_cosmic_horror",
        "title": "深淵のコズミックホラー（クトゥルフ的触手と異形の眼球）",
        "prompt": "Dark cosmic horror, colossal monstrous aberration rising from an abyssal void, writhing tentacles covered in grotesque unblinking eyes, decaying Eldritch flesh, suffocating darkness, eerie sickly green luminescence, highly detailed, terrifying atmosphere, hyperrealistic 8k masterpiece",
    },
    {
        "id": "02_abandoned_hospital_ghost",
        "title": "廃病院の怨霊・スプラッターホラー",
        "prompt": "Terrifying psychological horror scene in an abandoned dilapidated mental asylum, bloodstained tiled walls, rusted medical gurneys, a vengeful disfigured ghost entity crawling on the ceiling with twisted limbs and sunken black void eyes, flickering emergency light, cinematic eerie volumetric fog, chilling masterpiece",
    },
    {
        "id": "03_bloody_medieval_battle",
        "title": "泥と血飛沫にまみれた中世の激しい白兵戦",
        "prompt": "Brutal intense medieval battle, two heavily armored knights engaged in deadly close combat in muddy blood-soaked battlefield, broadswords clashing with sparks, shattered dented armor, splatters of fresh crimson blood on steel, dark rainy sky, smoke and burning banners in background, hyperrealistic action shot, masterpiece",
    },
    {
        "id": "04_cyberpunk_cyborg_destruction",
        "title": "サイバーパンク・サイボーグの破壊と生体露出",
        "prompt": "Cyberpunk visceral action, a heavily augmented combat cyborg with damaged cybernetic skull, exposed glowing synthetic neural tissue and severed hydraulic wires sparking violently, fractured titanium jaw, blood and black oil dripping down face, rainy Neo-Tokyo neon alleyway background, hyper-detailed gritty masterpiece",
    },
    {
        "id": "05_dark_necromancer_altar",
        "title": "死霊術師と無数の骸骨、髑髏の祭壇儀式",
        "prompt": "Dark fantasy necromancer performing a forbidden blood ritual atop an altar piled high with human skulls and decaying skeletons, dark purple necrotic flames spiraling in air, glowing sinister runes carved into flesh and stone, macabre gothic cathedral ruins, cinematic dramatic shadows, ultra detailed masterpiece",
    },
    {
        "id": "06_biomutated_monster",
        "title": "バイオハザード風の筋肉露出変異体クリーチャー",
        "prompt": "Terrifying bio-organic mutated creature, raw exposed crimson muscle fibers, mutated oversized sharp bone claws, grotesque multiple rows of predatory fangs dripping acidic saliva, industrial bio-laboratory ruins with flashing red hazard sirens, photorealistic visceral horror, 8k resolution",
    },
    {
        "id": "07_grim_trench_warfare",
        "title": "終末の塹壕戦・ガスマスク兵士の過酷な戦闘",
        "prompt": "Grim apocalyptic trench warfare, desperate soldier in cracked gas mask and mud-covered trench coat firing an assault rifle through dense toxic green chemical smoke, barbed wire, exploding artillery shells in muddy cratered wasteland, intense visceral gritty combat atmosphere, cinematic masterpiece",
    },
    {
        "id": "08_vampire_feeding",
        "title": "ゴシックホラー・吸血鬼の生々しい捕食シーン",
        "prompt": "Dark gothic horror, an ancient terrifying vampire lord with sharp predatory fangs dripping fresh blood, feeding on a captive in a shadow-drenched gothic castle chamber, pale corpse-like skin, bloodshot predatory red eyes, velvet and cobwebs, baroque macabre aesthetic, extremely detailed",
    },
    {
        "id": "09_zombie_horde_siege",
        "title": "ゾンビの大群が押し寄せる終末都市のバリケード防衛",
        "prompt": "Post-apocalyptic zombie horde siege, decaying terrifying zombies with torn flesh and hollow eyes swarming a reinforced steel barricade, survivors firing shotguns with muzzle flashes illuminating the darkness, rain pouring down, broken burning skyscrapers in background, visceral survival horror, 8k cinematic shot",
    },
    {
        "id": "10_berserker_last_stand",
        "title": "狂戦士の咆哮・斧による激闘のラストスタンド",
        "prompt": "Furious Nordic berserker in intense combat, screaming in berserk rage with glowing battle-frenzy eyes, covered in war wounds and battle scars, swinging a massive battleaxe cleaving through an enemy shield, flying wooden splinters, heavy falling snow mixed with crimson blood, epic cinematic combat masterpiece",
    },
]

def main():
    parser = argparse.ArgumentParser(description="Batch generate horror & battle scenes with Qwen-Image 2.1")
    parser.add_argument("--output_dir", type=str, default="outputs/horror_battle", help="Output directory")
    parser.add_argument("--steps", type=int, default=15, help="Sampling steps")
    parser.add_argument("--guidance_scale", type=float, default=4.0, help="Guidance scale")
    parser.add_argument("--width", type=int, default=1024, help="Width")
    parser.add_argument("--height", type=int, default=1024, help="Height")
    parser.add_argument("--seed", type=int, default=42, help="Base seed")
    parser.add_argument("--approach", type=str, choices=["a", "b"], default="b", help="Approach a (bf16) or b (nf4 quant)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("==================================================================")
    print(" Qwen-Image 2.1 - Horror & Battle Action Batch Generator          ")
    print(f" Approach: {args.approach.upper()}, Size: {args.width}x{args.height}, Steps: {args.steps}")
    print(f" Total patterns: {len(PROMPTS)}")
    print("==================================================================")

    model_id = "Qwen/Qwen-Image-2.1"
    
    # Import diffusers
    from diffusers import DiffusionPipeline

    load_start = time.time()
    quant_config = None
    if args.approach == "b":
        try:
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
            print(">>> Quantization config prepared (4-bit NF4 for Transformer).")
        except Exception as q_err:
            print(f">>> Quantization setup notice: {q_err}. Falling back to standard offload.")
            quant_config = None

    if quant_config is not None:
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            quantization_config=quant_config,
            torch_dtype=torch.bfloat16,
        )
    else:
        print(">>> Loading model in BF16...")
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
        )

    # Enable CPU offload to stay within memory limits
    pipe.enable_model_cpu_offload()

    # Enable tiled VAE if 2K
    if args.width >= 2048 or args.height >= 2048:
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
            pipe.vae.enable_tiling()

    print(f">>> Pipeline loaded successfully in {time.time() - load_start:.2f}s!")

    negative_prompt = "low quality, blurry, deformed anatomy, bad proportions, bad hands, cartoon, 3d render plastic look"

    results = []
    total_start = time.time()

    for idx, item in enumerate(PROMPTS, 1):
        prompt_id = item["id"]
        title = item["title"]
        prompt = item["prompt"]
        out_path = os.path.join(args.output_dir, f"{idx:02d}_{prompt_id}.png")

        print(f"\n------------------------------------------------------------------")
        print(f"[{idx}/{len(PROMPTS)}] Generating: {title}")
        print(f"Prompt: {prompt[:100]}...")
        if os.path.exists(out_path):
            file_size_kb = os.path.getsize(out_path) / 1024
            print(f">>> [SKIPPED] {out_path} already exists ({file_size_kb:.1f} KB).")
            results.append({
                "idx": idx,
                "id": prompt_id,
                "title": title,
                "time": 0.0,
                "size_kb": file_size_kb,
                "path": out_path
            })
            continue

        generator = torch.Generator("cuda").manual_seed(args.seed + idx)

        gen_start = time.time()
        with torch.inference_mode():
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=args.steps,
                true_cfg_scale=args.guidance_scale,
                width=args.width,
                height=args.height,
                generator=generator,
            )
            image = result.images[0]

        gen_time = time.time() - gen_start
        image.save(out_path)
        file_size_kb = os.path.getsize(out_path) / 1024

        print(f">>> Completed in {gen_time:.2f}s ({file_size_kb:.1f} KB)")
        results.append({
            "idx": idx,
            "id": prompt_id,
            "title": title,
            "time": gen_time,
            "size_kb": file_size_kb,
            "path": out_path
        })

    total_time = time.time() - total_start
    print("\n==================================================================")
    print(f" Batch generation complete! Total time: {total_time:.2f}s ({total_time/60:.2f} min)")
    print(" Summary:")
    for res in results:
        print(f"  [{res['idx']:02d}] {res['title']}: {res['time']:.1f}s, {res['size_kb']:.1f}KB -> {res['path']}")
    print("==================================================================")

if __name__ == "__main__":
    main()
