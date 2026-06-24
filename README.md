# aah-multiroute-runtime

AgentCore Runtime **1개**로 여러 용도를 처리하는 데모. Runtime 은 `/invocations` 엔드포인트가
하나뿐이고 path 를 추가할 수 없으므로, **payload(body) 필드 `type` (또는 헤더 `x-route-type`)**
으로 핸들러가 분기한다.

| type | route | 동작 |
|---|---|---|
| `1` (기본) | agent   | Bedrock Claude 호출 결과 (에이전트 용도) |
| `2` | webpage | HTML 반환 (웹페이지 뿌려주는 용도) |
| `3` | data    | JSON API 응답 (데이터 용도) |

## 호출 (배포 후)
```python
import boto3, json
c = boto3.client("bedrock-agentcore", region_name="us-east-1")
def call(t, **kw):
    r = c.invoke_agent_runtime(
        agentRuntimeArn=ARN, contentType="application/json", accept="application/json",
        runtimeSessionId="demo-session-0000000000000000000000000000000000",
        payload=json.dumps({"type": t, **kw}).encode())
    return json.loads(r["response"].read())
call(1, input="암보험 보장 한 줄 요약")   # agent
call(2)                                  # webpage(HTML)
call(3)                                  # data(JSON)
```

## Observability
한 Runtime 의 모든 호출은 동일 Runtime 메트릭(호출 수·지연·에러)에 집계된다. type 별 분리는
핸들러가 찍는 구조화 로그(`{"event":"invoke","route":...}`)를 **CloudWatch Logs Insights** 로
집계한다:
```
fields route | stats count() by route
```
