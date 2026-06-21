import os
path = r'D:\hermes项目文件夹\工程项目证据链管理系统\backend\evidence_web.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

marker = '@app.route("/api/llm/extract", methods=["POST"])'
idx = content.find(marker)
if idx == -1:
    print('ERROR: marker not found')
    exit(1)

test_llm_code = '''@app.route("/api/settings/test-llm", methods=["POST"])
@login_required
def api_test_llm():
    d = request.get_json() or {}
    api_key = d.get("api_key", "")
    model = d.get("model", "gpt-4o-mini")
    endpoint = d.get("endpoint", "https://api.openai.com/v1")
    if not api_key:
        return jsonify({"ok": False, "error": "请先输入 API Key"}), 400
    if not endpoint:
        return jsonify({"ok": False, "error": "请填写 API 端点"}), 400
    import urllib.request, json as jmod
    url = endpoint.rstrip("/") + "/chat/completions"
    test_messages = [{"role": "user", "content": "你好，请回复OK"}]
    body = jmod.dumps({"model": model, "messages": test_messages, "max_tokens": 10}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = jmod.loads(resp.read())
        if "choices" in result and len(result["choices"]) > 0:
            return jsonify({"ok": True, "message": "连接成功！模型响应正常"})
        else:
            return jsonify({"ok": False, "error": "响应格式异常"}), 500
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        return jsonify({"ok": False, "error": "HTTP " + str(e.code) + ": " + err_body}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


'''

content = content[:idx] + test_llm_code + content[idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: test-llm endpoint added')
