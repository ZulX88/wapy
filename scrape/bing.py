import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

def get_bing_images(query: str, limit: int = 1) -> dict:
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    q = '+'.join(query.strip().split())
    url = f"https://www.bing.com/images/search?q={q}&FORM=HDRSC2"

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {"error": f"Failed to fetch from Bing (status {res.status_code})"}

    soup = BeautifulSoup(res.text, "html.parser")
    results = []

    for a in soup.find_all("a", class_="iusc"):
        try:
            m = json.loads(a.get("m", "{}"))
            mad = json.loads(a.get("mad", "{}"))

            murl = m.get("murl")
            turl = mad.get("turl")
            if not murl:
                continue

            image_name = urllib.parse.urlsplit(murl).path.split("/")[-1]

            results.append({
                "image_name": image_name,
                "preview_url": turl,
                "original_url": murl
            })

            if len(results) >= limit:
                break

        except Exception:
            continue

    return {
        "query": query,
        "count": len(results),
        "results": results
    }
