"""Linear issues you touched during the window.

The only provider that needs a credential. Set LINEAR_API_KEY to a Linear
personal API key (Linear > Settings > Security & access > Personal API
keys). Without it this returns nothing, like any other provider that
cannot answer.

It exists because issue work leaves no trace anywhere else: moving four
issues to Cancelled in the Linear UI touches no branch, no commit and no
pull request, so the tickets provider - which reads ids off the work -
cannot see it at all.
"""
import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"
TIMEOUT = 15
LIMIT = 50

QUERY = """
query($from: DateTimeOrDuration!, $to: DateTimeOrDuration!, $limit: Int!) {
  issues(
    first: $limit
    orderBy: updatedAt
    filter: {
      updatedAt: { gt: $from, lt: $to }
      or: [
        { assignee: { isMe: { eq: true } } }
        { creator:  { isMe: { eq: true } } }
      ]
    }
  ) {
    nodes {
      identifier
      title
      url
      updatedAt
      state { name }
    }
  }
}
"""


def _post(payload, key):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": key},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


class Provider:
    name = "linear"

    def __init__(self, post=None):
        self._post = post or _post

    def collect(self, window, found):
        key = os.environ.get("LINEAR_API_KEY")
        if not key:
            return []
        start, end = window
        payload = {"query": QUERY,
                   "variables": {"from": start.isoformat(),
                                 "to": end.isoformat(),
                                 "limit": LIMIT}}
        try:
            data = self._post(payload, key)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            return []
        nodes = (((data or {}).get("data") or {}).get("issues") or {}).get("nodes") or []
        return [{"id": n.get("identifier"), "title": n.get("title"),
                 "url": n.get("url"),
                 "status": (n.get("state") or {}).get("name")}
                for n in nodes if n.get("identifier")]
