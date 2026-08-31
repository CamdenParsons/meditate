"""Linear ids, read off the work rather than from Linear."""
import re

# Case-insensitive: ids appear upper-case in PR titles but lower-case in
# branch names (acme-482-webhook-retries).
PATTERN = re.compile(r"\b([A-Za-z]{2,5})-(\d{1,6})\b")
NOT_TICKETS = {"UTF", "SHA", "GPT", "ISO", "RFC", "IPV", "MD", "PY", "JS", "TS"}


def ids_in(text):
    out = set()
    for word, num in PATTERN.findall(text or ""):
        if word.upper() not in NOT_TICKETS:
            out.add(f"{word.upper()}-{num}")
    return out


class Provider:
    name = "tickets"

    def collect(self, window, found):
        """Scan what the other providers found.

        Every id you touch tends to land in a PR title, a commit subject
        or a branch name, so this needs no Linear API key and no extra
        network call. It runs last, on their output.
        """
        gh = found.get("github", {})
        seen = set()
        for key in ("prs", "issues", "reviews"):
            for item in gh.get(key, []):
                seen |= ids_in(item.get("title"))
        for push in gh.get("pushes", []):
            seen |= ids_in(push.get("ref"))
            for msg in push.get("commits", []):
                seen |= ids_in(msg)
        for br in gh.get("branches", []):
            seen |= ids_in(br.get("ref"))
        for c in found.get("commits", []):
            seen |= ids_in(c.get("subject"))
        for s in found.get("claude", []):
            seen |= ids_in(s.get("branch"))
        # anything the linear provider named in full is already reported
        # there, with a title and a status
        seen -= {i.get("id") for i in found.get("linear", [])}
        return sorted(seen)
