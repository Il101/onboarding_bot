from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

from src.pipeline.anonymizer.engine import anonymize_text, create_analyzer, create_anonymizer
from src.pipeline.anonymizer.recognizers import RussianINNRecognizer, RussianPhoneRecognizer, RussianSNILSRecognizer
from src.pipeline.anonymizer.token_mapping import TokenMapper


def _build_analyzer() -> AnalyzerEngine:
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "ru", "model_name": "ru_core_news_md"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry(supported_languages=["ru"])
    registry.load_predefined_recognizers(languages=["ru"])
    registry.add_recognizer(RussianPhoneRecognizer())
    registry.add_recognizer(RussianINNRecognizer())
    registry.add_recognizer(RussianSNILSRecognizer())
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=["ru"])


def test_russian_phone_intl_format():
    analyzer = _build_analyzer()
    results = analyzer.analyze(text="Call +7(903)123-45-67", language="ru")
    assert any(r.entity_type == "PHONE_NUMBER" for r in results)


def test_russian_phone_8_format():
    analyzer = _build_analyzer()
    results = analyzer.analyze(text="Number 89031234567", language="ru")
    assert any(r.entity_type == "PHONE_NUMBER" for r in results)


def test_inn_detected():
    analyzer = _build_analyzer()
    results = analyzer.analyze(text="Tax ID 7707083893", language="ru")
    assert any(r.entity_type == "RUSSIAN_INN" for r in results)


def test_snils_detected():
    analyzer = _build_analyzer()
    results = analyzer.analyze(text="SNILS 123-456-789 01", language="ru")
    assert any(r.entity_type == "RUSSIAN_SNILS" for r in results)


def test_same_value_same_token():
    mapper = TokenMapper()
    t1 = mapper.get_or_create_token("PERSON", "Ivanov")
    t2 = mapper.get_or_create_token("PERSON", "Ivanov")
    assert t1 == t2 == "<PERSON_1>"


def test_different_values_different_tokens():
    mapper = TokenMapper()
    t1 = mapper.get_or_create_token("PERSON", "Ivanov")
    t2 = mapper.get_or_create_token("PERSON", "Petrov")
    assert t1 == "<PERSON_1>" and t2 == "<PERSON_2>"


def test_separate_counters_per_type():
    mapper = TokenMapper()
    t1 = mapper.get_or_create_token("PERSON", "Ivanov")
    t2 = mapper.get_or_create_token("PHONE_NUMBER", "+79031234567")
    assert t1 == "<PERSON_1>" and t2 == "<PHONE_NUMBER_1>"


def test_resolve_valid_token():
    mapper = TokenMapper()
    mapper.get_or_create_token("PERSON", "Ivanov")
    assert mapper.resolve("<PERSON_1>") == "Ivanov"


def test_resolve_unknown_returns_none():
    mapper = TokenMapper()
    assert mapper.resolve("<PERSON_99>") is None


def test_phone_anonymized():
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    text = "Call +7(903)123-45-67"
    result = anonymize_text(text, analyzer, anonymizer)
    assert "+7(903)123-45-67" not in result
    assert "<PHONE_NUMBER_" in result


def test_email_anonymized():
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    text = "Email: ivan@company.ru"
    result = anonymize_text(text, analyzer, anonymizer)
    assert "<EMAIL_ADDRESS_" in result


def test_inn_anonymized():
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    text = "Tax ID 7707083893"
    result = anonymize_text(text, analyzer, anonymizer)
    assert "<RUSSIAN_INN_" in result


def test_no_pii_unchanged():
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    text = "Regular text without personal data"
    result = anonymize_text(text, analyzer, anonymizer)
    assert result == text


def test_multiple_pii_sequential_tokens():
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    text = "Phones +7(903)123-45-67 and 89031234567"
    result = anonymize_text(text, analyzer, anonymizer)
    assert "<PHONE_NUMBER_1>" in result
    assert "<PHONE_NUMBER_2>" in result


def test_full_pii_text(sample_pii_text):
    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    result = anonymize_text(sample_pii_text, analyzer, anonymizer)
    assert "<PHONE_NUMBER_" in result
    assert "<EMAIL_ADDRESS_" in result
    assert "<RUSSIAN_INN_" in result
