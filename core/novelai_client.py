import requests
import zipfile
import io
import random

def generate_novelai_image(api_key, prompt, neg_prompt, width, height, steps, cfg, sampler, model="nai-diffusion-3", seed="", cfg_rescale=0.2, noise_schedule="native"):
    url = "https://image.novelai.net/ai/generate-image" 
    
    safe_width = (int(width) // 64) * 64
    safe_height = (int(height) // 64) * 64
    
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    try:
        if seed and str(seed).strip() != "-1":
            nai_seed = int(seed)
        else:
            nai_seed = random.randint(1, 99999999)
    except ValueError:
        nai_seed = random.randint(1, 99999999)
    
    payload = {
        "input": prompt,
        "model": model,
        "action": "generate",
        "parameters": {
            "width": safe_width,
            "height": safe_height,
            "n_samples": 1,
            "seed": nai_seed,                 
            "extra_noise_seed": nai_seed,
            "sampler": sampler,
            "steps": int(steps),
            "scale": float(cfg),
            "negative_prompt": neg_prompt,
            "cfg_rescale": float(cfg_rescale),
            "noise_schedule": noise_schedule,
            "params_version": 3,
            "legacy": False,
            "legacy_v3_extend": False
        }
    }
    
    # (이하 V4 프롬프트 규격 if문 및 통신 부분은 기존 코드 유지)
    if model.startswith("nai-diffusion-4"):
        payload["parameters"]["v4_prompt"] = {
            "caption": {
                "base_caption": prompt,
                "char_captions": []
            },
            "use_coords": False,
            "use_order": True
        }
        payload["parameters"]["v4_negative_prompt"] = {
            "caption": {
                "base_caption": neg_prompt,
                "char_captions": []
            }
        }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} | 상세 사유: {response.text}")
            
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            real_img_bytes = z.read(z.namelist()[0])
        return real_img_bytes
    except Exception as e:
        raise Exception(f"NovelAI API 뇌절: {str(e)}")