# AgentCore Runtime 은 arm64(Graviton) 전용. 빌드는 GitLab Runner / CodeBuild 에서 arm64 로.
FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY handler.py .
# AgentCore Runtime contract — 8080 /invocations
CMD ["python", "handler.py"]
