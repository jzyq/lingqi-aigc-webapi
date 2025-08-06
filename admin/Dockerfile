FROM python:3.11-alpine

COPY ./admin /app
COPY ./lib/ /lib/python/

RUN pip install -r /app/requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple && \
    pip cache purge

WORKDIR /app
ENV PYTHONPATH=/lib/python/

CMD ["python", "app.py"]