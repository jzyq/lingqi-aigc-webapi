FROM python:3.11-alpine

COPY ./web/ /app/
COPY ./lib/database/ /lib/python/database/

RUN pip install -r /app/requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple \
    && pip install -r /lib/python/database/requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple \
    && pip cache purge

ENV PYTHONPATH=/lib/python
WORKDIR /app

CMD ["python", "app.py"]