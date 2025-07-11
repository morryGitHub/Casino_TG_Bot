from lexicon.vocabulary import LEXICON_RU
from lexicon.vocabulary import LEXICON_EN

class Lexicon:
    def __init__(self, lexicons, default_lang='ru'):
        self.lexicons = lexicons
        self.default_lang = default_lang

    def get(self, lang: str, key: str, **kwargs) -> str:
        lexicon = self.lexicons.get(lang, self.lexicons[self.default_lang])
        text = lexicon.get(key, '')
        try:
            return text.format(**kwargs)
        except Exception:
            return text


LEXICON = {
    'ru': LEXICON_RU,
    'en': LEXICON_EN
}

lexicon = Lexicon(LEXICON)
