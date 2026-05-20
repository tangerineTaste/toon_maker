# core/novelai_client.py
import requests
import zipfile
import io
import random

def generate_novelai_image(api_key, prompt, neg_prompt, width, height, steps, cfg, sampler, model="nai-diffusion-3"):
    url = "https://image.novelai.net/ai/generate-image" 
    clean_key = api_key.strip()
    
    safe_width = (int(width) // 64) * 64
    safe_height = (int(height) // 64) * 64
    
    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json"
    }
    
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
            "cfg_rescale": 0.4,
            "noise_schedule": "native",
            "params_version": 3,
            "legacy": False,
            "legacy_v3_extend": False
        }
    }
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
            raise Exception(f"HTTP {response.status_code} | 상세 이유: {response.text}")
            
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            real_img_bytes = z.read(file_list[0])
            
        return real_img_bytes

    except Exception as e:
        raise Exception(f"NovelAI api Error: {str(e)}")