from presidio_analyzer import Pattern, PatternRecognizer


class RussianPhoneRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern(
            name="russian_phone_intl",
            regex=r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}",
            score=0.7,
        ),
        Pattern(
            name="russian_phone_short",
            regex=r"\b\d{10}\b",
            score=0.3,
        ),
    ]

    def __init__(self):
        super().__init__(supported_entity="PHONE_NUMBER", patterns=self.PATTERNS, supported_language="ru")


class RussianINNRecognizer(PatternRecognizer):
    def __init__(self):
        super().__init__(
            supported_entity="RUSSIAN_INN",
            patterns=[
                Pattern(
                    name="russian_inn",
                    regex=r"\b\d{10}\b|\b\d{12}\b",
                    score=0.4,
                )
            ],
            supported_language="ru",
        )


class RussianSNILSRecognizer(PatternRecognizer):
    def __init__(self):
        super().__init__(
            supported_entity="RUSSIAN_SNILS",
            patterns=[
                Pattern(
                    name="russian_snils",
                    regex=r"\b\d{3}[\-\s]\d{3}[\-\s]\d{3}[\-\s]\d{2}\b",
                    score=0.6,
                )
            ],
            supported_language="ru",
        )
