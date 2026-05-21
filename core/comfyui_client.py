# core/comfyui_client.py
import json
import time
import random
import urllib.request
import urllib.parse
import os

def generate_comfyui_image(server_url, prompt, neg_prompt, width, height, steps, cfg, sampler, scheduler, ckpt_name, lora_name, seed):
    if not server_url.startswith("http"):
        server_url = "http://" + server_url
        
    if not seed or str(seed).strip() == "-1":
        seed = random.randint(1, 1125899906842624)
    else:
        try: seed = int(seed)
        except: seed = random.randint(1, 1125899906842624)

    sampler_clean = sampler.replace("k_", "") 

    api_json_path = os.path.join(os.path.dirname(__file__), "workflow_api.json")
    if not os.path.exists(api_json_path):
        raise Exception("workflow_api.json 파일이 core 폴더에 없습니다!")

    with open(api_json_path, "r", encoding="utf-8") as f:
        workflow_str = f.read()

    has_placeholder = "[PROMPT]" in workflow_str or "[NEG_PROMPT]" in workflow_str
    workflow = json.loads(workflow_str)
    
    for node in workflow.values():
        cls_type = node.get("class_type", "")
        inputs = node.get("inputs", {})
        
        # 1. 프롬프트 치환
        for k, v in inputs.items():
            if isinstance(v, str):
                if has_placeholder:
                    if "[PROMPT]" in v: inputs[k] = v.replace("[PROMPT]", prompt)
                    if "[NEG_PROMPT]" in v: inputs[k] = v.replace("[NEG_PROMPT]", neg_prompt)
                else:
                    if k in ["text", "text_g", "text_l", "string", "value"]:
                        if len(v) > 2 and not v.endswith(".safetensors") and not v.endswith(".pt") and not v.endswith(".pth"):
                            v_low = v.lower()
                            neg_words = ["bad", "worst", "lowres", "ugly", "error", "missing", "watermark", "jpeg"]
                            if any(w in v_low for w in neg_words): inputs[k] = neg_prompt
                            else: inputs[k] = prompt

        # 2. SpectrumKSamplerModGuidance 및 모든 KSampler 호환 세팅 이식
        if "KSampler" in cls_type:
            if "seed" in inputs: inputs["seed"] = seed
            elif "noise_seed" in inputs: inputs["noise_seed"] = seed
            if "steps" in inputs: inputs["steps"] = int(steps)
            if "cfg" in inputs: inputs["cfg"] = float(cfg)
            if "sampler_name" in inputs: inputs["sampler_name"] = sampler_clean
            if "scheduler" in inputs: inputs["scheduler"] = scheduler 

        # 3. UNETLoader 
        if cls_type in ["CheckpointLoaderSimple", "UNETLoader", "AnimaUNetLoader"]:
            if "ckpt_name" in inputs: inputs["ckpt_name"] = ckpt_name
            elif "unet_name" in inputs: inputs["unet_name"] = ckpt_name
            
        # 4. Lora Loader (LoraManager)
        if cls_type == "Lora Loader (LoraManager)":
            if lora_name:
                clean_lora = lora_name.replace(".safetensors", "").replace(".ckpt", "")
                inputs["text"] = f"<lora:{clean_lora}:0.85>"
                inputs["loras"] = {
                    "__value__": [
                        {
                            "name": clean_lora,
                            "strength": "0.85",
                            "active": True,
                            "expanded": False,
                            "clipStrength": "0.85",
                            "locked": False
                        }
                    ]
                }
                
        # 5. 해상도 치환
        if cls_type == "EmptyLatentImage":
            if "width" in inputs: inputs["width"] = int(width)
            if "height" in inputs: inputs["height"] = int(height)

    req_data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(f"{server_url}/prompt", data=req_data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            prompt_id = result['prompt_id']
    except Exception as e:
        raise Exception(f"ComfyUI 서버 통신 실패: {e}")

    while True:
        try:
            hist_req = urllib.request.Request(f"{server_url}/history/{prompt_id}")
            with urllib.request.urlopen(hist_req) as hist_resp:
                history = json.loads(hist_resp.read())
            if prompt_id in history: break
        except Exception:
            pass
        time.sleep(0.5)

    try:
        history_data = history[prompt_id]
        for node_id in history_data['outputs']:
            node_output = history_data['outputs'][node_id]
            if 'images' in node_output:
                img_info = node_output['images'][0]
                url_values = urllib.parse.urlencode({'filename': img_info['filename'], 'subfolder': img_info['subfolder'], 'type': img_info['type']})
                img_req = urllib.request.Request(f"{server_url}/view?{url_values}")
                with urllib.request.urlopen(img_req) as img_resp:
                    return img_resp.read()
    except Exception as e:
        raise Exception(f"이미지 다운로드 실패: {e}")
        
    raise Exception("ComfyUI 응답에서 이미지를 찾을 수 없습니다!")