from pytrends.request import TrendReq
import requests
import json
from datetime import datetime, timedelta
import urllib.request
import os 
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from fastapi import FastAPI, Request, status, HTTPException

load_dotenv()

#類別
category = 'general'

#語言
lang = 'zh'

#國家
country = 'TW'

#最大結果
max_results = 10

# 计算日期范围
to_date = datetime.now()
from_date = to_date - timedelta(days=30)  # 2个月前

# 转换为 API 要求的日期格式
to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')


#初始化LINE的API
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
apiKey = os.getenv("API_KEY")

app = FastAPI()

# 使用FastAPI创建Webhook回调函数
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request"
        )

    return "OK"

# 处理文字信息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    if event.message.text.lower() == "查詢趨勢":
        trends = fetch_trends()  # 你需要替换为你的实现
        trends_text = "\n".join(trends)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=trends_text)
        )
    elif event.message.text.lower() == "最新新聞":
        news = fetch_news()  # 你需要替换为你的实现
        news_text = "\n".join(news)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=news_text)
        )

def fetch_trends():
  pytrends = TrendReq(hl='zh-TW', tz=360)
  # 获取实时热门搜索
  trending_searches_df = pytrends.trending_searches(pn='taiwan')
  keywords =  trending_searches_df.head()
  # 对每个关键词，获取相关新闻
  trends_list = []  # 用于存储趋势消息
  for keyword in keywords[0]:
    url = f"https://gnews.io/api/v4/search?q={keyword}&token={apiKey}&lang=zh-TW&from={from_date_str}&to={to_date_str}"
    response = requests.get(url)
    news = json.loads(response.text)
    
    #print(news)
    # 检查是否存在 'articles' 键
    if 'articles' not in news:
        #print(f"No articles found for keyword: {keyword}")
        continue


    for article in news['articles']:
        trend_message = f"Title: {article['title']}\nDescription: {article['description']}\nURL: {article['url']}"
        trends_list.append(trend_message)
    print(trends_list)
    return trends_list
  
def fetch_news():
    # 获取热门新闻
    url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang={lang}&country={country}&max={max_results}&apikey={apiKey}"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        articles = data["articles"]
    news_list = []  # 用于存储新闻消息
    for i in range(len(articles)):
        news_message = f"Title: {articles[i]['title']}\nDescription: {articles[i]['description']}\nURL: {articles[i]['url']}"
        news_list.append(news_message)
    
    print(news_list)
    return news_list




