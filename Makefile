.PHONY: run
run:
	uvicorn src.petbot.interface.api.v1.router:app --reload
