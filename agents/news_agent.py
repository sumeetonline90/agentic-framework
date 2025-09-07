"""
News Aggregation Agent

Handles news retrieval, aggregation, and categorization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.base_agent import BaseAgent
from core.message_bus import Message
from core.context_manager import ContextScope
from config.agent_config import AgentType


class NewsCategory(Enum):
    POLITICS = "politics"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    SCIENCE = "science"
    WORLD = "world"
    LOCAL = "local"
    GENERAL = "general"


class NewsSource(Enum):
    REUTERS = "reuters"
    AP = "ap"
    BBC = "bbc"
    CNN = "cnn"
    TECHCRUNCH = "techcrunch"
    ARS_TECHNICA = "ars_technica"
    ESPN = "espn"
    LOCAL_NEWS = "local_news"


@dataclass
class NewsArticle:
    article_id: str
    title: str
    content: str
    summary: str
    url: str
    source: NewsSource
    category: NewsCategory
    published_at: datetime
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    sentiment: Optional[float] = None
    read_time_minutes: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsFeed:
    feed_id: str
    name: str
    description: str
    source: NewsSource
    category: NewsCategory
    url: str
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class NewsAgent(BaseAgent):
    """
    News Aggregation Agent for handling news retrieval and processing.
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        self.feeds: Dict[str, NewsFeed] = {}
        self.articles: Dict[str, NewsArticle] = {}
        self.categories: Dict[str, List[str]] = {}
        self.api_key: Optional[str] = None
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
    async def start(self) -> bool:
        """Start the news agent and initialize news services."""
        if await super().start():
            self.logger.info("News agent started successfully")
            # Load API key from context
            if self.context_manager:
                self.api_key = self.context_manager.get("news_api_key", scope=ContextScope.GLOBAL)
            # Initialize default feeds
            await self._initialize_default_feeds()
            # Start background task for news updates
            asyncio.create_task(self._update_news_periodically())
            return True
        return False
    
    async def stop(self) -> bool:
        """Stop the news agent."""
        if await super().stop():
            self.logger.info("News agent stopped successfully")
            return True
        return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages for news operations."""
        try:
            if message.data.get("action") == "get_latest_news":
                return await self._handle_get_latest_news(message)
            elif message.data.get("action") == "search_news":
                return await self._handle_search_news(message)
            elif message.data.get("action") == "get_news_by_category":
                return await self._handle_get_news_by_category(message)
            elif message.data.get("action") == "add_feed":
                return await self._handle_add_feed(message)
            elif message.data.get("action") == "get_trending_topics":
                return await self._handle_get_trending_topics(message)
            elif message.data.get("action") == "summarize_article":
                return await self._handle_summarize_article(message)
            else:
                return await super().process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": str(e)},
                priority=message.priority
            )
    
    async def _handle_get_latest_news(self, message: Message) -> Message:
        """Handle latest news request."""
        limit = message.data.get("limit", 10)
        category = message.data.get("category")
        source = message.data.get("source")
        
        try:
            articles = await self._get_latest_articles(limit, category, source)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "latest_news",
                    "articles": [self._article_to_dict(article) for article in articles],
                    "count": len(articles),
                    "limit": limit
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting latest news: {str(e)}"}
            )
    
    async def _handle_search_news(self, message: Message) -> Message:
        """Handle news search request."""
        query = message.data.get("query")
        limit = message.data.get("limit", 10)
        date_from = message.data.get("date_from")
        date_to = message.data.get("date_to")
        
        if not query:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Search query is required"}
            )
        
        try:
            articles = await self._search_articles(query, limit, date_from, date_to)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "news_search",
                    "query": query,
                    "articles": [self._article_to_dict(article) for article in articles],
                    "count": len(articles),
                    "limit": limit
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error searching news: {str(e)}"}
            )
    
    async def _handle_get_news_by_category(self, message: Message) -> Message:
        """Handle news by category request."""
        category = message.data.get("category")
        limit = message.data.get("limit", 10)
        
        if not category:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": "Category is required"}
            )
        
        try:
            articles = await self._get_articles_by_category(category, limit)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "news_by_category",
                    "category": category,
                    "articles": [self._article_to_dict(article) for article in articles],
                    "count": len(articles),
                    "limit": limit
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting news by category: {str(e)}"}
            )
    
    async def _handle_add_feed(self, message: Message) -> Message:
        """Handle feed addition request."""
        feed_data = message.data.get("feed_data", {})
        
        feed = NewsFeed(
            feed_id=feed_data.get("feed_id", f"feed_{len(self.feeds) + 1}"),
            name=feed_data.get("name", "Untitled Feed"),
            description=feed_data.get("description", ""),
            source=NewsSource(feed_data.get("source", "general")),
            category=NewsCategory(feed_data.get("category", "general")),
            url=feed_data.get("url", ""),
            enabled=feed_data.get("enabled", True)
        )
        
        self.feeds[feed.feed_id] = feed
        self.logger.info(f"Added news feed: {feed.feed_id} - {feed.name}")
        
        return Message(
            sender=self.agent_id,
            recipient=message.sender,
            content={
                "action": "feed_added",
                "feed_id": feed.feed_id,
                "feed": {
                    "feed_id": feed.feed_id,
                    "name": feed.name,
                    "description": feed.description,
                    "source": feed.source.value,
                    "category": feed.category.value,
                    "url": feed.url,
                    "enabled": feed.enabled,
                    "created_at": feed.created_at.isoformat()
                }
            }
        )
    
    async def _handle_get_trending_topics(self, message: Message) -> Message:
        """Handle trending topics request."""
        limit = message.data.get("limit", 10)
        
        try:
            topics = await self._get_trending_topics(limit)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "trending_topics",
                    "topics": topics,
                    "count": len(topics),
                    "limit": limit
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error getting trending topics: {str(e)}"}
            )
    
    async def _handle_summarize_article(self, message: Message) -> Message:
        """Handle article summarization request."""
        article_id = message.data.get("article_id")
        
        if article_id not in self.articles:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Article {article_id} not found"}
            )
        
        try:
            article = self.articles[article_id]
            summary = await self._summarize_article(article)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "article_summarized",
                    "article_id": article_id,
                    "summary": summary
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error summarizing article: {str(e)}"}
            )
    
    async def _initialize_default_feeds(self):
        """Initialize default news feeds."""
        default_feeds = [
            {
                "feed_id": "tech_news",
                "name": "Technology News",
                "description": "Latest technology news and updates",
                "source": NewsSource.TECHCRUNCH,
                "category": NewsCategory.TECHNOLOGY,
                "url": "https://techcrunch.com/feed/"
            },
            {
                "feed_id": "business_news",
                "name": "Business News",
                "description": "Business and financial news",
                "source": NewsSource.REUTERS,
                "category": NewsCategory.BUSINESS,
                "url": "https://feeds.reuters.com/reuters/businessNews"
            },
            {
                "feed_id": "world_news",
                "name": "World News",
                "description": "International news and events",
                "source": NewsSource.BBC,
                "category": NewsCategory.WORLD,
                "url": "http://feeds.bbci.co.uk/news/world/rss.xml"
            }
        ]
        
        for feed_data in default_feeds:
            feed = NewsFeed(**feed_data)
            self.feeds[feed.feed_id] = feed
    
    async def _update_news_periodically(self):
        """Periodically update news from feeds."""
        while self.status == AgentStatus.RUNNING:
            try:
                await self._fetch_latest_news()
                await asyncio.sleep(3600)  # Update every hour
            except Exception as e:
                self.logger.error(f"Error updating news: {e}")
                await asyncio.sleep(3600)
    
    async def _fetch_latest_news(self):
        """Fetch latest news from all enabled feeds."""
        for feed in self.feeds.values():
            if feed.enabled:
                try:
                    articles = await self._fetch_articles_from_feed(feed)
                    for article in articles:
                        self.articles[article.article_id] = article
                    
                    self.logger.info(f"Fetched {len(articles)} articles from {feed.name}")
                except Exception as e:
                    self.logger.error(f"Error fetching from feed {feed.name}: {e}")
    
    async def _fetch_articles_from_feed(self, feed: NewsFeed) -> List[NewsArticle]:
        """Fetch articles from a specific feed."""
        # Simulate fetching articles from RSS feed
        import random
        
        articles = []
        for i in range(random.randint(3, 8)):
            article = NewsArticle(
                article_id=f"{feed.feed_id}_{len(self.articles) + i}",
                title=f"Sample Article {i + 1} from {feed.name}",
                content=f"This is a sample article content from {feed.name}. It contains some interesting information about {feed.category.value}.",
                summary=f"Summary of article {i + 1} from {feed.name}",
                url=f"https://example.com/article/{i + 1}",
                source=feed.source,
                category=feed.category,
                published_at=datetime.now() - timedelta(hours=random.randint(0, 24)),
                author=f"Author {i + 1}",
                tags=[feed.category.value, "sample"],
                read_time_minutes=random.randint(2, 8)
            )
            articles.append(article)
        
        return articles
    
    async def _get_latest_articles(self, limit: int, category: Optional[str] = None, source: Optional[str] = None) -> List[NewsArticle]:
        """Get latest articles with optional filtering."""
        articles = list(self.articles.values())
        
        # Sort by published date (newest first)
        articles.sort(key=lambda x: x.published_at, reverse=True)
        
        # Apply filters
        if category:
            articles = [a for a in articles if a.category.value == category]
        
        if source:
            articles = [a for a in articles if a.source.value == source]
        
        return articles[:limit]
    
    async def _search_articles(self, query: str, limit: int, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[NewsArticle]:
        """Search articles by query."""
        articles = list(self.articles.values())
        
        # Simple text search
        query_lower = query.lower()
        matching_articles = []
        
        for article in articles:
            if (query_lower in article.title.lower() or 
                query_lower in article.content.lower() or 
                query_lower in article.summary.lower() or
                any(query_lower in tag.lower() for tag in article.tags)):
                matching_articles.append(article)
        
        # Apply date filters
        if date_from:
            from_date = datetime.fromisoformat(date_from)
            matching_articles = [a for a in matching_articles if a.published_at >= from_date]
        
        if date_to:
            to_date = datetime.fromisoformat(date_to)
            matching_articles = [a for a in matching_articles if a.published_at <= to_date]
        
        # Sort by relevance (simple implementation)
        matching_articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return matching_articles[:limit]
    
    async def _get_articles_by_category(self, category: str, limit: int) -> List[NewsArticle]:
        """Get articles by category."""
        articles = [a for a in self.articles.values() if a.category.value == category]
        articles.sort(key=lambda x: x.published_at, reverse=True)
        return articles[:limit]
    
    async def _get_trending_topics(self, limit: int) -> List[Dict[str, Any]]:
        """Get trending topics based on article analysis."""
        # Simple trending topics implementation
        topic_counts = {}
        
        for article in self.articles.values():
            # Count by category
            category = article.category.value
            topic_counts[category] = topic_counts.get(category, 0) + 1
            
            # Count by tags
            for tag in article.tags:
                topic_counts[tag] = topic_counts.get(tag, 0) + 1
        
        # Sort by count and return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        trending_topics = []
        for topic, count in sorted_topics[:limit]:
            trending_topics.append({
                "topic": topic,
                "count": count,
                "trend": "up" if count > 5 else "stable"
            })
        
        return trending_topics
    
    async def _summarize_article(self, article: NewsArticle) -> str:
        """Summarize an article."""
        # Simple summarization (in a real implementation, you'd use NLP)
        words = article.content.split()
        if len(words) <= 50:
            return article.content
        
        # Take first 50 words as summary
        summary_words = words[:50]
        summary = " ".join(summary_words) + "..."
        
        return summary
    
    async def _handle_categorize_news(self, message: Message) -> Message:
        """Handle news categorization request."""
        article_id = message.data.get("article_id")
        
        if article_id not in self.articles:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Article {article_id} not found"}
            )
        
        try:
            article = self.articles[article_id]
            # Simple categorization based on keywords
            category = self._categorize_article(article)
            
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={
                    "action": "article_categorized",
                    "article_id": article_id,
                    "category": category
                }
            )
        except Exception as e:
            return Message(
                sender=self.agent_id,
                recipient=message.sender,
                content={"error": f"Error categorizing article: {str(e)}"}
            )
    
    def _categorize_article(self, article: NewsArticle) -> str:
        """Categorize an article based on content."""
        content_lower = (article.title + " " + article.content).lower()
        
        # Simple keyword-based categorization
        if any(word in content_lower for word in ["tech", "software", "ai", "computer", "digital"]):
            return "technology"
        elif any(word in content_lower for word in ["business", "economy", "finance", "market", "stock"]):
            return "business"
        elif any(word in content_lower for word in ["sport", "game", "team", "player", "match"]):
            return "sports"
        elif any(word in content_lower for word in ["movie", "music", "entertainment", "celebrity"]):
            return "entertainment"
        elif any(word in content_lower for word in ["health", "medical", "doctor", "hospital"]):
            return "health"
        else:
            return "general"
    
    def _article_to_dict(self, article: NewsArticle) -> Dict[str, Any]:
        """Convert article to dictionary for serialization."""
        return {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "url": article.url,
            "source": article.source.value,
            "category": article.category.value,
            "published_at": article.published_at.isoformat(),
            "author": article.author,
            "tags": article.tags,
            "sentiment": article.sentiment,
            "read_time_minutes": article.read_time_minutes,
            "metadata": article.metadata
        }
    
    async def _process_message_impl(self, message: Message) -> Dict[str, Any]:
        """Implementation of message processing for news agent."""
        try:
            action = message.data.get("action")
            
            if action == "get_latest_news":
                return await self._handle_get_latest_news(message)
            elif action == "search_news":
                return await self._handle_search_news(message)
            elif action == "categorize_news":
                return await self._handle_categorize_news(message)
            elif action == "add_feed":
                return await self._handle_add_feed(message)
            elif action == "get_trending_topics":
                return await self._handle_get_trending_topics(message)
            elif action == "categorize_news":
                return await self._handle_categorize_news(message)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in _process_message_impl: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get news agent metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "total_feeds": len(self.feeds),
            "total_articles": len(self.articles),
            "enabled_feeds": len([f for f in self.feeds.values() if f.enabled]),
            "articles_by_category": {
                category.value: len([a for a in self.articles.values() if a.category == category])
                for category in NewsCategory
            },
            "articles_by_source": {
                source.value: len([a for a in self.articles.values() if a.source == source])
                for source in NewsSource
            },
            "api_key_configured": self.api_key is not None
        })
        return metrics
