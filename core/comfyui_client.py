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
                # 콤마로 구분된 다중 LoRA 문자열을 리스트로 분해
                lora_list = [l.strip() for l in lora_name.split(",") if l.strip()]
                
                loras_value_array = []
                lora_text_tags = []
                
                for lora_item in lora_list:
                    # "파일명:가중치" 구조 분해 (가중치가 없으면 1.0으로 처리)
                    parts = lora_item.split(":")
                    name = parts[0].strip()
                    weight = parts[1].strip() if len(parts) > 1 else "1.0"
                    
                    # 프롬프트 내부 호출용 이름 정제 (확장자 제거)
                    clean_name = name.replace(".safetensors", "").replace(".ckpt", "")
                    
                    # 1) Trigger Text 태그 추가
                    lora_text_tags.append(f"<lora:{clean_name}:{weight}>")
                    
                    # 2) Manager 노드용 JSON 객체 생성
                    loras_value_array.append({
                        "name": clean_name,
                        "strength": str(weight),
                        "active": True,
                        "expanded": False,
                        "clipStrength": str(weight),
                        "locked": False
                    })
                
                # 병합된 데이터 최종 주입
                inputs["text"] = " ".join(lora_text_tags)
                inputs["loras"] = {
                    "__value__": loras_value_array
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