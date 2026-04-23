import openai
from openai import OpenAIError

def call_llm(prompt):

    # 检查提示文本
    if not prompt or not prompt.strip():
        raise ValueError("提示文本不能为空")

    try:
        # 配置 OpenAI 客户端
        client = openai.OpenAI(
            api_key="sk-91e436026cba49baaf8d00a80aaa01d6",
            base_url="https://api.deepseek.com/v1"
        )

        # 发送请求
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 检查响应
        if not response or not response.choices:
            raise ValueError("API 返回空响应")

        # 返回生成的文本
        return response.choices[0].message.content

    except OpenAIError as e:
        # 处理 API 错误
        raise OpenAIError(f"API 调用失败: {str(e)}")
    except Exception as e:
        # 处理其他错误
        raise Exception(f"调用 LLM 时发生错误: {str(e)}")
