class Lang:
    def __init__(self, **languages):
        self.languages = languages

    def get(self, language: str):
        return self.languages.get(language.lower(), "Unknown")

