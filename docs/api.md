# 在线刷题平台 API 文档

本文档介绍后端可用的 RESTful 接口。所有接口以 `http://<host>:8000` 为默认 Base URL，具体以部署环境为准。

## 鉴权

- JWT 认证，`/users/login` 成功后返回 `data` 字段即为 Token。
- 需要登录的接口在请求头添加 `Authorization: Bearer <token>`。
- 管理员接口需使用用户名 `admin` 登录获取的 Token。

## 用户模块

### 注册新用户

- `POST /users/register`
- 请求体：`{ "name": "student", "password": "123456" }`
- 响应：`Result[UserRead]`，包含用户信息。

### 登录获取 Token

- `POST /users/login`
- 请求体：`{ "name": "student", "password": "123456" }`
- 响应：`Result[str]`，`data` 字段为 JWT Token。

### 批量导入学生（管理员）

- `POST /users/import`
- Content-Type：`multipart/form-data`
- 表单字段：`file`，CSV 文件需包含 `name,password` 列。
- 响应：成功返回导入用户列表，失败返回错误信息。

## 题目模块

### 获取题目详情

- `GET /problems/{problem_id}`
- 响应：`Result[ProblemRead]`

### 分页查询题目

- `GET /problems/?page=1&page_size=20&problem_type=choice&name=算法`
- 响应：`Result[ProblemPage]`，`items` 为题目列表，附带总数。

### 筛选（类型或名称）

- 可通过 `problem_type` 或 `name` 参数单独查询。

### 创建题目（管理员）

- `POST /problems/create`
- 请求体（部分字段按题型可选）：

```json
{
  "title": "两数之和",
  "type": "coding",
  "description": "使用 Markdown 描述题目",
  "code_id": 1234,
  "options": ["A", "B"],
  "answer": "A"
}
```

- 当 `type` 为 `coding` 时必须提供 `code_id`；`choice` 题需提供 `options`。
- 提交 `coding` 题目时会实时校验 HOJ 是否存在该 `code_id`，若不存在将返回错误，避免引用无效题号。
- 响应：`Result[ProblemRead]`

### 批量导入题目（管理员）

- `POST /problems/import?fmt=auto`
- 请求为 `multipart/form-data`，字段 `file` 为需上传的 JSON / YAML 文本（默认自动识别）。
- 响应：`Result[List[ProblemRead]]`，返回所有成功导入的题目。
- 文件限制：默认大小 2MB，可通过环境变量 `PROBLEM_IMPORT_MAX_BYTES` 调整。
- 编程题的 `code_id` 会逐个校验 HOJ 是否存在，若失败会跳过并给出提示。

#### JSON 示例

```json
[
  {
    "title": "二分查找",
    "type": "choice",
    "description": "二分查找的时间复杂度是？",
    "options": ["O(logN)", "O(N)", "O(NlogN)"],
    "answer": "O(logN)",
    "solution": "每轮将区间一分为二。"
  },
  {
    "title": "两数之和",
    "type": "coding",
    "description": "返回数组中两数之和等于 target 的索引。",
    "code_id": 1001
  }
]
```

#### 文本（YAML）示例

```yaml
- title: 快速排序
  type: fill
  description: "快速排序的平均时间复杂度是 ______。"
  answer: O(N log N)
- title: 求最大值
  type: coding
  description: "实现一个函数，返回数组的最大值。"
  code_id: 1002
```

> `fmt` 参数可指定 `json` 或 `text`，默认 `auto`。文本模式使用 YAML 语法，普通 `.txt` 文件亦可。

## 题集模块

### 分页获取题集

- `GET /problem-sets/?page=1&page_size=20`
- 响应：`Result[ProblemSetPage]`

### 获取题集详情

- `GET /problem-sets/{problem_set_id}`
- 响应：`Result[ProblemSetStatus]`，包含题目 ID 与已完成用户。

### 创建题集（管理员）

- `POST /problem-sets/`
- 请求体：

```json
{
  "title": "入门题单",
  "description": "10 道基础题",
  "problem_ids": [1, 2, 3]
}
```

- 响应：`Result[ProblemSetStatus]`

### 标记题集完成 / 取消

- `POST /problem-sets/{problem_set_id}/completion`
- `DELETE /problem-sets/{problem_set_id}/completion`
- 需要登录（普通用户）。

## 提交模块

### 提交题目答案

- `POST /submissions/submit`
- 请求体：`{ "problem_id": 1, "user_answer": "A" }`
- 用户需登录。
- 编程题会自动提交到 HOJ 判题。

### 查询当前用户在某题的提交

- `GET /submissions/user/{problem_id}`
- 响应：`Result[List[Submission]]`

### 查询当前用户所有提交

- `GET /submissions/user`
- 响应：`Result[List[Submission]]`

### 根据提交 ID 查看详情

- `GET /submissions/{submission_id}`
- 仅限提交者或管理员访问。

## 管理员接口

### 获取 / 更新系统配置

- `GET /admin/config`
- `PUT /admin/config`
- 请求体示例：

```json
{
  "database_url": "mysql+pymysql://root:pwd@db:3306/PyClass",
  "hoj_base_url": "https://hoj.local",
  "hoj_username": "admin",
  "hoj_password": "secret"
}
```

- 更新数据库地址会立即重新建立连接，建议重启服务以确保模型同步。

### 分页查看所有提交

- `GET /admin/submissions?page=1&page_size=50`
- 响应：`Result[SubmissionPage]`

### 查看指定学生的全部提交

- `GET /admin/users/{user_id}/submissions`
- 响应：`Result[List[SubmissionRead]]`

## 响应格式

所有接口统一返回结构：

```json
{
  "code": 200,
  "message": "成功",
  "data": { ... }
}
```

- `code`：业务状态码，200 表示成功。
- `message`：提示信息。
- `data`：实际数据，可为对象、数组或分页结构。

错误示例：

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

## 文件上传说明

- 批量导入学生接口需使用 multipart/form-data。
- 单个 CSV 文件默认限制为 1MB、1000 行，可通过环境变量 `USER_IMPORT_MAX_BYTES`、`USER_IMPORT_MAX_ROWS` 调整。

## 配置说明

- **数据库地址**：支持通过管理员接口更新，同时写入运行环境。
- **HOJ 配置**：`base_url`、`username`、`password` 更新后立即生效，后续判题请求自动使用新配置。

如需更多信息或新增接口，请联系后端开发维护。 
