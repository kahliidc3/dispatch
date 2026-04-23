from apps.workers.celery_app import celery_app


def main() -> None:
    celery_app.start(argv=["celery", "beat", "-l", "info"])


if __name__ == "__main__":
    main()
