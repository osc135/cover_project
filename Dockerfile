# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_GOOGLE_MAPS_API_KEY=""
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY
RUN npx vite build

# Stage 2: Backend + serve static frontend
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./static

# Copy LAMC data
COPY backend/data ./data

ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
