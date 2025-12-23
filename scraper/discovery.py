import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse

class Discovery:
    def __init__(self, base_url="https://www.kokkieblanda.nl"):
        self.base_url = base_url
        self.visited = set()
        self.recipe_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ResearchBot/1.0 (+http://example.com) - Educational Project"
        })
    
    def get_soup(self, url):
        """Fetch and parse a URL with politeness delay."""
        if url in self.visited:
            return None
            
        print(f"Fetching {url}...")
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            self.visited.add(url)
            time.sleep(1.0) # Rate limiting
            return BeautifulSoup(r.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def is_recipe_url(self, href):
        """
        Check if href matches recipe pattern: /{cuisine}/{category}/{id}-{slug}
        Example: /indonesian/daging-rundvlees/1909-rendang-rendang-van-rundvlees
        """
        # Must have 3 parts after root.
        # Note: href might be full URL or relative.
        path = urlparse(href).path
        parts = [p for p in path.strip('/').split('/') if p]
        
        # We expect at least 3 parts: [cuisine, category, id-slug]
        if len(parts) >= 3:
            # Check if 3rd part starts with number
            if re.match(r'^\d+-', parts[2]):
                return True
        return False

    def is_category_url(self, href, root_path):
        """
        Check if valid category URL to follow.
        Should start with root_path and not be a recipe.
        """
        full_url = urljoin(self.base_url, href)
        parsed = urlparse(full_url)
        path = parsed.path
        
        # Ensure it belongs to the domain
        if parsed.netloc and parsed.netloc != urlparse(self.base_url).netloc:
            return False
            
        # Ensure it is under the root scope (e.g. /indonesian)
        if not path.startswith(root_path):
            return False
            
        # Ignore common non-content paths
        if any(x in path for x in ['login', 'register', 'profile', 'search']):
            return False
            
        return True

    def crawl(self, start_paths=["/indonesian", "/thailand", "/china", "/filipijnen", "/korea", "/overige-gerechten"], limit=None):
        """
        Main crawl loop.
        start_paths: list of paths to start discovery from (e.g. ['/indonesian'])
        limit: max number of recipes to find
        """
        queue = []
        for p in start_paths:
            full = urljoin(self.base_url, p)
            queue.append(full)
        
        # Removed max_pages limit for full scrape
        pages_crawled = 0
        
        while queue:
            if limit and len(self.recipe_urls) >= limit:
                break
                
            url = queue.pop(0)
            if url in self.visited:
                continue

            # Identify the root scope for this URL to safeguard crawling
            path = urlparse(url).path
            root_scope = "/" + path.strip('/').split('/')[0] # e.g. /indonesian
            
            soup = self.get_soup(url)
            if not soup:
                continue
            
            pages_crawled += 1
            
            # Extract links
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                full_link = urljoin(self.base_url, href)
                
                if self.is_recipe_url(href):
                    if full_link not in self.recipe_urls:
                        self.recipe_urls.add(full_link)
                        if limit and len(self.recipe_urls) >= limit:
                            break
                
                elif self.is_category_url(href, root_scope):
                    if full_link not in self.visited and full_link not in queue:
                        queue.append(full_link)
        
        print(f"Discovery complete. Found {len(self.recipe_urls)} recipes.")
        return list(self.recipe_urls)

if __name__ == "__main__":
    # Test run
    d = Discovery()
    # Test with a small scope
    d.crawl(start_paths=["/indonesian/daging-rundvlees"])
