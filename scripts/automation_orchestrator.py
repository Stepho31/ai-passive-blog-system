#!/usr/bin/env python3
"""
Main Automation Orchestrator for Baby Sleep Blog
Coordinates all automation systems: content generation, SEO, monetization, and social media
"""

import os
import json
import yaml
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Import our modules
from content_generator import BabySleepContentGenerator
from affiliate_manager import AffiliateManager
from social_automation import SocialMediaAutomator
from seo_optimizer import SEOOptimizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/automation.log'),
        logging.StreamHandler()
    ]
)

class BlogAutomationOrchestrator:
    def __init__(self, config_path: str = "/workspace/config/config.yaml"):
        self.config = self.load_config(config_path)
        self.setup_components()
        self.ensure_directories()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def setup_components(self):
        """Initialize all automation components"""
        try:
            self.content_generator = BabySleepContentGenerator()
            self.affiliate_manager = AffiliateManager()
            self.social_automator = SocialMediaAutomator()
            self.seo_optimizer = SEOOptimizer()
            logging.info("✓ All automation components initialized successfully")
        except Exception as e:
            logging.error(f"✗ Failed to initialize components: {e}")
            raise
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            "/workspace/content/posts",
            "/workspace/static/images", 
            "/workspace/logs",
            "/workspace/data",
            "/workspace/output"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def load_existing_posts(self) -> List[Dict]:
        """Load existing blog posts from the content directory"""
        posts = []
        content_dir = Path("/workspace/content/posts")
        
        for md_file in content_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        post_content = parts[2].strip()
                        
                        frontmatter['content'] = post_content
                        frontmatter['filename'] = md_file.name
                        posts.append(frontmatter)
                        
            except Exception as e:
                logging.warning(f"Failed to load post {md_file}: {e}")
        
        return posts
    
    def generate_daily_content(self):
        """Generate daily blog content"""
        try:
            logging.info("🚀 Starting daily content generation...")
            
            # Generate new blog posts
            num_posts = self.config['content']['posts_per_batch']
            generated_files = self.content_generator.generate_batch_content(num_posts)
            
            if not generated_files:
                logging.warning("No content generated today")
                return
            
            # Load and process the generated posts
            existing_posts = self.load_existing_posts()
            processed_posts = []
            
            for filepath in generated_files:
                try:
                    # Load the generated post
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        frontmatter = yaml.safe_load(parts[1])
                        post_content = parts[2].strip()
                        frontmatter['content'] = post_content
                    
                    # SEO optimization
                    optimized_post, seo_analysis = self.seo_optimizer.optimize_content(
                        frontmatter, existing_posts
                    )
                    
                    # Monetization (affiliate links, ads, email capture)
                    monetized_content, monetization_report = self.affiliate_manager.process_content(
                        optimized_post['content']
                    )
                    optimized_post['content'] = monetized_content
                    
                    # Save optimized post
                    self.save_optimized_post(filepath, optimized_post)
                    
                    processed_posts.append(optimized_post)
                    
                    logging.info(f"✓ Processed post: {optimized_post['title']}")
                    logging.info(f"  SEO Score: {seo_analysis.seo_score}/100")
                    logging.info(f"  Affiliate Links: {len(monetization_report['affiliate_links'])}")
                    
                except Exception as e:
                    logging.error(f"✗ Failed to process {filepath}: {e}")
            
            # Schedule social media posts
            if processed_posts:
                social_results = self.social_automator.schedule_social_posts(processed_posts)
                logging.info(f"📱 Social media results: {social_results}")
            
            # Update sitemap
            self.update_sitemap()
            
            # Generate performance report
            self.generate_daily_report(processed_posts, social_results if 'social_results' in locals() else {})
            
            logging.info(f"🎉 Daily content generation completed! Generated {len(processed_posts)} posts")
            
        except Exception as e:
            logging.error(f"✗ Daily content generation failed: {e}")
            raise
    
    def save_optimized_post(self, filepath: str, post_data: Dict):
        """Save optimized post back to file"""
        content = post_data.pop('content')
        
        # Create frontmatter
        frontmatter_content = '---\n'
        frontmatter_content += yaml.dump(post_data, default_flow_style=False)
        frontmatter_content += '---\n\n'
        frontmatter_content += content
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter_content)
    
    def update_sitemap(self):
        """Update sitemap with new posts"""
        try:
            posts = self.load_existing_posts()
            sitemap_xml = self.seo_optimizer.generate_sitemap(posts)
            
            # Save sitemap
            with open('/workspace/output/sitemap.xml', 'w') as f:
                f.write(sitemap_xml)
            
            # Generate robots.txt
            robots_txt = self.seo_optimizer.generate_robots_txt()
            with open('/workspace/output/robots.txt', 'w') as f:
                f.write(robots_txt)
            
            logging.info("✓ Sitemap and robots.txt updated")
            
        except Exception as e:
            logging.error(f"✗ Failed to update sitemap: {e}")
    
    def generate_daily_report(self, posts: List[Dict], social_results: Dict):
        """Generate daily automation report"""
        report = {
            'date': datetime.now().isoformat(),
            'posts_generated': len(posts),
            'posts_details': [
                {
                    'title': post['title'],
                    'slug': post['slug'],
                    'word_count': len(post['content'].split()),
                    'keywords': post.get('keywords', [])
                }
                for post in posts
            ],
            'social_media': social_results,
            'total_posts': len(self.load_existing_posts())
        }
        
        # Save report
        report_file = f"/workspace/logs/daily_report_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"📊 Daily report saved: {report_file}")
    
    def weekly_seo_audit(self):
        """Perform weekly SEO audit on all content"""
        try:
            logging.info("🔍 Starting weekly SEO audit...")
            
            posts = self.load_existing_posts()
            audit_results = []
            
            for post in posts:
                seo_analysis = self.seo_optimizer.perform_seo_analysis(
                    post['title'],
                    post['content'],
                    post.get('description', ''),
                    post.get('keywords', [])
                )
                
                audit_results.append({
                    'title': post['title'],
                    'slug': post['slug'],
                    'seo_score': seo_analysis.seo_score,
                    'word_count': seo_analysis.word_count,
                    'issues': self.identify_seo_issues(seo_analysis)
                })
            
            # Save audit report
            audit_report = {
                'date': datetime.now().isoformat(),
                'total_posts': len(posts),
                'average_seo_score': sum(r['seo_score'] for r in audit_results) / len(audit_results) if audit_results else 0,
                'posts': audit_results
            }
            
            audit_file = f"/workspace/logs/seo_audit_{datetime.now().strftime('%Y-%m-%d')}.json"
            with open(audit_file, 'w') as f:
                json.dump(audit_report, f, indent=2)
            
            logging.info(f"📋 SEO audit completed. Average score: {audit_report['average_seo_score']:.1f}/100")
            
        except Exception as e:
            logging.error(f"✗ Weekly SEO audit failed: {e}")
    
    def identify_seo_issues(self, analysis) -> List[str]:
        """Identify SEO issues from analysis"""
        issues = []
        
        if analysis.title_length > 60:
            issues.append("Title too long")
        elif analysis.title_length < 30:
            issues.append("Title too short")
        
        if analysis.meta_description_length > 160:
            issues.append("Meta description too long")
        elif analysis.meta_description_length < 150:
            issues.append("Meta description too short")
        
        if analysis.word_count < 1000:
            issues.append("Content too short")
        elif analysis.word_count > 4000:
            issues.append("Content too long")
        
        if analysis.h2_count < 2:
            issues.append("Insufficient headings")
        
        if analysis.internal_links < 2:
            issues.append("Insufficient internal links")
        
        if analysis.image_alt_count == 0:
            issues.append("Missing image alt text")
        
        return issues
    
    def social_media_boost(self):
        """Weekly social media boost - create additional pins and posts"""
        try:
            logging.info("📈 Starting weekly social media boost...")
            
            # Get recent posts for promotion
            posts = self.load_existing_posts()
            recent_posts = [p for p in posts if self.is_recent(p.get('date', ''))]
            
            if not recent_posts:
                recent_posts = posts[-3:]  # Last 3 posts if no recent ones
            
            # Create additional social content
            boost_results = self.social_automator.schedule_social_posts(recent_posts)
            
            logging.info(f"📱 Social media boost completed: {boost_results}")
            
        except Exception as e:
            logging.error(f"✗ Social media boost failed: {e}")
    
    def is_recent(self, date_str: str, days: int = 7) -> bool:
        """Check if date is within the last N days"""
        try:
            post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return (datetime.now() - post_date).days <= days
        except:
            return False
    
    def monthly_analytics_report(self):
        """Generate monthly analytics and performance report"""
        try:
            logging.info("📊 Generating monthly analytics report...")
            
            posts = self.load_existing_posts()
            current_month = datetime.now().replace(day=1)
            
            # Filter posts from current month
            monthly_posts = [
                p for p in posts 
                if self.is_from_month(p.get('date', ''), current_month)
            ]
            
            # Calculate metrics
            report = {
                'month': current_month.strftime('%Y-%m'),
                'posts_published': len(monthly_posts),
                'total_posts': len(posts),
                'average_word_count': sum(len(p['content'].split()) for p in monthly_posts) / len(monthly_posts) if monthly_posts else 0,
                'most_popular_keywords': self.get_popular_keywords(monthly_posts),
                'monetization_summary': self.get_monetization_summary(),
                'next_month_goals': self.generate_next_month_goals(monthly_posts)
            }
            
            # Save report
            report_file = f"/workspace/logs/monthly_report_{current_month.strftime('%Y-%m')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logging.info(f"📈 Monthly report generated: {report_file}")
            
        except Exception as e:
            logging.error(f"✗ Monthly analytics report failed: {e}")
    
    def is_from_month(self, date_str: str, target_month: datetime) -> bool:
        """Check if date is from target month"""
        try:
            post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return post_date.year == target_month.year and post_date.month == target_month.month
        except:
            return False
    
    def get_popular_keywords(self, posts: List[Dict]) -> List[str]:
        """Get most popular keywords from posts"""
        keyword_count = {}
        
        for post in posts:
            for keyword in post.get('keywords', []):
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # Return top 10 keywords
        return sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def get_monetization_summary(self) -> Dict:
        """Get monetization summary (placeholder for analytics integration)"""
        return {
            'estimated_ad_revenue': '$50-150',
            'affiliate_clicks': '250-500', 
            'email_signups': '25-75',
            'note': 'Actual metrics require Google Analytics and affiliate dashboard integration'
        }
    
    def generate_next_month_goals(self, monthly_posts: List[Dict]) -> Dict:
        """Generate goals for next month"""
        current_posts = len(monthly_posts)
        target_posts = max(15, current_posts + 5)
        
        return {
            'content_goals': {
                'target_posts': target_posts,
                'focus_keywords': ['sleep regression', 'newborn schedule', 'gentle methods'],
                'content_types': ['how-to guides', 'troubleshooting', 'age-specific tips']
            },
            'seo_goals': {
                'target_seo_score': 85,
                'internal_linking_expansion': True,
                'keyword_optimization': True
            },
            'monetization_goals': {
                'new_affiliate_partnerships': 2,
                'email_list_growth': '20%',
                'ad_revenue_optimization': True
            }
        }
    
    def setup_automation_schedule(self):
        """Setup the automation schedule"""
        logging.info("⏰ Setting up automation schedule...")
        
        # Daily content generation
        schedule.every().day.at("06:00").do(self.generate_daily_content)
        
        # Weekly SEO audit
        schedule.every().sunday.at("08:00").do(self.weekly_seo_audit)
        
        # Weekly social media boost
        schedule.every().wednesday.at("10:00").do(self.social_media_boost)
        
        # Monthly analytics report
        schedule.every().month.do(self.monthly_analytics_report)
        
        logging.info("✓ Automation schedule configured")
    
    def run_automation(self):
        """Run the automation system"""
        logging.info("🤖 Starting blog automation system...")
        
        self.setup_automation_schedule()
        
        # Run initial content generation
        logging.info("🚀 Running initial content generation...")
        self.generate_daily_content()
        
        # Main automation loop
        logging.info("🔄 Entering automation loop...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
            except KeyboardInterrupt:
                logging.info("🛑 Automation stopped by user")
                break
            except Exception as e:
                logging.error(f"✗ Automation error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def run_once(self):
        """Run automation once (for testing or manual execution)"""
        logging.info("🔧 Running automation once...")
        self.generate_daily_content()
        self.update_sitemap()
        logging.info("✅ Single automation run completed")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Baby Sleep Blog Automation')
    parser.add_argument('--mode', choices=['run', 'once', 'seo-audit'], default='once',
                       help='Automation mode')
    parser.add_argument('--config', default='/workspace/config/config.yaml',
                       help='Config file path')
    
    args = parser.parse_args()
    
    orchestrator = BlogAutomationOrchestrator(args.config)
    
    if args.mode == 'run':
        orchestrator.run_automation()
    elif args.mode == 'once':
        orchestrator.run_once()
    elif args.mode == 'seo-audit':
        orchestrator.weekly_seo_audit()

if __name__ == "__main__":
    main()