FROM python:3.12-slim
ARG VCS_REF=unknown
LABEL org.opencontainers.image.revision=$VCS_REF
WORKDIR /gestionale_eventi
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt
COPY app.py models.py routes.py permissions.py money.py entrypoint.sh ./
COPY templates ./templates
COPY static ./static
COPY migrations ./migrations
RUN chmod +x entrypoint.sh && useradd --uid 10001 --create-home app && chown app:app /gestionale_eventi
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
ENTRYPOINT ["./entrypoint.sh"]
