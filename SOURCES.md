# Sources — The Operating Brief

All RSS feeds ingested by `daily_digest.py`. Daily sources are fetched every run (Monday lookback is 72h, other days 24h). Weekly sources are fetched on Mondays only with a 7-day lookback, covering major tech companies that influence AI strategy.

To add/remove a source: edit the relevant section below **and** update the corresponding `FEEDS` or `WEEKLY_FEEDS` dict in `daily_digest.py`.

---

## Daily Sources

### AI & Technology
| Name | Feed URL |
|---|---|
| TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/feed/ |
| VentureBeat AI | https://venturebeat.com/category/ai/feed/ |
| The Verge AI | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml |
| Hacker News (AI, 50+ pts) | https://hnrss.org/newest?q=AI&points=50 |
| OpenAI News | https://openai.com/news/rss.xml |
| Anthropic | https://www.anthropic.com/rss.xml |
| Hugging Face Blog | https://huggingface.co/blog/feed.xml |
| MIT Technology Review | https://www.technologyreview.com/feed/ |
| Ars Technica AI | https://arstechnica.com/ai/feed/ |
| ZDNet AI | https://www.zdnet.com/topic/artificial-intelligence/rss.xml |

### Podcasts
| Name | Feed URL |
|---|---|
| Lex Fridman Podcast | https://lexfridman.com/feed/podcast/ |
| TWIML AI Podcast | https://twimlai.com/feed/ |
| The AI Daily Brief | https://anchor.fm/s/f7cac464/podcast/rss |
| No Priors | https://feeds.megaphone.fm/nopriors |
| The Cognitive Revolution | https://feeds.megaphone.fm/RINTP3108857801 |
| Latent Space | https://api.substack.com/feed/podcast/1084089.rss |
| Practical AI | https://changelog.com/practicalai/feed |

### World News
| Name | Feed URL |
|---|---|
| BBC World | https://feeds.bbci.co.uk/news/world/rss.xml |
| Reuters Top News | https://feeds.reuters.com/reuters/topNews |
| The Guardian World | https://www.theguardian.com/world/rss |
| New York Times World | https://rss.nytimes.com/services/xml/rss/nyt/World.xml |
| Wall Street Journal World | https://feeds.a.dj.com/rss/RSSWorldNews.xml |
| Sky News World | https://feeds.skynews.com/feeds/rss/world.xml |
| NPR News | https://feeds.npr.org/1004/rss.xml |

### Australian News
| Name | Feed URL |
|---|---|
| ABC News (National) | https://www.abc.net.au/news/feed/51120/rss.xml |
| Sydney Morning Herald | https://www.smh.com.au/rss/feed.xml |
| The Guardian Australia | https://www.theguardian.com/australia-news/rss |
| Australian Financial Review | https://www.afr.com/rss/feed.xml |
| News.com.au National | https://www.news.com.au/content-feeds/latest-news-national/ |
| 7News Australia | https://7news.com.au/news/australia/rss |
| ABC News (Politics) | https://www.abc.net.au/news/feed/45910/rss.xml |

---

## Weekly Sources (Mondays only — 7-day lookback)

These cover major tech companies whose product, earnings, and AI announcements shape the broader landscape. Fetched once per week so they don't crowd out daily AI news.

### Big Tech & Enterprise AI
| Name | Feed URL | Why weekly |
|---|---|---|
| Microsoft News | https://news.microsoft.com/feed/ | Azure AI, Copilot, enterprise |
| Microsoft AI Blog | https://blogs.microsoft.com/ai/feed/ | Direct AI announcements |
| Apple Newsroom | https://www.apple.com/newsroom/rss-feed.xml | Apple Intelligence, hardware |
| Meta AI Blog | https://ai.meta.com/blog/rss/ | LLaMA, open-source AI |
| Meta Newsroom | https://about.fb.com/news/feed/ | Platform & product moves |
| Amazon AWS News | https://aws.amazon.com/blogs/aws/feed/ | Bedrock, enterprise cloud AI |
| Amazon Newsroom | https://www.aboutamazon.com/news/rss | Alexa+, broader strategy |
| Google AI Blog | https://blog.google/technology/ai/rss/ | Gemini, DeepMind |
| Google DeepMind | https://deepmind.google/blog/rss/ | Research & model releases |
| Oracle Blog | https://blogs.oracle.com/rss | Enterprise AI, cloud |
| Workday Blog | https://blog.workday.com/en-us/feed.xml | HR/finance AI, enterprise |
| Salesforce News | https://www.salesforce.com/news/feed/ | Agentforce, CRM AI |
| SAP News | https://news.sap.com/feed/ | Enterprise AI, ERP |

---

## Sources Under Consideration
> Add candidates here before committing them to the feed lists above.

| Name | Feed URL | Category | Notes |
|---|---|---|---|
| — | — | — | — |

---

## Removed Sources
> Log removed sources here so we don't re-add them accidentally.

| Name | Removed | Reason |
|---|---|---|
| — | — | — |
