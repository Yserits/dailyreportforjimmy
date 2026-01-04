import requests
import os
import json
import time

# apiKEY调用
DEEPSEEK_API_KEY = os.environ.get("LLM_API_KEY")
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")

# DeepSeek 的配置
API_URL = "https://api.deepseek.com/chat/completions"

def get_crypto_news():
    """
    抓取 CoinGecko 的最新新闻
    """
    print("正在抓取 CoinGecko 资讯...")
    url = "https://api.coingecko.com/api/v3/news"
    try:
        # 抓取前 5 条新闻
        response = requests.get(url, timeout=15)
        data = response.json()
        if 'data' in data:
            return data['data'][:5] # 只取前5条
        else:
            return []
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def ai_summarize(news_list):
    """
    调用 DeepSeek
    """
    print("正在请求 AI 进行分析...")
    if not news_list:
        return "⚠️ 今日未获取到新闻数据，请检查网络或源站状态。"

    # 拼成一句话，汇总新闻
    news_text = ""
    for i, news in enumerate(news_list):
        news_text += f"{i+1}. Title: {news.get('title', 'No Title')}\nContent: {news.get('description', 'No Content')}\n\n"

    # Prompt ，决定了输出的风格
    prompt = f"""
    You are a professional crypto market analyst. Here are the latest news snippets:
    
    {news_text}
    
    Please summarize these news items into a daily report for a WeChat message.
    Requirements:
    1. Use a professional but easy-to-read tone.
    2. **Language Style**: Mixed Chinese and English. Translate the main logic into Chinese, but **KEEP professional crypto terms in English** (e.g., Bullish, Bearish, Pump, Dump, ETF, Liquidity, Volatility).
    3. Format:
       - 📅 **Daily Crypto Brief**
       - [Emoji] Title (Chinese with English keywords)
       - Brief summary (1-2 sentences).
    4. At the end, give a "Market Sentiment" score (0-10) and a one-sentence comment.
    
    Output the result directly in plain text (Markdown is supported).
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    try:
        # 发送请求给 DeepSeek
        response = requests.post(API_URL, headers=headers, json=payload)
        response_json = response.json()
        
        # 获取 AI 回复的内容
        content = response_json['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"AI 分析失败: {e}")
        return f"AI 接口报错: {str(e)}"

def send_to_wechat(content):
    """
    推送到微信 (PushPlus)
    """
    print("正在推送至微信...")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "今日币圈早报 (AI版)",
        "content": content,
        "template": "markdown" # 使用 markdown 格式，排版更漂亮
    }
    
    try:
        resp = requests.post(url, json=data)
        print("推送结果:", resp.text)
    except Exception as e:
        print(f"推送失败: {e}")

if __name__ == "__main__":
    # 1. 抓新闻
    news = get_crypto_news()
    
    # 2. AI 处理
    if news:
        report = ai_summarize(news)
    else:
        report = "今日无法获取新闻，请检查代码或源站。"
    
    # 3. 发微信
    # 只有当两个 key 都有值的时候才发送，防止报错
    if DEEPSEEK_API_KEY and PUSHPLUS_TOKEN:
        send_to_wechat(report)
    else:
        print("请检查 GitHub Secrets 是否配置了 LLM_API_KEY 和 PUSHPLUS_TOKEN")
