# Note: the C++ sensor daemon reads raw /dev/input devices and requires
# root + host device access, so it is NOT run inside this container — it
# stays on the host (see README). This image runs the Python intelligence
# engine and dashboard, which is the portable, containerizable part.

FROM python:3.11-slim

WORKDIR /app

COPY requirements-dash.txt .
RUN pip install --no-cache-dir -r requirements-dash.txt

COPY . .

RUN mkdir -p temporary models

EXPOSE 8000

CMD ["python", "dashboard.py"]
