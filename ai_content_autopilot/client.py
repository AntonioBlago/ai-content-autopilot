"""
Pull API client for the Visibly Content Autopilot.

Fetches articles, lists articles, and confirms publication.
Depends on: requests
"""

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class VisiblyClient:
    """
    Client for the Visibly Content Autopilot Pull API.

    Fetches articles, lists articles, and confirms publication.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = 'https://www.antonioblago.com/content-autopilot',
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'ai-content-autopilot/1.0',
        }

    def fetch_article(self, article_id: int, include_markdown: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a single article by ID.

        Args:
            article_id: Article ID
            include_markdown: Include content_markdown field

        Returns:
            Article dict or None on error
        """
        url = f"{self.base_url}/api/v1/articles/{article_id}"
        params = {}
        if include_markdown:
            params['include_markdown'] = 'true'

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('article')
            logger.warning(f"fetch_article {article_id}: HTTP {resp.status_code}")
            return None
        except Exception as e:
            logger.error(f"fetch_article error: {e}")
            return None

    def list_articles(
        self,
        status: Optional[str] = 'approved',
        project_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List articles with optional filters.

        Args:
            status: Filter by status (e.g. 'approved', 'published')
            project_id: Filter by project
            limit: Max results (1-100)
            offset: Pagination offset

        Returns:
            List of article dicts
        """
        url = f"{self.base_url}/api/v1/articles"
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        if project_id:
            params['project_id'] = project_id

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('articles', [])
            logger.warning(f"list_articles: HTTP {resp.status_code}")
            return []
        except Exception as e:
            logger.error(f"list_articles error: {e}")
            return []

    def confirm_published(self, article_id: int, published_url: str) -> bool:
        """
        Confirm that an article was published externally.

        Args:
            article_id: Article ID
            published_url: Public URL where the article was published

        Returns:
            True if confirmation was accepted
        """
        url = f"{self.base_url}/api/v1/articles/{article_id}/confirm"
        body = {'published_url': published_url}

        try:
            resp = requests.post(
                url, headers=self._headers(), json=body, timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('success', False)
            logger.warning(f"confirm_published {article_id}: HTTP {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"confirm_published error: {e}")
            return False