from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import psycopg

from apps.workers.queues import queue_name_for_domain
from libs.core.config import get_settings


@dataclass(frozen=True, slots=True)
class DomainWorkerConfig:
    domain_id: str
    domain_name: str
    queue: str
    worker_name: str
    start_command: str


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate per-domain Celery worker configuration for active domains."
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    args = parser.parse_args()

    configs = load_domain_worker_configs()

    if args.format == "json":
        print(json.dumps([asdict(item) for item in configs], indent=2))
    else:
        if not configs:
            print("No active verified domains found.")
            return 0
        for item in configs:
            print(f"{item.domain_name} -> {item.queue}")
            print(f"  {item.start_command}")
    return 0


def load_domain_worker_configs() -> list[DomainWorkerConfig]:
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    query = """
        SELECT id::text, name
        FROM domains
        WHERE verification_status = 'verified'
          AND reputation_status NOT IN ('retired', 'burnt')
        ORDER BY name ASC
    """
    configs: list[DomainWorkerConfig] = []
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            for domain_id, domain_name in cursor.fetchall():
                queue = queue_name_for_domain(str(domain_name))
                worker_name = f"send_{_safe_worker_fragment(str(domain_name))}"
                command = (
                    "celery -A apps.workers.celery_app worker "
                    f"-Q {queue} -n {worker_name}@%h --loglevel=INFO"
                )
                configs.append(
                    DomainWorkerConfig(
                        domain_id=str(domain_id),
                        domain_name=str(domain_name),
                        queue=queue,
                        worker_name=worker_name,
                        start_command=command,
                    )
                )
    return configs


def _safe_worker_fragment(domain_name: str) -> str:
    return "".join(
        char if char.isalnum() else "_"
        for char in domain_name.strip().lower()
    ).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
