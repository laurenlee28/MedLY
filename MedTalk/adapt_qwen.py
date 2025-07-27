from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline

model_path = "/Users/jaemin/Desktop/Edge AI/MedTalk/model/qwen_model"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)

pipe = TextGenerationPipeline(model=model, tokenizer=tokenizer, device=-1)  # CPU

prompt = "의학 용어 '간염'에 대해서 초등학생도 이해할 수 있도록 쉽게 설명해줘."
output = pipe(prompt, max_new_tokens=64)
print(output)