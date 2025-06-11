.PHONY: format format-backend format-frontend lint

# 格式化所有程式碼
format: format-backend format-frontend

# 後端格式化
format-backend:
	cd backend && ruff check . --fix && ruff format .

# 前端格式化
format-frontend:
	cd frontend && npm run format && npm run lint

# 檢查但不修改
lint:
	cd backend && ruff check .
	cd frontend && npm run format:check && npm run lint:check