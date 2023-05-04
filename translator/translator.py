from transformers import NllbTokenizer, AutoModelForSeq2SeqLM

MAX_TRANSLATION_LENGTH = 30

MODEL = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")

class Translator:
    def __init__(self, from_language, to_language):
        self.from_language = from_language
        self.to_language = to_language
        self.tokenizer = NllbTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", src_lang=from_language)

    def translate(self, original_text):
        original_tokens = self.tokenizer(original_text, return_tensors="pt")
        translated_tokens = MODEL.generate(
            **original_tokens,
            forced_bos_token_id=self.tokenizer.lang_code_to_id[self.to_language],
            max_length=MAX_TRANSLATION_LENGTH
        )
        translated_text = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        return translated_text


class PingPong:
    def __init__(self, from_language, to_language, original_text, number_repeats):
        self.from_language = from_language
        self.to_language = to_language
        self.original_text = original_text
        self.number_repeats = number_repeats
        
        self.translation_list = [original_text]
        self.is_looped = False

        self.ping_translator = Translator(from_language, to_language)
        self.pong_translator = Translator(to_language, from_language)
    
    def run(self):
        if self.is_looped:
            return
        
        ping_text = self.translation_list[-1]
        for _ in range(self.number_repeats):
            pong_text = self.ping_translator.translate(ping_text)
            ping_text_new = self.pong_translator.translate(pong_text)
            
            self.translation_list.append(pong_text)
            self.translation_list.append(ping_text_new)

            if ping_text == ping_text_new:
                self.is_looped = True
                break
            else:
                ping_text = ping_text_new


if __name__ == "__main__":
    # --from-language "eng_Latn" --to-language "pol_Latn" --text "Hello world!" --num-repeats 2
    import argparse
    parser = argparse.ArgumentParser(
        prog='Ping Pong Translator',
        description='Translates back and forth between two different languages'
    )
    
    parser.add_argument("--from-language", help="Source language code as in FLORES-200", required=True)
    parser.add_argument("--to-language", help="Target language code as in FLORES-200", required=True)
    parser.add_argument("--text", help="Original text to translate, in Source Language", required=True)
    parser.add_argument("--number-repeats", help="Number of repeats", required=True)

    args = parser.parse_args()

    pp = PingPong(
        args.from_language,
        args.to_language,
        args.text,
        int(args.number_repeats)
    )

    pp.run()

    for i, el in enumerate(pp.translation_list):
        if i % 2 == 1:
            print("    ", el)
        else:
            print(el)
    if pp.is_looped:
        print("# Looped #")