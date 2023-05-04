# Dry run to download and cache the models

from transformers import NllbTokenizer, AutoModelForSeq2SeqLM


tokenizer = NllbTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")

original_text = "Hello world!"
original_tokens = tokenizer(original_text, return_tensors="pt")
translated_tokens = model.generate(**original_tokens, forced_bos_token_id=tokenizer.lang_code_to_id["fra_Latn"], max_length=30)
translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

assert 'Bonjour le monde!' == translated_text