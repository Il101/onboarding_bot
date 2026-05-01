#!/usr/bin/env python
"""
Create comprehensive test data for V-Brain system.
Generates: Telegram export file, creates sources, runs ingest, publishes knowledge.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from src.api.deps import SessionLocal
from src.core.logging import get_logger
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.models.source import Source, SourceType

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
    # Published items (English for screenshots)
    published_items = [
        {
            "topic": "Onboarding",
            "fact": "New employee onboarding takes place every Monday at 10:00 AM in the office. Please bring passport, SNILS, and INN.",
            "confidence": 0.95,
        },
        {
            "topic": "IT Support",
            "fact": "For system access, email support@company.com. You will receive login credentials for email, Jira, and Confluence.",
            "confidence": 0.90,
        },
        {
            "topic": "Wi-Fi",
            "fact": "Office Wi-Fi: SSID = V-Brain, password = Welcome2024. Password changes monthly.",
            "confidence": 0.92,
        },
        {
            "topic": "Salary",
            "fact": "Salary is paid on the 25th of each month to your bank card. Transfer usually arrives before 3:00 PM.",
            "confidence": 0.98,
        },
        {
            "topic": "Vacation",
            "fact": "Minimum vacation is 14 days. Submit request at least 2 weeks in advance. Must be approved by manager.",
            "confidence": 0.88,
        },
        {
            "topic": "Sick Leave",
            "fact": "First 3 days of sick leave are paid by employer, then per sick leave certificate. Provide certificate within 5 days.",
            "confidence": 0.90,
        },
        {
            "topic": "Office Amenities",
            "fact": "Coffee and tea are free in the break area. Lunch in cafeteria from 12:00 to 14:00. Lunch budget is 500 rubles.",
            "confidence": 0.85,
        },
        {
            "topic": "IT Issues",
            "fact": "For computer issues: 1) Restart, 2) Check internet, 3) Submit ticket or call 8-800-IT-HELP.",
            "confidence": 0.87,
        },
        {
            "topic": "Meetings",
            "fact": "Duty schedule is published in the calendar. Daily standup at 10:30 AM in Zoom. Link: company.zoom.us/daily-standup",
            "confidence": 0.86,
        },
        {
            "topic": "Access Badge",
            "fact": "Office access badge is issued at reception on the first floor. Do not share your badge with other employees.",
            "confidence": 0.95,
        },
        {
            "topic": "Bonuses",
            "fact": "Bonuses are paid quarterly based on performance. Maximum bonus is 30% of base salary.",
            "confidence": 0.85,
        },
        {
            "topic": "VPN",
            "fact": "Company uses WireGuard for VPN. Configuration sent by email after onboarding. Never share your secret key.",
            "confidence": 0.90,
        },
        {
            "topic": "Code Review",
            "fact": "Each PR requires at least one approval. Review time is up to 24 business hours.",
            "confidence": 0.88,
        },
        {
            "topic": "Overtime",
            "fact": "Overtime is paid at 1.5x hourly rate. Working more than 4 hours overtime is prohibited without permission.",
            "confidence": 0.89,
        },
        {
            "topic": "Office Supplies",
            "fact": "Office supplies (pens, notebooks) are in the kitchen cabinet. If anything runs out, message the office manager.",
            "confidence": 0.82,
        },
        {
            "topic": "GitHub",
            "fact": "GitHub organization: v-brain-corp. Repositories are private. Request access after being added to the team.",
            "confidence": 0.90,
        },
        {
            "topic": "Development Plan",
            "fact": "Individual Development Plan (IDP) is created in the first month. Discuss 3-month goals with your manager.",
            "confidence": 0.85,
        },
    ]

    # Pending review items (for variety in admin panel)
    pending_items = [
        {
            "topic": "Remote Work",
            "fact": "Remote work is allowed up to 2 days per week with manager approval. Requires VPN access.",
            "confidence": 0.75,
        },
        {
            "topic": "Training Budget",
            "fact": "Annual training budget is 50,000 rubles per employee. Requires prior approval and expense report.",
            "confidence": 0.68,
        },
        {
            "topic": "Parking",
            "fact": "Parking is available in the underground lot. Monthly fee is 5,000 rubles. Register with security.",
            "confidence": 0.82,
        },
        {
            "topic": "Conference Room",
            "fact": "Book conference rooms via Google Calendar. Maximum booking is 4 hours. Cancellations required 1 hour prior.",
            "confidence": 0.70,
        },
        {
            "topic": "Equipment",
            "fact": "Laptops are provided on day 1. Additional monitors require business justification approved by IT director.",
            "confidence": 0.78,
        },
    ]

    created = 0

    # Create published items
    for item_data in published_items:
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

    # Create pending items
    for item_data in pending_items:
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
                status=KnowledgeStatus.PENDING,
            )
            db.add(item)
            created += 1

    db.commit()
    return created


def main() -> int:
    print("Creating test data for V-Brain\n")

    # Create Telegram export file
    print("1. Creating Telegram export...")
    telegram_file = create_realistic_telegram_export()
    print(f"   ✓ File created: {telegram_file}")

    # Create database entries
    db = SessionLocal()
    try:
        print("\n2. Creating Source record...")
        existing_source = db.query(Source).filter_by(filename="test_onboarding.json").first()

        if not existing_source:
            import uuid

            from src.models.source import IngestStatus
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
            print(f"   ✓ Source created (ID: {source_id})")
        else:
            source_id = existing_source.id
            print(f"   ✓ Source already exists (ID: {source_id})")

        print("\n3. Creating Knowledge Items...")
        created_items = create_test_knowledge_items(db, source_id)
        print(f"   ✓ Created {created_items} knowledge items")

        # Verify
        total_items = db.query(KnowledgeItem).count()
        published_items = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PUBLISHED).count()
        pending_items = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PENDING).count()

        print("\n4. Final statistics:")
        print(f"   Total items in DB: {total_items}")
        print(f"   Published: {published_items}")
        print(f"   Pending review: {pending_items}")

        print("\n✓ Test data created successfully!")
        print("\nNow you can run the integration test:")
        print("   python scripts/integration_test.py")

        return 0

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
