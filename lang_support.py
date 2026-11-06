from typing import overload
import json

class Lang:
    USING_LANG: str | None = "türkçe"

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

    def to_dict(self) -> dict:
        return {
            "languages": self.languages
        }

    def to_json(self):
        return json.loads(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> "Lang":
        return cls(
            **d["languages"]
        )

    @classmethod
    def from_json(cls, j) -> "Lang":
        return Lang.from_dict(json.loads(j))

    def __str__(self):
        if Lang.USING_LANG is not None:
            return self.__call__()

        else:
            return self.__call__("english")
