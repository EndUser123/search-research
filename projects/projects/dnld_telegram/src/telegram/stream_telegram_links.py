import argparse
import asyncio

import asyncpraw  # type: ignore


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream new posts from a subreddit and extract Telegram links."
    )
    parser.add_argument("subreddit", help="The name of the subreddit to stream.")
    args = parser.parse_args()

    reddit = asyncpraw.Reddit(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        user_agent="YOUR_USER_AGENT",
    )

    subreddit = await reddit.subreddit(args.subreddit)
    print(f"Streaming new posts from r/{subreddit.display_name}...")

    async for submission in subreddit.stream.submissions():
        telegram_links = []
        if "t.me/" in submission.url:
            telegram_links.append(submission.url)
        if hasattr(submission, "selftext") and "t.me/" in submission.selftext:
            for word in submission.selftext.split():
                if "t.me/" in word:
                    telegram_links.append(word)

        if telegram_links:
            print(f"\nPost: {submission.title}")
            print(f"URL: https://www.reddit.com{submission.permalink}")
            for link in telegram_links:
                print(f"Found Telegram Link: {link}")


if __name__ == "__main__":
    asyncio.run(main())
