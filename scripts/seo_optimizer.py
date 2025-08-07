#!/usr/bin/env python3
"""
SEO Optimization System for Baby Sleep Blog
Handles keyword research, meta optimization, sitemap generation, and SEO analysis
"""

import re
import json
import yaml
import requests
import openai
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
import os

@dataclass
class SEOAnalysis:
    keyword_density: Dict[str, float]
    readability_score: float
    meta_description_length: int
    title_length: int
    h1_count: int
    h2_count: int
    image_alt_count: int
    internal_links: int
    external_links: int
    word_count: int
    seo_score: float

class SEOOptimizer:
    def __init__(self, config_path: str = "/workspace/config/config.yaml"):
        self.config = self.load_config(config_path)
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def optimize_title(self, title: str, primary_keyword: str) -> str:
        """Optimize title for SEO"""
        prompt = f"""
        Optimize this blog post title for SEO:
        Current title: {title}
        Primary keyword: {primary_keyword}
        
        Requirements:
        1. Include the primary keyword naturally
        2. Keep under 60 characters
        3. Make it compelling and clickable
        4. Use power words when appropriate
        5. Ensure it's specific and descriptive
        
        Return only the optimized title, nothing else.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        optimized_title = response.choices[0].message.content.strip()
        
        # Ensure title length is under 60 characters
        if len(optimized_title) > 60:
            optimized_title = optimized_title[:57] + "..."
        
        return optimized_title
    
    def generate_meta_description(self, title: str, content: str, primary_keyword: str) -> str:
        """Generate optimized meta description"""
        prompt = f"""
        Create an SEO-optimized meta description for this blog post:
        Title: {title}
        Primary keyword: {primary_keyword}
        Content preview: {content[:300]}...
        
        Requirements:
        1. 150-160 characters exactly
        2. Include primary keyword naturally
        3. Be compelling and click-worthy
        4. Include a call-to-action
        5. Accurately describe the content
        
        Return only the meta description, nothing else.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        meta_description = response.choices[0].message.content.strip()
        
        # Ensure proper length
        if len(meta_description) > 160:
            meta_description = meta_description[:157] + "..."
        elif len(meta_description) < 150:
            meta_description += " Learn more here."
        
        return meta_description
    
    def optimize_headings(self, content: str, primary_keyword: str) -> str:
        """Optimize headings for SEO"""
        # Extract current headings
        h2_pattern = r'<h2[^>]*>(.*?)</h2>'
        h3_pattern = r'<h3[^>]*>(.*?)</h3>'
        
        h2_headings = re.findall(h2_pattern, content, re.IGNORECASE)
        h3_headings = re.findall(h3_pattern, content, re.IGNORECASE)
        
        # Optimize headings with AI
        prompt = f"""
        Optimize these headings for SEO with the primary keyword "{primary_keyword}":
        
        H2 Headings:
        {json.dumps(h2_headings, indent=2)}
        
        H3 Headings:
        {json.dumps(h3_headings, indent=2)}
        
        Requirements:
        1. Include primary keyword in at least one H2
        2. Use related keywords in other headings
        3. Keep headings descriptive and useful
        4. Maintain natural language flow
        5. Include numbers when appropriate
        
        Return optimized headings in the same JSON format.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        try:
            optimized_headings = json.loads(response.choices[0].message.content)
            
            # Replace headings in content
            for i, old_heading in enumerate(h2_headings):
                if i < len(optimized_headings.get('h2_headings', [])):
                    new_heading = optimized_headings['h2_headings'][i]
                    content = content.replace(f'<h2>{old_heading}</h2>', f'<h2>{new_heading}</h2>')
            
            for i, old_heading in enumerate(h3_headings):
                if i < len(optimized_headings.get('h3_headings', [])):
                    new_heading = optimized_headings['h3_headings'][i]
                    content = content.replace(f'<h3>{old_heading}</h3>', f'<h3>{new_heading}</h3>')
                    
        except json.JSONDecodeError:
            print("Failed to parse optimized headings")
        
        return content
    
    def add_internal_links(self, content: str, existing_posts: List[Dict]) -> str:
        """Add relevant internal links to content"""
        # Find opportunities for internal linking
        linking_opportunities = self.find_internal_link_opportunities(content, existing_posts)
        
        for opportunity in linking_opportunities:
            # Replace first occurrence of anchor text with link
            old_text = opportunity['anchor_text']
            new_text = f'<a href="/blog/{opportunity["slug"]}">{old_text}</a>'
            content = content.replace(old_text, new_text, 1)
        
        return content
    
    def find_internal_link_opportunities(self, content: str, existing_posts: List[Dict]) -> List[Dict]:
        """Find opportunities for internal linking"""
        opportunities = []
        content_lower = content.lower()
        
        for post in existing_posts:
            # Check if post title or keywords appear in content
            title_words = post['title'].lower().split()
            
            # Look for partial matches
            for i in range(len(title_words) - 1):
                phrase = ' '.join(title_words[i:i+2])
                if phrase in content_lower and len(phrase) > 5:
                    opportunities.append({
                        'anchor_text': phrase.title(),
                        'slug': post['slug'],
                        'target_title': post['title']
                    })
                    break
        
        return opportunities[:3]  # Limit to 3 internal links
    
    def optimize_images(self, content: str, primary_keyword: str) -> str:
        """Add alt text to images"""
        img_pattern = r'<img([^>]*?)>'
        
        def add_alt_text(match):
            img_tag = match.group(0)
            if 'alt=' not in img_tag:
                # Generate appropriate alt text
                alt_text = f"{primary_keyword} - baby sleep tips"
                return img_tag.replace('>', f' alt="{alt_text}">')
            return img_tag
        
        return re.sub(img_pattern, add_alt_text, content)
    
    def calculate_keyword_density(self, content: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density"""
        # Remove HTML tags for analysis
        text_content = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_content.split())
        
        keyword_density = {}
        
        for keyword in keywords:
            # Count occurrences (case insensitive)
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text_content, re.IGNORECASE))
            density = (count / word_count) * 100 if word_count > 0 else 0
            keyword_density[keyword] = round(density, 2)
        
        return keyword_density
    
    def analyze_readability(self, content: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        
        # Count sentences
        sentences = len(re.findall(r'[.!?]+', text))
        
        # Count words
        words = len(text.split())
        
        # Count syllables (simplified)
        syllables = sum([max(1, len(re.findall(r'[aeiouAEIOU]', word))) for word in text.split()])
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch Reading Ease formula
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        return max(0, min(100, readability))
    
    def perform_seo_analysis(self, title: str, content: str, meta_description: str, keywords: List[str]) -> SEOAnalysis:
        """Perform comprehensive SEO analysis"""
        
        # Keyword density
        keyword_density = self.calculate_keyword_density(content, keywords)
        
        # Readability
        readability_score = self.analyze_readability(content)
        
        # Count elements
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        
        # Images with alt text
        img_total = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
        img_with_alt = len(re.findall(r'<img[^>]*alt=', content, re.IGNORECASE))
        
        # Links
        internal_links = len(re.findall(r'<a[^>]*href="/', content, re.IGNORECASE))
        external_links = len(re.findall(r'<a[^>]*href="http', content, re.IGNORECASE))
        
        # Word count
        text_content = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_content.split())
        
        # Calculate overall SEO score
        score = 0
        
        # Title length (max 20 points)
        if 30 <= len(title) <= 60:
            score += 20
        elif len(title) < 30 or len(title) > 60:
            score += 10
        
        # Meta description length (max 15 points)
        if 150 <= len(meta_description) <= 160:
            score += 15
        elif 140 <= len(meta_description) <= 170:
            score += 10
        
        # Keyword density (max 20 points)
        primary_keyword = keywords[0] if keywords else ""
        primary_density = keyword_density.get(primary_keyword, 0)
        if 1 <= primary_density <= 3:
            score += 20
        elif 0.5 <= primary_density <= 5:
            score += 15
        elif primary_density > 0:
            score += 10
        
        # Headings (max 15 points)
        if h2_count >= 3:
            score += 15
        elif h2_count >= 1:
            score += 10
        
        # Word count (max 15 points)
        if 1500 <= word_count <= 3000:
            score += 15
        elif 1000 <= word_count <= 4000:
            score += 10
        
        # Images with alt text (max 10 points)
        if img_total > 0 and img_with_alt == img_total:
            score += 10
        elif img_with_alt > 0:
            score += 5
        
        # Internal links (max 5 points)
        if internal_links >= 2:
            score += 5
        elif internal_links >= 1:
            score += 3
        
        return SEOAnalysis(
            keyword_density=keyword_density,
            readability_score=readability_score,
            meta_description_length=len(meta_description),
            title_length=len(title),
            h1_count=h1_count,
            h2_count=h2_count,
            image_alt_count=img_with_alt,
            internal_links=internal_links,
            external_links=external_links,
            word_count=word_count,
            seo_score=score
        )
    
    def generate_sitemap(self, posts: List[Dict], pages: List[Dict] = None) -> str:
        """Generate XML sitemap"""
        root = ET.Element('urlset')
        root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        base_url = self.config['site']['url']
        
        # Homepage
        url = ET.SubElement(root, 'url')
        ET.SubElement(url, 'loc').text = base_url
        ET.SubElement(url, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(url, 'changefreq').text = 'daily'
        ET.SubElement(url, 'priority').text = '1.0'
        
        # Blog posts
        for post in posts:
            url = ET.SubElement(root, 'url')
            ET.SubElement(url, 'loc').text = f"{base_url}/blog/{post['slug']}"
            ET.SubElement(url, 'lastmod').text = post.get('date', datetime.now().strftime('%Y-%m-%d'))
            ET.SubElement(url, 'changefreq').text = 'weekly'
            ET.SubElement(url, 'priority').text = '0.8'
        
        # Static pages
        if pages:
            for page in pages:
                url = ET.SubElement(root, 'url')
                ET.SubElement(url, 'loc').text = f"{base_url}/{page['slug']}"
                ET.SubElement(url, 'lastmod').text = page.get('date', datetime.now().strftime('%Y-%m-%d'))
                ET.SubElement(url, 'changefreq').text = 'monthly'
                ET.SubElement(url, 'priority').text = '0.6'
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def generate_robots_txt(self) -> str:
        """Generate robots.txt file"""
        base_url = self.config['site']['url']
        
        robots_content = f"""User-agent: *
Allow: /

# Sitemaps
Sitemap: {base_url}/sitemap.xml

# Disallow admin areas
Disallow: /admin/
Disallow: /config/
Disallow: /scripts/

# Allow important pages
Allow: /blog/
Allow: /static/
"""
        return robots_content
    
    def optimize_content(self, post_data: Dict, existing_posts: List[Dict] = None) -> Tuple[Dict, SEOAnalysis]:
        """Optimize a blog post for SEO"""
        if existing_posts is None:
            existing_posts = []
            
        # Extract data
        title = post_data['title']
        content = post_data['content']
        primary_keyword = post_data.get('keywords', [''])[0]
        
        # Optimize title
        optimized_title = self.optimize_title(title, primary_keyword)
        
        # Generate meta description
        meta_description = self.generate_meta_description(optimized_title, content, primary_keyword)
        
        # Optimize headings
        optimized_content = self.optimize_headings(content, primary_keyword)
        
        # Add internal links
        optimized_content = self.add_internal_links(optimized_content, existing_posts)
        
        # Optimize images
        optimized_content = self.optimize_images(optimized_content, primary_keyword)
        
        # Update post data
        optimized_post = post_data.copy()
        optimized_post['title'] = optimized_title
        optimized_post['content'] = optimized_content
        optimized_post['meta_description'] = meta_description
        
        # Perform SEO analysis
        seo_analysis = self.perform_seo_analysis(
            optimized_title, 
            optimized_content, 
            meta_description, 
            post_data.get('keywords', [])
        )
        
        return optimized_post, seo_analysis
    
    def generate_schema_markup(self, post_data: Dict) -> Dict:
        """Generate JSON-LD schema markup for blog post"""
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post_data['title'],
            "description": post_data.get('meta_description', ''),
            "author": {
                "@type": "Person",
                "name": self.config['site']['author']
            },
            "publisher": {
                "@type": "Organization",
                "name": self.config['site']['title'],
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{self.config['site']['url']}/static/images/logo.png"
                }
            },
            "datePublished": post_data.get('date', datetime.now().isoformat()),
            "dateModified": post_data.get('date', datetime.now().isoformat()),
            "url": f"{self.config['site']['url']}/blog/{post_data['slug']}",
            "image": f"{self.config['site']['url']}/static/images/blog/{post_data['slug']}.jpg",
            "articleSection": post_data.get('category', 'Baby Sleep Tips'),
            "keywords": post_data.get('keywords', [])
        }
        
        return schema

def main():
    """Test SEO optimization"""
    optimizer = SEOOptimizer()
    
    # Test post
    test_post = {
        'title': 'Baby Sleep Tips for New Parents',
        'content': '''
        <h2>Understanding Baby Sleep</h2>
        <p>Baby sleep is important for development. Many parents struggle with sleep training.</p>
        
        <h2>Creating a Sleep Routine</h2>
        <p>A consistent routine helps babies sleep better. White noise can help too.</p>
        
        <h3>Bedtime Steps</h3>
        <p>Follow these steps for better sleep.</p>
        ''',
        'keywords': ['baby sleep', 'sleep training', 'newborn sleep'],
        'slug': 'baby-sleep-tips-new-parents',
        'date': '2024-01-01'
    }
    
    # Optimize content
    optimized_post, analysis = optimizer.optimize_content(test_post)
    
    print("=== SEO ANALYSIS ===")
    print(f"SEO Score: {analysis.seo_score}/100")
    print(f"Word Count: {analysis.word_count}")
    print(f"Readability: {analysis.readability_score}")
    print(f"Keyword Density: {analysis.keyword_density}")
    
    print("\n=== OPTIMIZED CONTENT ===")
    print(f"Title: {optimized_post['title']}")
    print(f"Meta: {optimized_post['meta_description']}")

if __name__ == "__main__":
    main()