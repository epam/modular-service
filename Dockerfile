FROM public.ecr.aws/docker/library/python:3.10-slim as compile-image

ARG MODULAR_SERVICE_PATH=.

COPY $MODULAR_SERVICE_PATH/src/requirements.txt /src/requirements.txt
COPY $MODULAR_SERVICE_PATH/src/lambdas/modular_api_handler/requirements.txt /src/lambdas/modular_api_handler/requirements.txt
RUN pip install --user -r /src/requirements.txt

COPY $MODULAR_SERVICE_PATH/src/commons /src/commons
COPY $MODULAR_SERVICE_PATH/src/lambdas /src/lambdas
COPY $MODULAR_SERVICE_PATH/src/models /src/models
COPY $MODULAR_SERVICE_PATH/src/onprem /src/onprem
COPY $MODULAR_SERVICE_PATH/src/services /src/services
COPY $MODULAR_SERVICE_PATH/src/validators /src/validators
COPY $MODULAR_SERVICE_PATH/src/main.py $MODULAR_SERVICE_PATH/src/entrypoint.sh /src/

# can be removed
RUN rm -rf $(find /root/.local/lib -name "*.dist-info") && rm -rf $(find /root/.local/lib/ -name "__pycache__")

FROM public.ecr.aws/docker/library/python:3.10-slim AS build-image

RUN apt-get update && apt-get install -y wget && apt-get clean  # for compose health check

COPY --from=compile-image /root/.local /root/.local
COPY --from=compile-image /src /src


ENV AWS_REGION=us-east-1 \
    MODULAR_SERVICE_MODE=docker \
    PATH=/root/.local/bin:$PATH \
    modular_service_mode=docker

WORKDIR /src
EXPOSE 8040
RUN chmod +x entrypoint.sh main.py
ENTRYPOINT ["./entrypoint.sh"]
