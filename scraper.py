import asyncio
import re
import aiohttp


async def fetch_recent_posts():
    """
    Returns a list of dicts: {'id': str, 'title': str, 'url': str, 'content': str}
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
    variables = {"skip": 0, "take": 12, "orderBy": {"bumpedAt": "desc"}}
    posts = []
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"query": query, "variables": variables}) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    graphql_data = data.get("data")
                    if not graphql_data:
                        print(f"Error: {data.get('errors')}")
                        return posts
                    
                    edges = graphql_data.get("findOfferPreviews", {}).get("edges", [])
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


async def fetch_post_content(url: str) -> str:
    """
    Fetches the HTML of the post page and extracts the meta description
    using regex only (no bs4 dependency).
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status == 200:
                    html = await res.text()

                    # 1) HTML meta 태그에서 description 추출
                    match = re.search(
                        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
                        html, re.IGNORECASE,
                    )
                    if match:
                        return match.group(1)

                    # 2) Next.js JSON 데이터에서 description 추출
                    match = re.search(
                        r'"name"\s*:\s*"description"\s*,\s*"content"\s*:\s*"(.*?)"',
                        html, re.IGNORECASE,
                    )
                    if match:
                        try:
                            return match.group(1).encode('utf-8').decode('unicode_escape')
                        except Exception:
                            return match.group(1)
    except Exception as e:
        print(f"Error fetching content for {url}: {e}")
    return ''
