FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY v2/frontend/package.json ./
RUN npm install
COPY v2/frontend/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY v2/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY v2/backend/app ./app
COPY halfy_report_template.xlsx ./templates/halfy_report_template.xlsx
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
