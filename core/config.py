from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis配置
    REDIS_HOST: str = "112.124.63.7"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "Redis@123456"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # MySQL配置
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "dcloud_aipan"
    MYSQL_CHARSET: str = "utf8mb4"

    # RabbitMQ配置
    RABBITMQ_HOST: str = "127.0.0.1"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    FILE_INDEX_QUEUE: str = "file.index"


    # MinIO
    MINIO_ENDPOINT: str = "http://127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "ai-pan"
    
    # 应用配置
    APP_NAME: str = "AI智能体中心API服务"
    DEBUG: bool = False
    
    # JWT配置
    JWT_SECRET_KEY: str = "xdclass.net168xdclass.net168xdclass.net168xdclass.net168"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_LOGIN_SUBJECT: str = "XDCLASS"
    
    # LLM配置
    # LLM_MODEL_NAME: str = "qwen-plus"
    LLM_MODEL_NAME: str = "deepseek-r1:8b"
    # LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "sk-005c3c25f6d042848b29d75f2f020f08"
    LLM_TEMPERATURE: float = 0.7
    LLM_STREAMING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()