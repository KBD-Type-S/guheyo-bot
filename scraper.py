import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def fetch_recent_posts():
    """
    Returns a list of dicts: {'id': str, 'title': str, 'url': str}
    """
    url = "https://api.guheyo.com/graphql"
    query = """
    query FindOfferPreviews($skip: Int!, $take: Int!, $orderBy: FindOfferPreviewsOrderByInput) {
      findOfferPreviews(skip: $skip, take: $take, orderBy: $orderBy) {
        edges {
          node {
            post {
              id
              title
              slug
            }
          }
        }
      }
    }
    """
    variables = {"skip": 0, "take": 20, "orderBy": {"bumpedAt": "desc"}}
    posts = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"query": query, "variables": variables}) as response:
                if response.status == 200:
                    data = await response.json()
                    edges = data.get("data", {}).get("findOfferPreviews", {}).get("edges", [])
                    for edge in edges:
                        post = edge.get("node", {}).get("post")
                        if post:
                            posts.append({
                                'id': post.get('id'),
                                'title': post.get('title'),
                                'url': f"https://guheyo.com/offer/{post.get('slug')}"
                            })
    except Exception as e:
        print(f"Error fetching posts: {e}")
    
    return posts
