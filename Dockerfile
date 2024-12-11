FROM python:3.12-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

WORKDIR /app
COPY requirements.txt /app

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list \
    && apt update  \
    && apt-get install -y gcc libmariadb-dev\
    && apt clean

RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple  \
    && pip install --upgrade pip  \
    && pip install ipython

RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

EXPOSE 8000:8000

CMD python manage.py runserver 0.0.0.0:8000 --settings=settings
