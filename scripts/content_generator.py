#!/usr/bin/env python3
"""
AI-Powered Content Generator for Baby Sleep Blog
Generates high-quality, SEO-optimized blog posts using OpenAI GPT
"""

import os
import json
import yaml
import openai
import datetime
import re
from pathlib import Path
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass

@dataclass
class BlogPost:
    title: str
    content: str
    meta_description: str
    keywords: List[str]
    featured_image_prompt: str
    category: str
    slug: str
    excerpt: str
    affiliate_products: List[Dict]

class BabySleepContentGenerator:
    def __init__(self, config_path: str = "/workspace/config/config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_openai()
        self.content_templates = self.load_content_templates()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_openai(self):
        """Initialize OpenAI client"""
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    def load_content_templates(self) -> Dict:
        """Load content templates and prompts"""
        return {
            "article_types": [
                "How-to guides",
                "Problem-solving articles", 
                "Age-specific sleep tips",
                "Product reviews",
                "Sleep science explanations",
                "Real parent stories",
                "Expert interviews",
                "Troubleshooting guides"
            ],
            "baby_sleep_topics": [
                "newborn sleep patterns",
                "sleep regression solutions", 
                "gentle sleep training methods",
                "creating bedtime routines",
                "dealing with night wakings",
                "nap scheduling",
                "sleep safety guidelines",
                "co-sleeping considerations",
                "sleep props and weaning",
                "travel and sleep disruptions",
                "daylight saving time adjustments",
                "teething and sleep",
                "growth spurts and sleep",
                "premature baby sleep",
                "multiple babies sleep management"
            ],
            "age_groups": [
                "0-3 months (newborn)",
                "3-6 months",
                "6-12 months",
                "12-18 months", 
                "18+ months (toddler)"
            ],
            "content_formats": [
                "Ultimate guide",
                "Step-by-step tutorial",
                "Common mistakes to avoid",
                "Expert tips",
                "Real-life case study",
                "Product comparison",
                "Myth-busting article",
                "Quick reference guide"
            ]
        }
    
    def generate_content_ideas(self, num_ideas: int = 10) -> List[Dict]:
        """Generate content ideas using AI"""
        prompt = f"""
        Generate {num_ideas} high-quality blog post ideas for a baby sleep tips website. 
        
        Target audience: Parents of babies 0-24 months struggling with sleep issues
        Website focus: Evidence-based, gentle sleep solutions that work
        
        For each idea, provide:
        1. A compelling, SEO-friendly title (60 characters or less)
        2. A brief description of the article
        3. Primary keyword to target
        4. Target age group
        5. Article type (how-to, guide, tips, etc.)
        6. Estimated word count (1500-3000 words)
        
        Focus on:
        - Practical, actionable advice
        - Common sleep problems parents face
        - Gentle, evidence-based methods
        - Age-appropriate content
        - SEO-friendly titles with good search potential
        
        Avoid overly clinical or medical advice.
        
        Format as JSON array with objects containing: title, description, keyword, age_group, article_type, word_count
        """
        
        response = openai.ChatCompletion.create(
            model=self.config['ai']['openai_model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config['ai']['temperature'],
            max_tokens=2000
        )
        
        try:
            ideas = json.loads(response.choices[0].message.content)
            return ideas
        except json.JSONDecodeError:
            print("Failed to parse AI response as JSON")
            return []
    
    def generate_blog_post(self, idea: Dict) -> BlogPost:
        """Generate a complete blog post from an idea"""
        
        # Main content generation prompt
        content_prompt = f"""
        Write a comprehensive, engaging blog post about "{idea['title']}".
        
        Target audience: Parents of {idea.get('age_group', 'babies 0-24 months')}
        Primary keyword: {idea['keyword']}
        Word count target: {idea.get('word_count', 2000)} words
        
        Requirements:
        1. Write in a warm, supportive, and expert tone
        2. Include personal anecdotes and relatable scenarios
        3. Provide specific, actionable steps and tips
        4. Use scientific backing where appropriate (but keep it accessible)
        5. Include real-world examples and case studies
        6. Structure with clear headings and subheadings
        7. Include a compelling introduction and conclusion
        8. Naturally incorporate the primary keyword throughout
        9. Add internal linking opportunities (mention related topics)
        10. Include safety reminders where relevant
        
        Structure:
        - Engaging introduction with a relatable scenario
        - Problem identification and empathy
        - 5-7 main sections with practical solutions
        - Real examples and case studies
        - Common mistakes to avoid
        - When to seek additional help
        - Encouraging conclusion with key takeaways
        
        Write in HTML format with proper headings (h2, h3), paragraphs, and lists.
        Include placeholders for affiliate links like [AFFILIATE: product name].
        """
        
        response = openai.ChatCompletion.create(
            model=self.config['ai']['openai_model'],
            messages=[{"role": "user", "content": content_prompt}],
            temperature=self.config['ai']['temperature'],
            max_tokens=self.config['ai']['max_tokens']
        )
        
        content = response.choices[0].message.content
        
        # Generate meta description
        meta_prompt = f"""
        Create a compelling meta description (150-160 characters) for this blog post:
        Title: {idea['title']}
        Keyword: {idea['keyword']}
        
        The meta description should:
        - Include the primary keyword naturally
        - Be compelling and click-worthy
        - Accurately describe the content value
        - Stay within 150-160 characters
        """
        
        meta_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": meta_prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        meta_description = meta_response.choices[0].message.content.strip()
        
        # Generate excerpt
        excerpt_prompt = f"""
        Create a compelling 2-3 sentence excerpt for this blog post:
        Title: {idea['title']}
        
        The excerpt should hook readers and make them want to read more.
        """
        
        excerpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": excerpt_prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        excerpt = excerpt_response.choices[0].message.content.strip()
        
        # Generate image prompt
        image_prompt = f"""
        Create a detailed image prompt for DALL-E to generate a featured image for this blog post:
        Title: {idea['title']}
        Topic: {idea['description']}
        
        The image should be:
        - Warm and comforting
        - Family-friendly
        - Professional yet approachable
        - Suitable for a baby sleep blog
        - Visually appealing for social media sharing
        
        Describe composition, colors, mood, and specific elements to include.
        """
        
        image_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": image_prompt}],
            temperature=0.8,
            max_tokens=200
        )
        
        featured_image_prompt = image_response.choices[0].message.content.strip()
        
        # Generate affiliate product suggestions
        affiliate_products = self.suggest_affiliate_products(idea['title'], content)
        
        # Create slug
        slug = self.create_slug(idea['title'])
        
        # Extract keywords
        keywords = self.extract_keywords(idea['keyword'], content)
        
        return BlogPost(
            title=idea['title'],
            content=content,
            meta_description=meta_description,
            keywords=keywords,
            featured_image_prompt=featured_image_prompt,
            category=idea.get('article_type', 'Sleep Tips'),
            slug=slug,
            excerpt=excerpt,
            affiliate_products=affiliate_products
        )
    
    def suggest_affiliate_products(self, title: str, content: str) -> List[Dict]:
        """Suggest relevant affiliate products for the post"""
        prompt = f"""
        Based on this blog post title and content, suggest 3-5 relevant baby sleep products that would be helpful for parents reading this article.
        
        Title: {title}
        Content preview: {content[:500]}...
        
        For each product, suggest:
        1. Product category (e.g., "white noise machine", "sleep sack", "crib")
        2. Specific product features to mention
        3. Why it's relevant to this article
        4. Where in the article it should be mentioned
        
        Focus on products available on Amazon that would genuinely help with the sleep issues discussed.
        
        Format as JSON array with objects containing: category, features, relevance, placement
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        try:
            products = json.loads(response.choices[0].message.content)
            return products
        except json.JSONDecodeError:
            return []
    
    def create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def extract_keywords(self, primary_keyword: str, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        keywords = [primary_keyword]
        
        # Add related keywords from config
        for keyword in self.config['seo']['primary_keywords']:
            if keyword.lower() in content.lower():
                keywords.append(keyword)
        
        for keyword in self.config['seo']['long_tail_keywords']:
            if keyword.lower() in content.lower():
                keywords.append(keyword)
        
        return list(set(keywords))
    
    def save_blog_post(self, post: BlogPost) -> str:
        """Save blog post to markdown file"""
        timestamp = datetime.datetime.now()
        filename = f"{timestamp.strftime('%Y-%m-%d')}-{post.slug}.md"
        filepath = Path(f"/workspace/content/posts/{filename}")
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create frontmatter
        frontmatter = {
            'title': post.title,
            'slug': post.slug,
            'date': timestamp.isoformat(),
            'description': post.meta_description,
            'keywords': post.keywords,
            'category': post.category,
            'featured_image_prompt': post.featured_image_prompt,
            'excerpt': post.excerpt,
            'affiliate_products': post.affiliate_products,
            'author': self.config['site']['author'],
            'draft': False
        }
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('---\n')
            yaml.dump(frontmatter, f, default_flow_style=False)
            f.write('---\n\n')
            f.write(post.content)
        
        return str(filepath)
    
    def generate_batch_content(self, num_posts: int = 3) -> List[str]:
        """Generate a batch of blog posts"""
        print(f"Generating {num_posts} blog post ideas...")
        ideas = self.generate_content_ideas(num_posts)
        
        if not ideas:
            print("Failed to generate content ideas")
            return []
        
        generated_files = []
        
        for i, idea in enumerate(ideas, 1):
            print(f"\nGenerating post {i}/{len(ideas)}: {idea['title']}")
            
            try:
                post = self.generate_blog_post(idea)
                filepath = self.save_blog_post(post)
                generated_files.append(filepath)
                print(f"✓ Saved: {filepath}")
                
            except Exception as e:
                print(f"✗ Error generating post: {e}")
                continue
        
        print(f"\n🎉 Successfully generated {len(generated_files)} blog posts!")
        return generated_files

def main():
    """Main function to run content generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate AI-powered baby sleep blog content')
    parser.add_argument('--posts', type=int, default=3, help='Number of posts to generate')
    parser.add_argument('--config', default='/workspace/config/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    generator = BabySleepContentGenerator(args.config)
    generator.generate_batch_content(args.posts)

if __name__ == "__main__":
    main()