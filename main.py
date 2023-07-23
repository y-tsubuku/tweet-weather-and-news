import openai
import requests
import tweepy
import os
from dotenv import load_dotenv
import asyncio


# 実行前に下記の項目を .env に記載する
# NEWS_API_KEY=
# OPENAI_ORGANIZATION=
# OPENAI_API_KEY=
# TWITTER_CONSUMER_KEY=
# TWITTER_CONSUMER_SECRET=
# TWITTER_ACCESS_TOKEN=
# TWITTER_ACCESS_TOKEN_SECRET=

# 天気を取得する
async def fetch_weather():
    meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=35.6895&longitude=139.6917&daily=temperature_2m_max," \
                "temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise," \
                "sunset&timezone=Asia%2FTokyo"
    return requests.get(meteo_url).json()


# ニュースを取得する
async def fetch_news():
    news_api_key = os.environ.get("NEWS_API_KEY")
    news_api_url = "https://newsapi.org/v2/top-headlines?country=jp&category=business&pageSize=3&apiKey=" + news_api_key
    return requests.get(news_api_url).json()


# プロンプトを実行する
def execute_prompt(prompt):
    openai.organization = os.environ.get("OPENAI_ORGANIZATION")
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]


def create_prompt(temp_max, temp_min, news_title):
    return """
    下記の情報とルールからtwitterに投稿する文章を考えて下さい。
    
    【情報】
    ・今日の東京は最高気温「{}℃」、最低気温「{}℃」である
    ・直近のビジネスニュースは下記である
    {}
    
    【ルール】
    ・投稿は必ず140文字以内に収めること
    ・ポジティブな形で伝えること
    ・アナウンサーが読むような形で伝えること
    ・ですます調で伝えること
    ・ニュースの内容は重要なものだけ取り上げて、不要と判断した場合は投稿に含めなくて良い
    ・文章の先頭と末尾に " や 「」 などの記号は入れないこと
    ・気温に関して、暑いか寒いなどの表現を入れること
    ・ツイートの文章以外は、文章の中に入れないこと
    """.format(
        temp_max,
        temp_min,
        news_title,
    )


# 4. ツイートする
def tweet(text):
    consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
    consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    client.create_tweet(text=text)


async def main():
    # 0. 環境変数を読み込む
    load_dotenv()

    # 1. 天気とニュースを非同期で取得する
    [weather, news] = await asyncio.gather(fetch_weather(), fetch_news())
    # 2. ツイートの文章を生成するプロンプトを作成する
    prompt = create_prompt(
        weather["daily"]["temperature_2m_max"][0],
        weather["daily"]["temperature_2m_min"][0],
        news["articles"][0]["title"],
    )
    # 3. chatgptでプロンプトから文章を生成する
    text = execute_prompt(prompt)
    # 4. ツイートする（chatgptが140文字以内に収めないケースがあるため、念のため切り捨てる）
    tweet(text[0:140])


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.close()
