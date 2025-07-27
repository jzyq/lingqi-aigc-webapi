FROM python:3.11-alpine

RUN --mount=type=bind,source=./admin,target=/app \
    pip install -r /app/requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN --mount=type=bind,source=./lib/database,target=/app\
    pip install -r /app/requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY ./admin/*.py /app/
COPY ./lib/database/*.py /aigc-lib/database/

WORKDIR /app
ENV PYTHONPATH=/aigc-lib

CMD ["python", "app.py"]