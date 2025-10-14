# Wine-Pick-QR • Demo (HTML5 + FastAPI + Postgres)

Demo listo para desplegar con **Neon (Postgres)**, **Render (FastAPI)** y **Vercel (frontend estático)**.

## Estructura
```
backend/
  main.py
  requirements.txt
frontend/
  index.html
  product.html
  styles.css
  script.js
sql/
  001_init.sql
  002_sample_data.sql
vercel.json
```

## Variables de entorno
- `DATABASE_URL` → cadena de conexión de Neon con SSL requerido (async):  
  `postgresql+asyncpg://USER:PASSWORD@HOST/DB?ssl=require`
- `ADMIN_TOKEN` (opcional) → habilita creación simple de productos.
- `FRONTEND_ORIGIN` (opcional) → dominio del frontend para CORS (ej. https://tu-frontend.vercel.app).

## Deploy
### 1) Neon (DB)
1. Crear proyecto y DB.
2. Tomar la connection string y convertirla al formato async con `?ssl=require`.
3. Ejecutar en el editor SQL: `sql/001_init.sql` y luego `sql/002_sample_data.sql`.

### 2) Render (API)
1. Nuevo **Web Service** (Python).
2. Build Command: `pip install -r backend/requirements.txt`
3. Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Variables: `DATABASE_URL`, opcionales `FRONTEND_ORIGIN`, `ADMIN_TOKEN`.
5. Probar `GET /health` y `/docs`.

### 3) Vercel (frontend)
1. Importar el repo y usar carpeta `frontend/` como salida estática.
2. Editar `vercel.json` en la raíz reemplazando la URL del backend de Render.
3. Deploy y probar `/` y `/product.html?pid=G7AKJ3H9XY1`.

## Endpoints
- `GET /api/products?q=malbec`
- `GET /api/products/{pid}`
- `POST /api/admin/products` con header `X-Admin-Token: <ADMIN_TOKEN>`

## Notas
- No se usa `starlette.middleware.proxy_headers` (evita el error de import).
- Promos soportadas: `percent` y `two_for`, con ventana de vigencia.
- Este repo es educativo; ajustá validaciones y auth según tu caso.

— Generado el 2025-10-14 22:51:28
