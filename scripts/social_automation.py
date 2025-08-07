#!/usr/bin/env python3
"""
Social Media Automation System for Baby Sleep Blog
Automatically creates and posts content to Pinterest, Reddit, and Medium
"""

import os
import json
import yaml
import requests
import openai
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime, timedelta
import random

@dataclass
class SocialPost:
    platform: str
    title: str
    description: str
    image_url: str
    target_url: str
    hashtags: List[str]
    scheduled_time: datetime

class SocialMediaAutomator:
    def __init__(self, config_path: str = "/workspace/config/config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_apis()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_apis(self):
        """Setup API connections"""
        # OpenAI for content generation
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Pinterest API (requires OAuth)
        self.pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')
        
        # Reddit API (requires OAuth)
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.reddit_username = os.getenv('REDDIT_USERNAME')
        self.reddit_password = os.getenv('REDDIT_PASSWORD')
        
        # Medium API
        self.medium_token = os.getenv('MEDIUM_INTEGRATION_TOKEN')
    
    def create_pinterest_pin_image(self, title: str, featured_image_prompt: str) -> str:
        """Create Pinterest-optimized pin image using DALL-E"""
        
        # Generate image with DALL-E
        pinterest_prompt = f"""
        Create a Pinterest-style pin image with these specifications:
        - Vertical aspect ratio (2:3 or 1:1.5)
        - Title text overlay: "{title}"
        - Soft, warm colors suitable for baby/parenting content
        - Clean, readable typography
        - Professional yet approachable design
        - Image content: {featured_image_prompt}
        - Include subtle branding elements
        - Optimized for Pinterest discovery
        """
        
        response = openai.Image.create(
            prompt=pinterest_prompt,
            n=1,
            size="1024x1536",  # Pinterest-optimized ratio
            response_format="url"
        )
        
        return response['data'][0]['url']
    
    def generate_pinterest_description(self, blog_title: str, blog_excerpt: str) -> Tuple[str, List[str]]:
        """Generate Pinterest description and hashtags"""
        
        prompt = f"""
        Create an engaging Pinterest description for this blog post:
        Title: {blog_title}
        Excerpt: {blog_excerpt}
        
        Requirements:
        1. 100-200 characters
        2. Include a compelling hook
        3. Use actionable language
        4. Include call-to-action
        5. Pinterest-friendly tone
        
        Also generate 10-15 relevant hashtags for baby sleep content.
        
        Format as JSON:
        {{
            "description": "...",
            "hashtags": ["#babysleep", "#parentingtips", ...]
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result['description'], result['hashtags']
        except json.JSONDecodeError:
            # Fallback
            return f"Discover proven baby sleep tips! {blog_excerpt[:100]}... Click to read more! 💤", ["#babysleep", "#parentingtips", "#newborn"]
    
    def create_pinterest_pin(self, blog_post: Dict) -> Optional[str]:
        """Create and schedule Pinterest pin"""
        if not self.config['social']['pinterest']['enabled'] or not self.pinterest_token:
            return None
        
        try:
            # Generate pin image
            pin_image_url = self.create_pinterest_pin_image(
                blog_post['title'], 
                blog_post.get('featured_image_prompt', 'baby sleeping peacefully')
            )
            
            # Generate description and hashtags
            description, hashtags = self.generate_pinterest_description(
                blog_post['title'], 
                blog_post.get('excerpt', '')
            )
            
            # Format description with hashtags
            full_description = f"{description}\n\n{' '.join(hashtags[:10])}"
            
            # Pinterest API call
            pin_data = {
                "link": f"{self.config['site']['url']}/blog/{blog_post['slug']}",
                "description": full_description,
                "image_url": pin_image_url,
                "board_id": self.get_pinterest_board_id("Baby Sleep Tips")
            }
            
            headers = {
                "Authorization": f"Bearer {self.pinterest_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.pinterest.com/v5/pins",
                headers=headers,
                json=pin_data
            )
            
            if response.status_code == 201:
                pin_id = response.json()['id']
                print(f"✓ Pinterest pin created: {pin_id}")
                return pin_id
            else:
                print(f"✗ Pinterest pin failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Pinterest error: {e}")
            return None
    
    def get_pinterest_board_id(self, board_name: str) -> str:
        """Get Pinterest board ID by name"""
        # This would require fetching boards from Pinterest API
        # For now, return a placeholder
        return "1234567890"
    
    def create_reddit_post(self, blog_post: Dict) -> Optional[str]:
        """Create Reddit post"""
        if not self.config['social']['reddit']['enabled']:
            return None
        
        try:
            # Generate Reddit-appropriate title and content
            reddit_content = self.generate_reddit_content(blog_post)
            
            # Get Reddit access token
            access_token = self.get_reddit_access_token()
            if not access_token:
                return None
            
            # Choose appropriate subreddit
            subreddit = self.choose_reddit_subreddit(blog_post['title'])
            
            # Create post
            post_data = {
                "sr": subreddit,
                "kind": "self",  # Text post
                "title": reddit_content['title'],
                "text": reddit_content['text'],
                "api_type": "json"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "BabySleepBot/1.0"
            }
            
            response = requests.post(
                "https://oauth.reddit.com/api/submit",
                headers=headers,
                data=post_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('json', {}).get('errors'):
                    print(f"✗ Reddit post error: {result['json']['errors']}")
                    return None
                else:
                    post_url = result['json']['data']['url']
                    print(f"✓ Reddit post created: {post_url}")
                    return post_url
            else:
                print(f"✗ Reddit post failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Reddit error: {e}")
            return None
    
    def generate_reddit_content(self, blog_post: Dict) -> Dict:
        """Generate Reddit-appropriate content"""
        prompt = f"""
        Adapt this blog post for Reddit posting:
        Title: {blog_post['title']}
        Excerpt: {blog_post.get('excerpt', '')}
        
        Create:
        1. A Reddit-friendly title (no clickbait, authentic)
        2. A helpful text post that provides value upfront
        3. Naturally mention the full article without being spammy
        
        Reddit guidelines:
        - Be genuinely helpful
        - Don't be overly promotional
        - Focus on community value
        - Use conversational tone
        - Include personal touch
        
        Format as JSON:
        {{
            "title": "...",
            "text": "..."
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback
            return {
                "title": f"Tips: {blog_post['title']}",
                "text": f"{blog_post.get('excerpt', '')} [Full article here: link]"
            }
    
    def choose_reddit_subreddit(self, title: str) -> str:
        """Choose appropriate subreddit based on content"""
        subreddits = self.config['social']['reddit']['subreddits']
        
        # Simple keyword matching
        title_lower = title.lower()
        
        if 'newborn' in title_lower or '0-3 month' in title_lower:
            return 'NewParents'
        elif 'sleep training' in title_lower:
            return 'sleeptrain'
        elif 'beyond the bump' in title_lower or 'toddler' in title_lower:
            return 'beyondthebump'
        else:
            return 'Parenting'  # Default
    
    def get_reddit_access_token(self) -> Optional[str]:
        """Get Reddit OAuth access token"""
        auth = requests.auth.HTTPBasicAuth(self.reddit_client_id, self.reddit_client_secret)
        
        data = {
            'grant_type': 'password',
            'username': self.reddit_username,
            'password': self.reddit_password
        }
        
        headers = {'User-Agent': 'BabySleepBot/1.0'}
        
        try:
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                print(f"✗ Reddit auth failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Reddit auth error: {e}")
            return None
    
    def create_medium_article(self, blog_post: Dict) -> Optional[str]:
        """Cross-post to Medium"""
        if not self.config['social']['medium']['enabled'] or not self.medium_token:
            return None
        
        try:
            # Adapt content for Medium
            medium_content = self.adapt_for_medium(blog_post)
            
            # Get user ID
            user_id = self.get_medium_user_id()
            if not user_id:
                return None
            
            # Create post
            post_data = {
                "title": medium_content['title'],
                "contentFormat": "html",
                "content": medium_content['content'],
                "tags": medium_content['tags'],
                "publishStatus": "public",
                "canonicalUrl": f"{self.config['site']['url']}/blog/{blog_post['slug']}"
            }
            
            headers = {
                "Authorization": f"Bearer {self.medium_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"https://api.medium.com/v1/users/{user_id}/posts",
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                post_url = response.json()['data']['url']
                print(f"✓ Medium article created: {post_url}")
                return post_url
            else:
                print(f"✗ Medium post failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Medium error: {e}")
            return None
    
    def adapt_for_medium(self, blog_post: Dict) -> Dict:
        """Adapt blog post for Medium"""
        # Add canonical link notice
        canonical_notice = f"""
<p><em>This article was originally published on <a href="{self.config['site']['url']}/blog/{blog_post['slug']}">{self.config['site']['title']}</a>.</em></p>
"""
        
        # Clean up content and add notice
        content = canonical_notice + blog_post['content']
        
        # Extract tags from keywords
        tags = blog_post.get('keywords', [])[:5]  # Medium allows up to 5 tags
        
        return {
            "title": blog_post['title'],
            "content": content,
            "tags": tags
        }
    
    def get_medium_user_id(self) -> Optional[str]:
        """Get Medium user ID"""
        headers = {
            "Authorization": f"Bearer {self.medium_token}"
        }
        
        try:
            response = requests.get(
                "https://api.medium.com/v1/me",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()['data']['id']
            else:
                print(f"✗ Medium user fetch failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Medium user error: {e}")
            return None
    
    def schedule_social_posts(self, blog_posts: List[Dict]) -> Dict:
        """Schedule social media posts for multiple blog posts"""
        results = {
            'pinterest': [],
            'reddit': [],
            'medium': [],
            'errors': []
        }
        
        for post in blog_posts:
            print(f"\n📱 Creating social posts for: {post['title']}")
            
            # Pinterest
            if self.config['social']['pinterest']['enabled']:
                pinterest_result = self.create_pinterest_pin(post)
                if pinterest_result:
                    results['pinterest'].append(pinterest_result)
            
            # Reddit (with rate limiting)
            if self.config['social']['reddit']['enabled']:
                reddit_result = self.create_reddit_post(post)
                if reddit_result:
                    results['reddit'].append(reddit_result)
            
            # Medium
            if self.config['social']['medium']['enabled']:
                medium_result = self.create_medium_article(post)
                if medium_result:
                    results['medium'].append(medium_result)
        
        return results
    
    def generate_social_calendar(self, days: int = 30) -> List[SocialPost]:
        """Generate a social media posting calendar"""
        calendar = []
        
        # Generate posting schedule
        start_date = datetime.now()
        
        for day in range(days):
            post_date = start_date + timedelta(days=day)
            
            # Pinterest: 5 pins per day
            for i in range(5):
                pin_time = post_date.replace(
                    hour=random.randint(8, 20),
                    minute=random.randint(0, 59)
                )
                
                calendar.append(SocialPost(
                    platform="pinterest",
                    title="Generated Pin Title",
                    description="Generated description",
                    image_url="",
                    target_url="",
                    hashtags=[],
                    scheduled_time=pin_time
                ))
        
        return calendar

def main():
    """Test social media automation"""
    automator = SocialMediaAutomator()
    
    # Test blog post
    test_post = {
        'title': 'How to Get Your Baby to Sleep Through the Night',
        'slug': 'baby-sleep-through-night',
        'excerpt': 'Discover gentle, proven methods to help your baby sleep through the night without tears.',
        'content': '<p>Test content...</p>',
        'keywords': ['baby sleep', 'sleep training', 'newborn'],
        'featured_image_prompt': 'peaceful baby sleeping in crib'
    }
    
    # Test social posting
    results = automator.schedule_social_posts([test_post])
    
    print("\n=== SOCIAL MEDIA RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()