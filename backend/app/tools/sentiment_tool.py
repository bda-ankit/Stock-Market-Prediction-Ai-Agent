from textblob import TextBlob


def sentiment_tool(
    news_text: str
):

    if not news_text.strip():
        return {
            "score": 0,
            "classification": "Neutral",
            "summary": "No news provided."
        }

    polarity = TextBlob(
        news_text
    ).sentiment.polarity

    score = round(
        polarity * 100,
        2
    )

    if polarity > 0.25:
        label = "Bullish"

    elif polarity < -0.25:
        label = "Bearish"

    else:
        label = "Neutral"

    return {
        "score": score,
        "classification": label,
        "summary": news_text[:500]
    }