import requests
import os
import xml.etree.ElementTree as ET # 引入这个自带工具来解析 RSS
import time

# 读取配置
DEEPSEEK_API_KEY = os.environ.get("LLM_API_KEY")
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN")

# DeepSeek 配置
API_URL = "https://api.deepseek.com/chat/completions"

def get_crypto_news():
    """
    [修改版] 抓取 Cointelegraph 的 RSS 订阅源
    RSS 相比 API 更稳定，不容易被屏蔽
    """
    print("正在抓取 Cointelegraph 新闻...")
    url = "https://cointelegraph.com/rss"
    
    # 伪装成普通浏览器，防止被拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        # 解析 XML 数据
        root = ET.fromstring(response.content)
        
        news_list = []
        # 查找所有的 item 标签 (每一条新闻)
        # 我们只取前 5 条
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text
            #有些 RSS 的描述里带 HTML 标签，我们简单清洗一下（如果需要）
            description = item.find('description').text
            if description:
                # 简单去除 HTML 标签的粗暴方法，或者直接发给 AI 让 AI 去洗
                pass 
            
            news_list.append({
                'title': title, 
                'description': description
            })
            
        print(f"成功获取 {len(news_list)} 条新闻")
        return news_list

    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def ai_summarize(news_list):
    """
    调用 DeepSeek 进行总结和翻译
    """
    print("正在请求 AI 进行分析...")
    if not news_list:
        return "⚠️ 今日未获取到新闻数据 (RSS源为空)。"

    # 拼接新闻
    news_text = ""
    for i, news in enumerate(news_list):
        # 只取前200个字符避免太长费钱
        desc_preview = news.get('description', '')[:200] 
        news_text += f"{i+1}. {news.get('title')}\nDesc: {desc_preview}...\n\n"

    prompt = f"""
    You are a crypto analyst. Summarize these 5 news items for a WeChat daily report.
    
    Data:
    {news_text}
    
    Requirements:
    1. **Format**: Mixed Chinese and English.
    2. **Translate** the summary to Chinese, but **KEEP** professional terms in English (e.g. Bullish, ETF, Liquidity).
    3. Output Format (Markdown):
       - 📅 **Crypto Daily**
       - [Emoji] **Title** (Chinese)
       - Summary (1 sentence)
    4. End with a "Market Sentiment" score (0-10).
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response_json = response.json()
        
        # 检查有没有报错
        if 'error' in response_json:
            print(f"DeepSeek API 报错: {response_json['error']}")
            return f"AI 罢工了: {response_json['error']['message']}"
            
        content = response_json['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"AI 请求异常: {e}")
        return f"AI 连接失败: {str(e)}"

def send_to_wechat(content):
    """
    推送到微信
    """
    print("正在推送至微信...")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "今日币圈早报 (CoinTelegraph版)",
        "content": content,
        "template": "markdown"
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
    # 如果 DeepSeek 没钱了，这里会报错，但我们至少先看看能不能抓到新闻
    if news:
        # 如果你确定 DeepSeek 有额度，就用这一行：
        report = ai_summarize(news)
        
        # 【备用方案】如果 AI 还是坏的，把上面那行注释掉，用下面这行直接发英文：
        # report = "今日新闻 (AI 暂不可用):\n\n" + "\n".join([n['title'] for n in news])
    else:
        report = "⚠️ 无法获取新闻，CoinTelegraph 可能也屏蔽了 IP。"
    
    # 3. 发微信
    if PUSHPLUS_TOKEN:
        send_to_wechat(report)
    else:
        print("缺少 PUSHPLUS_TOKEN")
