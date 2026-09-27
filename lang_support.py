from typing import overload

class Lang:
    USING_LANG: str | None = None

    def __init__(self, **languages):
        self.languages = languages

    def get(self, language: str):
        return self.languages.get(language.lower(), "Unknown")

    @overload
    def __call__(self, language: str) -> str: ...

    @overload
    def __call__(self) -> str: ...

    def __call__(self, language: str = None):
        if Lang.USING_LANG is not None:
            if language is None:
                return self.languages.get(Lang.USING_LANG.lower(), "Unknown")

            else:
                return self.languages.get(language.lower(), "Unknown")

        else:
            if language is None:
                raise Exception("Did not given language but Lang.USING_LANG is None.")

            else:
                return self.languages.get(language.lower(), "Unknown")

