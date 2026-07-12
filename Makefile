.PHONY: dev stop restart status logs

dev:
	./scripts/dev.sh start

stop:
	./scripts/dev.sh stop

restart:
	./scripts/dev.sh restart

status:
	./scripts/dev.sh status

logs:
	./scripts/dev.sh logs
fxxk:
	./envfa