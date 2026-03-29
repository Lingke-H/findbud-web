"""
独立 AI 连通性测试脚本
运行方式（在 backend 目录下）：
    python test_ai.py
"""

import asyncio
import os
import json
import time

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[env] .env 已加载")
except ImportError:
    print("[env] python-dotenv 未安装，跳过 .env 加载（依赖系统环境变量）")

import openai


async def test_ai():
    api_key    = os.getenv("AI_API_KEY", "")
    api_base   = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("AI_MODEL_NAME", "gpt-4o")

    print(f"\n{'='*50}")
    print(f"  AI_API_KEY    : {'已设置 (' + api_key[:6] + '...)' if api_key else '❌ 未设置'}")
    print(f"  AI_API_BASE_URL: {api_base}")
    print(f"  AI_MODEL_NAME  : {model_name}")
    print(f"{'='*50}\n")

    if not api_key:
        print("❌ AI_API_KEY 未配置，请检查 .env 文件")
        return

    prompt = """为「数学建模」竞赛生成 1 道单选题：
  1. skill_modeling：数学建模能力

规则：题目≤20字，选项≤12字，禁止出现维度名称，选项A最强→D最弱

只返回JSON，无多余文字：
{"questions":[{"id":"q_1","dimension":"skill_modeling","text":"题目","options":[{"option_id":"A","text":"选项A"},{"option_id":"B","text":"选项B"},{"option_id":"C","text":"选项C"},{"option_id":"D","text":"选项D"}]}]}"""

    print(">>> 正在调用 AI API...")
    t0 = time.time()

    try:
        client = openai.AsyncOpenAI(api_key=api_key, base_url=api_base)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=300,
            ),
            timeout=30.0,
        )
        elapsed = round(time.time() - t0, 2)
        raw = response.choices[0].message.content or "{}"

        print(f"✅ API 响应成功！耗时 {elapsed}s，tokens={response.usage.total_tokens if response.usage else '?'}")
        print(f"\n原始响应：\n{raw}\n")

        parsed = json.loads(raw)
        questions = parsed.get("questions", [])
        if questions:
            q = questions[0]
            print(f"题目：{q.get('text')}")
            for opt in q.get("options", []):
                print(f"  {opt['option_id']}. {opt['text']}")
        else:
            print("⚠️  响应成功但 questions 列表为空")

    except asyncio.TimeoutError:
        print(f"❌ 超时（30s），API 没有响应")
    except openai.AuthenticationError as e:
        print(f"❌ 认证失败（API Key 无效）: {e}")
    except openai.APIConnectionError as e:
        print(f"❌ 网络连接失败（检查 base_url 或代理）: {e}")
    except openai.APIStatusError as e:
        print(f"❌ API 返回错误状态 {e.status_code}: {e.message}")
    except Exception as e:
        print(f"❌ 未知错误: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_ai())
