FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

WORKDIR /app
COPY index.html server.py ./
COPY public/og-endpoint-agentic.png public/robots.txt public/llms.txt public/llms-full.txt public/proof.json public/sitemap.xml public/security.txt ./public/

RUN useradd --create-home --uid 10001 portfolio
USER portfolio

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
