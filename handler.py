"""
AgentCore Runtime 1개로 여러 용도 — payload 'type' 으로 라우팅하는 데모.

AgentCore Runtime 은 /invocations 엔드포인트가 1개뿐이고 path 를 추가할 수 없다.
그래서 여러 동작을 한 Runtime 에 담으려면 payload(body) 필드(또는 헤더)로 분기한다.

  type=1 (기본) → agent   : Bedrock Claude 호출 결과 (에이전트 용도)
  type=2        → webpage : HTML 반환 (웹페이지 뿌려주는 용도)
  type=3        → data    : JSON API 응답 (데이터 용도)

배포 후 호출은 boto3 invoke_agent_runtime(payload={"type":2, ...}) 처럼 body 로 전달한다.
"""
from bedrock_agentcore import BedrockAgentCoreApp
import boto3, json, time

app = BedrockAgentCoreApp()
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "us.anthropic.claude-sonnet-4-6-20250929-v1:0"   # cross-region inference 필수


def _log(route, **extra):
    """route 별 구조화 로그 — CloudWatch Logs Insights 에서 type 별 집계가 가능하도록."""
    print(json.dumps({"event": "invoke", "route": route, **extra}, ensure_ascii=False), flush=True)


@app.entrypoint
def invoke(payload, context):
    # 라우팅 키: payload['type'] 우선 → 헤더(x-route-type) → 기본 '1'
    headers = getattr(context, "request_headers", None) or {}
    rtype = str(payload.get("type") or headers.get("x-route-type") or "1")
    t0 = time.time()

    if rtype == "2":
        # 웹페이지 용도 — HTML 문자열 반환
        _log("webpage")
        html = (
            "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            "<title>멀티라우트 데모</title></head>"
            "<body style='font-family:sans-serif;padding:40px'>"
            "<h1>삼성생명 멀티라우트 Runtime</h1>"
            "<p>한 AgentCore Runtime · <code>type=2</code> → 웹페이지(HTML) 용도</p>"
            "</body></html>"
        )
        return {"route": "webpage", "content_type": "text/html", "body": html,
                "latency_ms": int((time.time() - t0) * 1000)}

    if rtype == "3":
        # API 데이터 용도 — JSON
        _log("data")
        return {"route": "data",
                "items": [{"id": 1, "name": "암 진단 특약"}, {"id": 2, "name": "실손 특약"}],
                "latency_ms": int((time.time() - t0) * 1000)}

    # 기본 type=1 — agent 용도 (Bedrock Claude 호출)
    q = payload.get("input", "삼성생명 약관에 대해 한 줄로 소개해줘")
    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": q}]}],
        inferenceConfig={"maxTokens": 512},
    )
    out = resp["output"]["message"]["content"][0]["text"]
    usage = resp.get("usage", {})
    _log("agent", tokens_in=usage.get("inputTokens", 0), tokens_out=usage.get("outputTokens", 0))
    return {"route": "agent", "output": out,
            "tokens_in": usage.get("inputTokens", 0),
            "tokens_out": usage.get("outputTokens", 0),
            "latency_ms": int((time.time() - t0) * 1000)}


app.run()   # 0.0.0.0:8080 /invocations
