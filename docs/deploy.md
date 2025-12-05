# 部署指南

## 构建后端镜像

```bash
docker build -t hoj-python-backend .
```

## 直接运行容器（连接 HOJ 网络）

```bash
docker run \
  --name hoj-python-backend \
  --rm \
  --env DATABASE_URL="mysql+pymysql://root:hoj123456@hoj-mysql:3306/PyClass" \
  --env BACKEND_PORT=8000 \
  --network hoj-network \
  -p 8000:8000 \
  hoj-python-backend
```

## docker-compose 集成示例

在 HOJ 的 `docker-compose.yml` 中加入：

```yaml
  hoj-python-backend:
    build:
      context: ../Python-Course
    image: hoj-python-backend:latest
    container_name: hoj-python-backend
    restart: always
    depends_on:
      hoj-mysql:
        condition: service_healthy
    environment:
      - DATABASE_URL=${DATABASE_URL:-mysql+pymysql://root:hoj123456@hoj-mysql:3306/PyClass}
      - BACKEND_PORT=${BACKEND_PORT:-8000}
    ports:
      - "8000:8000"
    networks:
      hoj-network:
        ipv4_address: ${PY_BACKEND_HOST:-172.20.0.9}
```

> `context` 需指向当前 FastAPI 项目目录。`ipv4_address` 需要位于 `SUBNET` 配置范围内，并保证不与其他容器冲突。
