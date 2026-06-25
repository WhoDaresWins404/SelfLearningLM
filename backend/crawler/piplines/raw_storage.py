import json

from backend.storage.lake import store_blob


class RawStoragePipeline:
    def process_item(self, item, spider):
        url = item.get("url", "")
        domain = item.get("domain", spider.domain)
        html = item.get("body", "")
        status = item.get("status", 200)
        headers = item.get("headers", {})

        store_blob(
            original_url=url,
            domain=domain,
            html_content=html,
            http_status=status,
            headers=headers,
        )
        return item
