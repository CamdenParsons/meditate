"""Everything your GitHub account did during the window."""
import json

from ._util import parse_time, run

TIMEOUT = 20
PAGES = 3          # 100 events a page; a Session rarely spans more


class Provider:
    name = "github"

    def collect(self, window, found):
        """Read the user events feed.

        Not the contributions API: that reports zero for private
        repositories unless the profile opts in, while the events feed
        carries private activity in full. The feed keeps roughly the last
        300 events, which is ample for one Session but means this cannot
        backfill history.
        """
        start, end = window
        login = _login()
        if not login:
            return {}

        events = []
        for page in range(1, PAGES + 1):
            out = run(["gh", "api",
                       f"/users/{login}/events?per_page=100&page={page}"], TIMEOUT)
            if not out:
                break
            try:
                batch = json.loads(out)
            except json.JSONDecodeError:
                break
            if not batch:
                break
            events.extend(batch)
            oldest = parse_time(batch[-1].get("created_at"))
            if oldest and oldest < start:          # walked past the window
                break

        buckets = {"pushes": [], "prs": [], "issues": [],
                   "reviews": [], "branches": []}
        for e in events:
            t = parse_time(e.get("created_at"))
            if not (t and start <= t <= end):
                continue
            _sort_event(e, buckets)
        return {k: v for k, v in buckets.items() if v}


def _login():
    out = run(["gh", "api", "user", "--jq", ".login"], TIMEOUT)
    return out.strip() if out else None


def _sort_event(e, b):
    repo = (e.get("repo") or {}).get("name", "?")
    p = e.get("payload") or {}
    kind = e.get("type")
    if kind == "PushEvent":
        # Private repositories omit the commit list from the feed - only
        # before/head/ref survive - so subjects come from the git provider.
        b["pushes"].append({
            "repo": repo,
            "ref": (p.get("ref") or "").replace("refs/heads/", ""),
            "commits": [c.get("message", "").split("\n")[0]
                        for c in p.get("commits") or []],
        })
    elif kind == "PullRequestEvent":
        pr = p.get("pull_request") or {}
        b["prs"].append({"repo": repo, "action": p.get("action"),
                         "number": pr.get("number"), "title": pr.get("title"),
                         "url": pr.get("html_url")})
    elif kind in ("IssueCommentEvent", "IssuesEvent"):
        iss = p.get("issue") or {}
        b["issues"].append({"repo": repo, "number": iss.get("number"),
                            "title": iss.get("title"), "url": iss.get("html_url")})
    elif kind in ("PullRequestReviewEvent", "PullRequestReviewCommentEvent"):
        pr = p.get("pull_request") or {}
        b["reviews"].append({"repo": repo, "number": pr.get("number"),
                             "title": pr.get("title")})
    elif kind == "CreateEvent" and p.get("ref_type") == "branch":
        b["branches"].append({"repo": repo, "ref": p.get("ref")})
