#!/usr/bin/env python
"""
Create comprehensive test data for V-Brain system.
Generates: Telegram export file, creates sources, runs ingest, publishes knowledge.
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from src.api.deps import SessionLocal
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.models.source import Source, SourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


def create_realistic_telegram_export() -> str:
    """Create a realistic Telegram export JSON file."""
    messages = [
        {
            "id": 1,
            "type": "message",
            "date": "2024-01-15T09:00:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Всем привет! Добро пожаловать в команду V-Brain. Напоминаю важную информацию для новых сотрудников.",
        },
        {
            "id": 2,
            "type": "message",
            "date": "2024-01-15T09:05:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Онбординг новых сотрудников проходит каждый понедельник в 10:00 в офисе по адресу ул. Примерная, д. 1. Пожалуйста, принесите паспорт, СНИЛС и ИНН.",
        },
        {
            "id": 3,
            "type": "message",
            "date": "2024-01-15T09:10:00",
            "from": "IT Department",
            "from_id": 101,
            "text": "Для доступа к системам напишите на support@company.com. Вам выдадут логин и пароль для почты, Jira и Confluence.",
        },
        {
            "id": 4,
            "type": "message",
            "date": "2024-01-15T09:15:00",
            "from": "IT Department",
            "from_id": 101,
            "text": "Wi-Fi в офисе: SSID = V-Brain, пароль = Welcome2024. Смена пароля каждый месяц.",
        },
        {
            "id": 5,
            "type": "message",
            "date": "2024-01-15T09:20:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Зарплата выплачивается 25-го числа каждого месяца на карту. Перевод обычно приходит до 15:00.",
        },
        {
            "id": 6,
            "type": "message",
            "date": "2024-01-15T09:25:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "ОТПУСК: Минимальный отпуск 14 дней. Заявление подавать минимум за 2 недели. Согласовывать с руководителем.",
        },
        {
            "id": 7,
            "type": "message",
            "date": "2024-01-15T09:30:00",
            "from": "Office Manager",
            "from_id": 102,
            "text": "Кофе и чай бесплатные в зоне отдыха. Обед в столовой с 12:00 до 14:00. Бюджет на обед 500 рублей.",
        },
        {
            "id": 8,
            "type": "message",
            "date": "2024-01-15T09:35:00",
            "from": "IT Department",
            "from_id": 101,
            "text": "В случае проблем с компьютером: 1) Перезагрузите, 2) Проверьте интернет, 3) Напишите в тикет-систему или позвоните на 8-800-IT-HELP.",
        },
        {
            "id": 9,
            "type": "message",
            "date": "2024-01-15T09:40:00",
            "from": "Team Lead",
            "from_id": 103,
            "text": "Дежурства: График публикуется в календаре. Ежедневный стендап в 10:30 в Zoom. Ссылка: company.zoom.us/daily-standup",
        },
        {
            "id": 10,
            "type": "message",
            "date": "2024-01-15T09:45:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Больничный: Первые 3 дня оплачиваются работодателем, далее по больничному листу. Справку предоставить в течение 5 дней.",
        },
        {
            "id": 11,
            "type": "message",
            "date": "2024-01-15T09:50:00",
            "from": "Security",
            "from_id": 104,
            "text": "Пропуск в офис выдается в первом отделении на первом этаже. Не передавайте пропуск другим сотрудникам.",
        },
        {
            "id": 12,
            "type": "message",
            "date": "2024-01-15T09:55:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Премии выплачиваются квартально по результатам работы. Максимальная премия 30% от оклада.",
        },
        {
            "id": 13,
            "type": "message",
            "date": "2024-01-15T10:00:00",
            "from": "IT Department",
            "from_id": 101,
            "text": "VPN: Компания использует WireGuard. Конфиг на почте после оформления. Секретный ключ не передавать никому.",
        },
        {
            "id": 14,
            "type": "message",
            "date": "2024-01-15T10:05:00",
            "from": "Team Lead",
            "from_id": 103,
            "text": "Code Review: Каждый PR требует минимум одного одобрения. Время на ревью до 24 часов рабочих дней.",
        },
        {
            "id": 15,
            "type": "message",
            "date": "2024-01-15T10:10:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Переработки оплачиваются по ставке 1.5 от часовой. Работать больше 4 часов сверхурочно запрещено без разрешения.",
        },
        {
            "id": 16,
            "type": "service_message",
            "text": "Photo",
        },
        {
            "id": 17,
            "type": "message",
            "date": "2024-01-15T10:15:00",
            "from": "New Employee",
            "from_id": 200,
            "text": "Спасибо за информацию! А где взять ручки и тетради?",
        },
        {
            "id": 18,
            "type": "message",
            "date": "2024-01-15T10:20:00",
            "from": "Office Manager",
            "from_id": 102,
            "text": "Канцелярия в шкафу на кухне. Если что-то закончилось, напишите мне, закажу.",
        },
        {
            "id": 19,
            "type": "message",
            "date": "2024-01-15T10:25:00",
            "from": "Team Lead",
            "from_id": 103,
            "text": "GitHub: Организация v-brain-corp. Репозитории приватные. После добавления в команду запросите доступ.",
        },
        {
            "id": 20,
            "type": "message",
            "date": "2024-01-15T10:30:00",
            "from": "HR Department",
            "from_id": 100,
            "text": "Индивидуальный план развития (ИПР) составляется в первый месяц работы. Обсудите с руководителем задачи на 3 месяца.",
        },
    ]

    telegram_export = {"messages": messages}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(telegram_export, f, ensure_ascii=False, indent=2)
        return f.name


def create_test_knowledge_items(db: Session, source_id: str) -> int:
    """Create test knowledge items directly in the database."""
    items_data = [
        {
            "topic": "Онбординг",
            "fact": "Онбординг новых сотрудников проходит каждый понедельник в 10:00 в офисе. Необходимо принести паспорт, СНИЛС и ИНН.",
            "confidence": 0.95,
        },
        {
            "topic": "IT Поддержка",
            "fact": "Для доступа к системам напишите на support@company.com. Выдадут логин и пароль для почты, Jira и Confluence.",
            "confidence": 0.90,
        },
        {
            "topic": "Wi-Fi",
            "fact": "Wi-Fi в офисе: SSID = V-Brain, пароль = Welcome2024. Смена пароля каждый месяц.",
            "confidence": 0.92,
        },
        {
            "topic": "Зарплата",
            "fact": "Зарплата выплачивается 25-го числа каждого месяца на карту. Перевод обычно приходит до 15:00.",
            "confidence": 0.98,
        },
        {
            "topic": "Отпуск",
            "fact": "Минимальный отпуск 14 дней. Заявление подавать минимум за 2 недели. Согласовывать с руководителем.",
            "confidence": 0.88,
        },
        {
            "topic": "Больничный",
            "fact": "Первые 3 дня больничного оплачиваются работодателем, далее по больничному листу. Справку предоставить в течение 5 дней.",
            "confidence": 0.90,
        },
        {
            "topic": "Кофе и обед",
            "fact": "Кофе и чай бесплатные в зоне отдыха. Обед в столовой с 12:00 до 14:00. Бюджет на обед 500 рублей.",
            "confidence": 0.85,
        },
        {
            "topic": "IT Проблемы",
            "fact": "При проблемах с компьютером: 1) Перезагрузите, 2) Проверьте интернет, 3) Напишите в тикет-систему или позвоните на 8-800-IT-HELP.",
            "confidence": 0.87,
        },
        {
            "topic": "Дежурства и встречи",
            "fact": "График дежурств публикуется в календаре. Ежедневный стендап в 10:30 в Zoom. Ссылка: company.zoom.us/daily-standup",
            "confidence": 0.86,
        },
        {
            "topic": "Пропуск",
            "fact": "Пропуск в офис выдается в первом отделении на первом этаже. Не передавайте пропуск другим сотрудникам.",
            "confidence": 0.95,
        },
        {
            "topic": "Премии",
            "fact": "Премии выплачиваются квартально по результатам работы. Максимальная премия 30% от оклада.",
            "confidence": 0.85,
        },
        {
            "topic": "VPN",
            "fact": "Компания использует WireGuard для VPN. Конфиг на почте после оформления. Секретный ключ не передавать никому.",
            "confidence": 0.90,
        },
        {
            "topic": "Code Review",
            "fact": "Каждый PR требует минимум одного одобрения. Время на ревью до 24 часов рабочих дней.",
            "confidence": 0.88,
        },
        {
            "topic": "Переработки",
            "fact": "Переработки оплачиваются по ставке 1.5 от часовой. Работать больше 4 часов сверхурочно запрещено без разрешения.",
            "confidence": 0.89,
        },
        {
            "topic": "Канцелярия",
            "fact": "Канцелярия (ручки, тетради) в шкафу на кухне. Если что-то закончилось, написать офис-менеджеру.",
            "confidence": 0.82,
        },
        {
            "topic": "GitHub",
            "fact": "Организация GitHub: v-brain-corp. Репозитории приватные. После добавления в команду запросить доступ.",
            "confidence": 0.90,
        },
        {
            "topic": "ИПР",
            "fact": "Индивидуальный план развития (ИПР) составляется в первый месяц работы. Обсудить с руководителем задачи на 3 месяца.",
            "confidence": 0.85,
        },
    ]

    created = 0
    for item_data in items_data:
        existing = db.query(KnowledgeItem).filter_by(
            source_refs=f'["{source_id}"]',
            fact=item_data["fact"]
        ).first()

        if not existing:
            item = KnowledgeItem(
                source_refs=f'["{source_id}"]',
                topic=item_data["topic"],
                fact=item_data["fact"],
                confidence=item_data["confidence"],
                status=KnowledgeStatus.PUBLISHED,
            )
            db.add(item)
            created += 1

    db.commit()
    return created


def main() -> int:
    print("Создание тестовых данных для V-Brain\n")

    # Create Telegram export file
    print("1. Создание Telegram экспорта...")
    telegram_file = create_realistic_telegram_export()
    print(f"   ✓ Файл создан: {telegram_file}")

    # Create database entries
    db = SessionLocal()
    try:
        print("\n2. Создание Source записи...")
        existing_source = db.query(Source).filter_by(filename="test_onboarding.json").first()

        if not existing_source:
            from src.models.source import IngestStatus
            import uuid
            source_id = str(uuid.uuid4())
            source = Source(
                id=source_id,
                type=SourceType.TELEGRAM,
                filename="test_onboarding.json",
                file_path=telegram_file,
                status=IngestStatus.COMPLETED,
            )
            db.add(source)
            db.commit()
            print(f"   ✓ Source создан (ID: {source_id})")
        else:
            source_id = existing_source.id
            print(f"   ✓ Source уже существует (ID: {source_id})")

        print("\n3. Создание Knowledge Items...")
        created_items = create_test_knowledge_items(db, source_id)
        print(f"   ✓ Создано {created_items} knowledge items")

        # Verify
        total_items = db.query(KnowledgeItem).count()
        published_items = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PUBLISHED).count()

        print(f"\n4. Итоговая статистика:")
        print(f"   Всего items в БД: {total_items}")
        print(f"   Опубликовано: {published_items}")

        print(f"\n✓ Тестовые данные успешно созданы!")
        print(f"\nТеперь можно запустить интеграционный тест:")
        print(f"   python scripts/integration_test.py")

        return 0

    except Exception as e:
        db.rollback()
        print(f"\n✗ Ошибка: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
