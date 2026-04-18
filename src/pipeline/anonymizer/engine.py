import re

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

from src.pipeline.anonymizer.recognizers import RussianINNRecognizer, RussianPhoneRecognizer, RussianSNILSRecognizer
from src.pipeline.anonymizer.token_mapping import TokenMapper


def create_analyzer() -> AnalyzerEngine:
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "ru", "model_name": "ru_core_news_md"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry(supported_languages=["ru", "en"])
    registry.load_predefined_recognizers(languages=["en", "ru"])
    registry.add_recognizer(RussianPhoneRecognizer())
    registry.add_recognizer(RussianINNRecognizer())
    registry.add_recognizer(RussianSNILSRecognizer())
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=["ru", "en"])


def create_anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()


ANONYMIZATION_OPERATORS = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON_>"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_NUMBER_>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_ADDRESS_>"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "<ADDRESS_>"}),
    "RUSSIAN_INN": OperatorConfig("replace", {"new_value": "<RUSSIAN_INN_>"}),
    "RUSSIAN_SNILS": OperatorConfig("replace", {"new_value": "<RUSSIAN_SNILS_>"}),
}


def anonymize_text(text: str, analyzer: AnalyzerEngine, anonymizer: AnonymizerEngine) -> str:
    if not text:
        return text

    results = analyzer.analyze(text=text, language="ru")
    if not results:
        return text

    entity_priority = {
        "RUSSIAN_INN": 100,
        "RUSSIAN_SNILS": 95,
        "EMAIL_ADDRESS": 90,
        "PHONE_NUMBER": 80,
        "PERSON": 70,
        "LOCATION": 60,
    }
    prioritized = sorted(
        results,
        key=lambda r: (r.start, -(r.end - r.start), -entity_priority.get(r.entity_type, 0), -r.score),
    )
    selected = []
    occupied = []
    for result in prioritized:
        if any(not (result.end <= start or result.start >= end) for start, end in occupied):
            continue
        occupied.append((result.start, result.end))
        selected.append(result)

    mapper = TokenMapper()
    output = text
    for result in sorted(selected, key=lambda r: r.start, reverse=True):
        original = text[result.start : result.end]
        normalized_entity = re.sub(r"[^A-Z0-9_]+", "_", result.entity_type.upper())
        token = mapper.get_or_create_token(normalized_entity, original)
        output = output[: result.start] + token + output[result.end :]
    return output
