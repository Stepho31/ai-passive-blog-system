#!/usr/bin/env python3
"""
Affiliate Link Management System for Baby Sleep Blog
Automatically inserts affiliate links and manages monetization
"""

import re
import json
import yaml
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode
import hashlib

@dataclass
class AffiliateProduct:
    name: str
    category: str
    amazon_asin: str
    clickbank_id: str
    price_range: str
    description: str
    keywords: List[str]
    amazon_url: str
    clickbank_url: str

class AffiliateManager:
    def __init__(self, config_path: str = "/workspace/config/config.yaml"):
        self.config = self.load_config(config_path)
        self.products = self.load_affiliate_products()
        self.amazon_associate_id = self.config['monetization']['amazon_associates']['associate_id']
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def load_affiliate_products(self) -> List[AffiliateProduct]:
        """Load affiliate product database"""
        products_data = [
            {
                "name": "Hatch Baby Rest Sound Machine",
                "category": "sound_machine",
                "amazon_asin": "B078K2XMJY",
                "clickbank_id": "",
                "price_range": "$60-80",
                "description": "Smart sound machine with app control and night light",
                "keywords": ["sound machine", "white noise", "night light", "sleep environment"],
                "amazon_url": "https://amazon.com/dp/B078K2XMJY",
                "clickbank_url": ""
            },
            {
                "name": "Baby Sleep Miracle Guide",
                "category": "sleep_guide",
                "amazon_asin": "",
                "clickbank_id": "babysleep1",
                "price_range": "$37-47",
                "description": "Complete baby sleep training system by clinical psychologist",
                "keywords": ["sleep training", "sleep guide", "baby sleep method", "sleep schedule"],
                "amazon_url": "",
                "clickbank_url": "https://babysleep.com/special-offer"
            },
            {
                "name": "Nested Bean Zen Sack Sleep Sack",
                "category": "sleep_sack",
                "amazon_asin": "B07QKZJ8Q1",
                "clickbank_id": "",
                "price_range": "$30-40",
                "description": "Weighted sleep sack that mimics parent's touch",
                "keywords": ["sleep sack", "swaddle", "weighted", "safe sleep"],
                "amazon_url": "https://amazon.com/dp/B07QKZJ8Q1",
                "clickbank_url": ""
            },
            {
                "name": "Owlet Smart Sock 3",
                "category": "baby_monitor",
                "amazon_asin": "B077QNZ5DG",
                "clickbank_id": "",
                "price_range": "$250-300",
                "description": "Smart baby monitor that tracks heart rate and oxygen",
                "keywords": ["baby monitor", "smart sock", "heart rate", "peace of mind"],
                "amazon_url": "https://amazon.com/dp/B077QNZ5DG",
                "clickbank_url": ""
            },
            {
                "name": "The Happy Sleeper Book",
                "category": "sleep_book",
                "amazon_asin": "0143108808",
                "clickbank_id": "",
                "price_range": "$15-20",
                "description": "Evidence-based approach to baby and toddler sleep",
                "keywords": ["sleep book", "sleep training book", "gentle methods"],
                "amazon_url": "https://amazon.com/dp/0143108808",
                "clickbank_url": ""
            },
            {
                "name": "Blackout Curtains for Nursery",
                "category": "room_darkening",
                "amazon_asin": "B07GXZQ8VG",
                "clickbank_id": "",
                "price_range": "$25-35",
                "description": "Room darkening curtains for better baby sleep",
                "keywords": ["blackout curtains", "room darkening", "sleep environment"],
                "amazon_url": "https://amazon.com/dp/B07GXZQ8VG",
                "clickbank_url": ""
            },
            {
                "name": "Baby Shusher Sleep Miracle",
                "category": "sound_machine",
                "amazon_asin": "B00D2JN87I",
                "clickbank_id": "",
                "price_range": "$35-45",
                "description": "Rhythmic shushing sound to soothe babies to sleep",
                "keywords": ["shusher", "soothing sounds", "baby sleep aid"],
                "amazon_url": "https://amazon.com/dp/B00D2JN87I",
                "clickbank_url": ""
            },
            {
                "name": "Marpac Dohm White Noise Machine",
                "category": "sound_machine",
                "amazon_asin": "B000KUHFGM",
                "clickbank_id": "",
                "price_range": "$45-55",
                "description": "Natural white noise machine with adjustable tone",
                "keywords": ["white noise machine", "natural sound", "sleep machine"],
                "amazon_url": "https://amazon.com/dp/B000KUHFGM",
                "clickbank_url": ""
            }
        ]
        
        return [AffiliateProduct(**product) for product in products_data]
    
    def generate_amazon_link(self, asin: str, keyword: str = "") -> str:
        """Generate Amazon affiliate link with tracking"""
        base_url = f"https://www.amazon.com/dp/{asin}"
        
        params = {
            'tag': self.amazon_associate_id,
            'linkCode': 'as2',
            'camp': '1789',
            'creative': '9325'
        }
        
        if keyword:
            params['keywords'] = keyword
        
        return f"{base_url}?{urlencode(params)}"
    
    def generate_clickbank_link(self, product_id: str, tid: str = "") -> str:
        """Generate ClickBank affiliate link"""
        if not tid:
            tid = "default"
        
        return f"https://hop.clickbank.net/?affiliate={self.config['monetization']['affiliate_programs'][0].get('clickbank_id', 'defaultid')}&vendor={product_id}&tid={tid}"
    
    def find_relevant_products(self, content: str, max_products: int = 3) -> List[AffiliateProduct]:
        """Find products relevant to the content"""
        relevant_products = []
        content_lower = content.lower()
        
        for product in self.products:
            relevance_score = 0
            
            # Check if any keywords appear in content
            for keyword in product.keywords:
                if keyword.lower() in content_lower:
                    relevance_score += 1
            
            # Check if category appears in content
            if product.category.replace('_', ' ') in content_lower:
                relevance_score += 2
            
            if relevance_score > 0:
                relevant_products.append((product, relevance_score))
        
        # Sort by relevance and return top products
        relevant_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in relevant_products[:max_products]]
    
    def insert_affiliate_links(self, content: str) -> Tuple[str, List[Dict]]:
        """Insert affiliate links into content and return modified content"""
        relevant_products = self.find_relevant_products(content)
        inserted_links = []
        
        for product in relevant_products:
            # Find appropriate insertion points
            insertion_points = self.find_insertion_points(content, product)
            
            for point in insertion_points:
                # Generate affiliate link
                if product.amazon_asin:
                    link = self.generate_amazon_link(product.amazon_asin, product.keywords[0])
                    link_text = f'<a href="{link}" target="_blank" rel="noopener">{product.name}</a>'
                elif product.clickbank_id:
                    link = self.generate_clickbank_link(product.clickbank_id)
                    link_text = f'<a href="{link}" target="_blank" rel="noopener">{product.name}</a>'
                else:
                    continue
                
                # Insert link at appropriate location
                content = self.insert_link_at_position(content, point, link_text, product)
                
                inserted_links.append({
                    'product': product.name,
                    'category': product.category,
                    'link': link,
                    'position': point
                })
        
        return content, inserted_links
    
    def find_insertion_points(self, content: str, product: AffiliateProduct) -> List[str]:
        """Find appropriate places to insert affiliate links"""
        insertion_points = []
        
        # Look for mentions of keywords
        for keyword in product.keywords:
            pattern = rf'\b{re.escape(keyword)}\b'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                insertion_points.append(match.group())
        
        return insertion_points[:2]  # Limit to 2 insertions per product
    
    def insert_link_at_position(self, content: str, search_term: str, link_text: str, product: AffiliateProduct) -> str:
        """Insert affiliate link at specific position"""
        # Replace first occurrence of search term with linked version
        pattern = rf'\b{re.escape(search_term)}\b'
        
        def replacement(match):
            return link_text
        
        return re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
    
    def add_product_recommendations(self, content: str) -> str:
        """Add product recommendation sections to content"""
        relevant_products = self.find_relevant_products(content, max_products=3)
        
        if not relevant_products:
            return content
        
        recommendation_html = self.generate_recommendation_section(relevant_products)
        
        # Insert before conclusion or at the end
        conclusion_pattern = r'(<h2[^>]*>.*?conclusion.*?</h2>)'
        if re.search(conclusion_pattern, content, re.IGNORECASE):
            content = re.sub(conclusion_pattern, f'{recommendation_html}\n\n\\1', content, flags=re.IGNORECASE)
        else:
            content += f'\n\n{recommendation_html}'
        
        return content
    
    def generate_recommendation_section(self, products: List[AffiliateProduct]) -> str:
        """Generate HTML for product recommendations"""
        html = '''
<div class="product-recommendations">
    <h2>💡 Recommended Products to Help Your Baby Sleep Better</h2>
    <p>Based on the tips in this article, here are some products that many parents find helpful:</p>
    <div class="product-grid">
'''
        
        for product in products:
            if product.amazon_asin:
                link = self.generate_amazon_link(product.amazon_asin)
                platform = "Amazon"
            elif product.clickbank_id:
                link = self.generate_clickbank_link(product.clickbank_id)
                platform = "Get Guide"
            else:
                continue
            
            product_html = f'''
        <div class="product-card">
            <h3>{product.name}</h3>
            <p class="price">{product.price_range}</p>
            <p class="description">{product.description}</p>
            <a href="{link}" class="btn btn-affiliate" target="_blank" rel="noopener">
                View on {platform} →
            </a>
            <small class="affiliate-disclosure">As an Amazon Associate, we earn from qualifying purchases.</small>
        </div>
'''
            html += product_html
        
        html += '''
    </div>
</div>
'''
        return html
    
    def add_email_capture(self, content: str) -> str:
        """Add email capture lead magnet"""
        email_capture_html = '''
<div class="email-capture-box">
    <div class="email-capture-content">
        <h3>🎁 Get Your FREE Baby Sleep Schedule Template</h3>
        <p>Join over 10,000 parents who've downloaded our proven sleep schedule guide. Perfect for babies 0-12 months!</p>
        <form class="email-form" action="/subscribe" method="POST">
            <input type="email" name="email" placeholder="Your email address" required>
            <input type="hidden" name="lead_magnet" value="sleep_schedule_template">
            <button type="submit" class="btn btn-primary">Get My Free Template →</button>
        </form>
        <small>We respect your privacy. Unsubscribe anytime.</small>
    </div>
</div>
'''
        
        # Insert after first section
        h2_pattern = r'(</h2>.*?<p>.*?</p>)'
        if re.search(h2_pattern, content, re.DOTALL):
            content = re.sub(h2_pattern, f'\\1\n\n{email_capture_html}', content, count=1, flags=re.DOTALL)
        
        return content
    
    def add_google_adsense_units(self, content: str) -> str:
        """Add Google AdSense ad units throughout content"""
        if not self.config['monetization']['google_adsense']['enabled']:
            return content
        
        client_id = self.config['monetization']['google_adsense']['client_id']
        
        # In-article ad
        in_article_ad = f'''
<div class="ad-container in-article-ad">
    <ins class="adsbygoogle"
         style="display:block; text-align:center;"
         data-ad-layout="in-article"
         data-ad-format="fluid"
         data-ad-client="{client_id}"
         data-ad-slot="1234567891"></ins>
    <script>
         (adsbygoogle = window.adsbygoogle || []).push({{}});
    </script>
</div>
'''
        
        # Insert after 2nd paragraph
        paragraphs = content.split('</p>')
        if len(paragraphs) >= 3:
            paragraphs.insert(2, f'{in_article_ad}</p>')
            content = '</p>'.join(paragraphs)
        
        return content
    
    def process_content(self, content: str) -> Tuple[str, Dict]:
        """Process content with all monetization features"""
        # Track what was added
        monetization_report = {
            'affiliate_links': [],
            'email_captures': 0,
            'ad_units': 0,
            'product_recommendations': 0
        }
        
        # Add affiliate links
        content, affiliate_links = self.insert_affiliate_links(content)
        monetization_report['affiliate_links'] = affiliate_links
        
        # Add product recommendations
        original_length = len(content)
        content = self.add_product_recommendations(content)
        if len(content) > original_length:
            monetization_report['product_recommendations'] = 1
        
        # Add email capture
        original_length = len(content)
        content = self.add_email_capture(content)
        if len(content) > original_length:
            monetization_report['email_captures'] = 1
        
        # Add AdSense units
        original_length = len(content)
        content = self.add_google_adsense_units(content)
        if len(content) > original_length:
            monetization_report['ad_units'] = 1
        
        return content, monetization_report

def main():
    """Test the affiliate manager"""
    manager = AffiliateManager()
    
    # Test content
    test_content = """
    <h2>Creating the Perfect Sleep Environment</h2>
    <p>A white noise machine can help mask household sounds that might wake your baby. 
    Many parents find that blackout curtains are essential for daytime naps.</p>
    
    <h2>Sleep Training Methods</h2>
    <p>There are many gentle sleep training approaches. A good sleep guide can help you 
    choose the right method for your family.</p>
    """
    
    processed_content, report = manager.process_content(test_content)
    
    print("=== MONETIZATION REPORT ===")
    print(json.dumps(report, indent=2))
    print("\n=== PROCESSED CONTENT ===")
    print(processed_content)

if __name__ == "__main__":
    main()