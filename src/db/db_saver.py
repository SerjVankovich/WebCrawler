import logging
from sqlalchemy import create_engine
from src.db.base import Base
from sqlalchemy.orm import sessionmaker

from src.db.entities.external_link import ExternalDomain
from src.db.entities.internal_link import InternalLink


class DBSaver():
    def __init__(self, db_url):
        logging.basicConfig(
            filename="db_saver.log",
            filemode='w',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger("db_saver")

        self.engine = create_engine(db_url)
        # Создание таблиц, если их ещё нет
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_to_db(self, internal_links, external_links):
        """Сохранение внутренних ссылок и внешних доменов в базу данных"""
        # Сохраняем внутренние ссылки в таблицу
        for link, count in internal_links.items():
            # Проверяем, существует ли ссылка
            existing_link = self.session.query(
                InternalLink).filter_by(url=link).first()
            if existing_link:
                existing_link.count = count
            else:
                new_link = InternalLink(url=link, count=count)
                self.session.add(new_link)

        # Сохраняем внешние домены в таблицу
        for domain, count in external_links.items():
            # Проверяем, существует ли домен
            existing_domain = self.session.query(
                ExternalDomain).filter_by(domain=domain).first()
            if existing_domain:
                existing_domain.count = count
            else:
                new_domain = ExternalDomain(domain=domain, count=count)
                self.session.add(new_domain)

        self.session.commit()
        self.logger.info(
            f"Saved {len(internal_links)} internal links and {len(external_links)} external domains to the database")

    def close(self):
        """Закрытие сессии базы данных"""
        self.session.close()
        self.logger.info("Database session closed")
