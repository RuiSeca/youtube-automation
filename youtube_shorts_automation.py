"""
YouTube Shorts Content Automation System
=========================================
This system automates the end-to-end process of creating YouTube Shorts:
1. Dynamic content research and script generation optimized for Shorts
2. Voice narration generation (brief and engaging)
3. Vertical video assembly with relevant visuals
4. Thumbnail creation for Shorts
5. Upload and optimization with Shorts-specific tags

Features:
- Seamless API and template-based content generation
- Advanced error handling and recovery
- Self-improving content selection
- Performance tracking and analytics
- Optimized for YouTube Shorts algorithm
- Voice selection for narration
- Expanded title templates for more variety
"""

import os
import json
import time
import random
import requests
import subprocess
import re
import sys
import shutil
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class YouTubeShortsAutomationSystem:
    def __init__(self, config_path="config.json"):
        """Initialize the YouTube Shorts automation system with configuration."""
        self.load_config(config_path)
        self.setup_directories()
        self.load_api_keys()
        
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            print("Configuration loaded successfully.")
            
            # Ensure shorts_mode is always true
            self.config["shorts_mode"] = True
            
            # If shorts_settings doesn't exist, create it with default values
            if "shorts_settings" not in self.config:
                self.config["shorts_settings"] = {
                    "enabled": True,
                    "max_duration": 60,
                    "vertical_format": True,
                    "fast_paced": True
                }
            else:
                # Make sure enabled is True
                self.config["shorts_settings"]["enabled"] = True
            
            # Set video_length to short for Shorts
            self.config["video_length"] = "short"
            
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Creating default config.")
            self.config = {
                "content_types": ["how_to", "top_10", "explainer"],
                "video_length": "short",  # short for Shorts
                "target_audience": "general",
                "style": "engaging",  # More engaging style for Shorts
                "upload_schedule": {
                    "frequency": "daily",  # daily, weekly, biweekly
                    "time": "15:00"
                },
                "directories": {
                    "scripts": "scripts",
                    "audio": "audio",
                    "video": "video",
                    "thumbnails": "thumbnails",
                    "output": "output",
                    "analytics": "analytics"
                },
                "api_settings": {
                    "retry_attempts": 3,
                    "use_api_quota": 0.8,  # Use API for 80% of content, templates for 20%
                    "preferred_model": "gpt-3.5-turbo"  # Cheaper model as default
                },
                "shorts_mode": True,  # Always True for Shorts
                "shorts_settings": {
                    "enabled": True,
                    "max_duration": 60,  # Maximum 60 seconds for Shorts
                    "vertical_format": True,  # Vertical format for Shorts
                    "fast_paced": True  # Fast-paced editing for Shorts
                }
            }
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
    
    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        for dir_name in self.config["directories"].values():
            os.makedirs(dir_name, exist_ok=True)
        print("Directories setup complete.")
    
    def load_api_keys(self):
        """Load API keys from environment variables."""
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "elevenlabs": os.getenv("ELEVENLABS_API_KEY"),
            "pexels": os.getenv("PEXELS_API_KEY"),
            "youtube": os.getenv("YOUTUBE_API_KEY")
        }
        
        # Check if all required keys are available
        missing_keys = [key for key, value in self.api_keys.items() if not value]
        if missing_keys:
            print(f"Warning: Missing API keys for: {', '.join(missing_keys)}")
    
    # ======== DYNAMIC CONTENT GENERATION SYSTEM ========
    
    def generate_content_ideas(self, niche, count=5):
        """
        Generate content ideas based on the specified niche.
        This is the main entry point that uses the enhanced dynamic content system.
        Optimized for YouTube Shorts.
        """
        # Use our dynamic content generator for seamless API and template integration
        ideas = self.get_dynamic_content_ideas(niche, count=count)
        
        if not ideas:
            print("Warning: Could not generate any content ideas.")
            return []
        
        print(f"Successfully generated {len(ideas)} Shorts content ideas.")
        return ideas
    
    def get_dynamic_content_ideas(self, niche, count=5, use_api=True):
        """
        Enhanced content generation system that seamlessly combines API and template-based approaches.
        Optimized for YouTube Shorts.
        
        Args:
            niche (str): The content niche
            count (int): Number of ideas to generate
            use_api (bool): Whether to attempt API generation first
            
        Returns:
            list: A list of content idea dictionaries
        """
        all_ideas = []
        api_success = False
        
        # PART 1: API GENERATION WITH SMART FALLBACK
        if use_api and self.api_keys["openai"]:
            # Try multiple models in order of cost-effectiveness
            models_to_try = ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]
            
            for model in models_to_try:
                # Skip if we already have enough ideas
                if len(all_ideas) >= count:
                    break
                    
                try:
                    # Calculate how many more ideas we need
                    remaining_count = count - len(all_ideas)
                    print(f"Attempting to generate {remaining_count} ideas with {model}")
                    
                    # Enhance the prompt with specific instructions for the niche AND for Shorts
                    prompt = self._create_enhanced_prompt(niche, remaining_count)
                    
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_keys['openai']}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7
                        },
                        timeout=60  # Increased from 30 to 60 seconds
                    )
                    
                    if response.status_code == 200:
                        raw_content = response.json()["choices"][0]["message"]["content"]
                        print(f"Raw response from {model} received.")
                        
                        # Advanced error handling for JSON parsing
                        try:
                            ideas = json.loads(raw_content)
                            
                            # Validate each idea has required fields
                            valid_ideas = []
                            for idea in ideas:
                                if all(key in idea for key in ["title", "description", "key_points", "keywords"]):
                                    # Ensure key_points is a list
                                    if isinstance(idea["key_points"], list) and len(idea["key_points"]) > 0:
                                        valid_ideas.append(idea)
                                    else:
                                        # Fix key_points if it's not a list
                                        if isinstance(idea["key_points"], str):
                                            idea["key_points"] = [item.strip() for item in idea["key_points"].split(',')]
                                            valid_ideas.append(idea)
                            
                            # Add valid ideas to our collection
                            all_ideas.extend(valid_ideas)
                            print(f"Successfully generated {len(valid_ideas)} Shorts content ideas with {model}")
                            
                            if len(valid_ideas) > 0:
                                api_success = True
                            
                            # If we have enough ideas, break the loop
                            if len(all_ideas) >= count:
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSON from {model}: {str(e)}")
                            # Try to extract JSON if it exists in the text
                            extracted_ideas = self._extract_json_from_text(raw_content)
                            if extracted_ideas:
                                all_ideas.extend(extracted_ideas)
                                api_success = True
                            continue
                    else:
                        print(f"Error with {model}: {response.status_code}")
                        if hasattr(response, 'text'):
                            print(response.text)
                        continue
                
                except Exception as e:
                    print(f"Error with {model}: {str(e)}")
                    continue
        
        # PART 2: TEMPLATE-BASED GENERATION (Used for remaining ideas or if API failed)
        remaining_count = count - len(all_ideas)
        if remaining_count > 0:
            if api_success:
                print(f"API generation partial success. Generating {remaining_count} more ideas from templates.")
            else:
                print(f"API generation failed. Using template system for all {count} ideas.")
            
            # Get template-based ideas
            template_ideas = self._generate_template_ideas(niche, remaining_count)
            all_ideas.extend(template_ideas)
        
        # PART 3: DIVERSIFICATION AND ENHANCEMENT
        # Make sure ideas are diverse and well-formatted
        all_ideas = self._diversify_ideas(all_ideas, niche)
        
        # PART 4: OPTIMIZE FOR SHORTS
        all_ideas = self._optimize_for_shorts(all_ideas)
        
        # Limit to requested count
        return all_ideas[:count]
    
    def _create_enhanced_prompt(self, niche, count):
        """Create a detailed prompt tailored to the specific niche and optimized for Shorts."""
        # Base prompt - optimized for Shorts content
        base_prompt = f"""
        Generate {count} YouTube Shorts ideas for the {niche} niche.
        
        These MUST be optimized for YouTube Shorts:
        - Short, attention-grabbing content (under 60 seconds)
        - Vertical format videos
        - Hook viewers in the first 3 seconds
        - Engaging and fast-paced
        - Clear and concise information
        
        Return a simple JSON array with idea objects. Each object should have:
        - "title": A catchy, engaging title (less than 50 characters)
        - "description": A 1-2 sentence description (very concise)
        - "key_points": A list of 2-3 key points to cover as strings (each point must be brief)
        - "keywords": A list of 4-6 relevant keywords as strings
        
        Keep the format very simple and valid JSON. For example:
        [
            {{
                "title": "Example Shorts Title",
                "description": "Short description here",
                "key_points": ["Quick point 1", "Quick point 2", "Quick point 3"],
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
            }}
        ]
        
        Make sure all ideas are factually accurate, highly engaging, and can be communicated in under 60 seconds.
        Focus on trending topics, quick tips, or surprising facts that work well in short-form content.
        """
        
        # Add niche-specific instructions
        niche_lower = niche.lower()
        
        if any(term in niche_lower for term in ["finance", "money", "invest", "trading", "fintech", "crypto", "wealth"]):
            base_prompt += """
            For these finance-related Shorts:
            - Include quick, actionable finance tips
            - Use striking statistics or numbers
            - Present one clear financial insight per Short
            - Make complex topics simple and digestible
            - Focus on "did you know" or "financial hacks" angles
            """
        
        elif any(term in niche_lower for term in ["tech", "technology", "software", "digital", "ai", "programming"]):
            base_prompt += """
            For these technology-related Shorts:
            - Showcase quick tech tips or shortcuts
            - Reveal lesser-known features
            - Compare tech solutions in seconds
            - Demonstrate "before and after" tech applications
            - Use visually striking tech demonstrations
            """
        
        elif any(term in niche_lower for term in ["health", "fitness", "exercise", "workout", "diet"]):
            base_prompt += """
            For these health/fitness-related Shorts:
            - Focus on quick workout moves or health tips
            - Include impressive before/after transformations
            - Highlight common health myths to debunk
            - Use motivational hooks
            - Make complex health concepts simple and actionable
            """
            
        elif any(term in niche_lower for term in ["food", "cooking", "recipe", "baking", "kitchen"]):
            base_prompt += """
            For these food-related Shorts:
            - Focus on quick recipes or cooking hacks
            - Show dramatic food transformations
            - Include unique flavor combinations
            - Emphasize time-saving techniques
            - Use vibrant visuals and mouth-watering descriptions
            """
        
        # Add time-awareness
        current_month = datetime.now().strftime("%B")
        current_year = datetime.now().year
        base_prompt += f"""
        Since it's currently {current_month} {current_year}, consider:
        - Current tech/finance trends that are viral on social media
        - Seasonal relevance for short-form content
        - Trending hashtags that could be incorporated
        """
        
        # Add Shorts-specific guidance
        base_prompt += """
        Remember these YouTube Shorts best practices:
        - Start with an immediate hook
        - Focus on one main idea per Short
        - Use questions, challenges, or surprising facts to engage viewers
        - Keep language simple and direct
        - End with a clear call-to-action
        """
        
        return base_prompt
    
    def _generate_template_ideas(self, niche, count):
        """Generate ideas based on templates, with variations to ensure uniqueness. Optimized for Shorts."""
        # Normalize the niche
        niche_lower = niche.lower()
        
        # Define template structures with variations optimized for Shorts
        title_templates = [
            "{n} {adj} {niche} Tips in 60 Seconds",
            "Did You Know This About {niche}?",
            "Why Your {niche} Strategy Is Wrong",
            "This {niche} Hack Will Surprise You",
            "{verb} Your {niche} in Seconds",
            "The {niche} Secret No One Tells You",
            "{niche} Myth Busted!",
            "Try This {niche} Trick Today",
            "You're Doing {niche} Wrong! Here's Why",
            "The {adj} Truth About {niche}",
            # Additional templates
            "How to {verb} Your {niche} Today",
            "The {adj} {niche} Guide You Need",
            "What No One Tells You About {niche}",
            "{niche} Facts That Will Blow Your Mind",
            "Stop Making These {niche} Mistakes",
            "The Most {adj} {niche} Tips Ever",
            "{niche} Hacks You Can't Miss",
            "Transform Your {niche} with This One Trick",
            "I Tried This {niche} Method and...",
            "Why Most {niche} Advice Fails",
            "One {niche} Secret That Changed Everything",
            "The Fastest Way to {verb} Your {niche}",
            "Never Do This With Your {niche}",
            "This {niche} Trick Saved Me Hours",
            "{n} Seconds to Better {niche} Results"
        ]
        
        # Elements to fill templates - expanded with more variations
        elements = {
            "n": [3, 5, 7, 10, "These", "Top", "Best", "Secret", "Quick", "Proven", "Essential", "Simple"],
            "adj": ["Secret", "Quick", "Game-Changing", "Hidden", "Shocking", "Amazing", "Incredible", 
                   "Mind-Blowing", "Powerful", "Effective", "Simple", "Easy", "Ultimate", "Essential",
                   "Surprising", "Unbelievable", "Proven", "Brilliant", "Perfect", "Instant"],
            "verb": ["Transform", "Boost", "Hack", "Upgrade", "Fix", "Master", "Improve", "Optimize", 
                    "Revolutionize", "Supercharge", "Simplify", "Accelerate", "Enhance", "Perfect",
                    "Maximize", "Double", "Unlock", "Elevate", "Streamline", "Conquer"],
            "noun": ["Strategy", "Technique", "Method", "Approach", "Hack", "Trick", "Secret", "System", 
                    "Formula", "Blueprint", "Framework", "Process", "Solution", "Principle", "Rule",
                    "Guide", "Plan", "Shortcut", "Roadmap", "Protocol"]
        }
        
        # Finance-specific templates
        finance_templates = [
            "The {niche} Rule Nobody Follows",
            "This {niche} Mistake Costs You Money",
            "How To {verb} Your {niche} Today",
            "Save Money With This {niche} Trick",
            "{n} Seconds To Better {niche} Results",
            # Additional finance templates
            "The {niche} Strategy Millionaires Use",
            "Double Your {niche} Returns With This",
            "The {niche} Trick Banks Don't Want You To Know",
            "How I Fixed My {niche} In One Day",
            "{niche} Red Flags You're Ignoring",
            "The {adj} {niche} Strategy for Beginners",
            "Why Your {niche} Is Failing (And How to Fix It)",
            "Passive {niche} Secrets Revealed",
            "The {n} {niche} Rules You Must Follow",
            "The Only {niche} Advice You'll Ever Need",
            "This One {niche} Mistake Could Cost You Thousands",
            "How to {verb} Your {niche} Portfolio in Minutes",
            "I Tried This {niche} Hack and Made $500",
            "The Easiest Way to {verb} Your {niche}",
            "The {niche} Secret Wall Street Doesn't Share"
        ]
        
        # Tech-specific templates
        tech_templates = [
            "This {niche} Shortcut Will Save You Hours",
            "The {niche} Feature You Never Knew Existed",
            "Try This {niche} Setting Right Now",
            "Update Your {niche} Settings Immediately",
            "The Future of {niche} Is Already Here",
            # Additional tech templates
            "Hidden {niche} Features You Need To Try",
            "This {niche} Trick Makes Everything Faster",
            "The {niche} Hack Developers Don't Tell You",
            "Why Your {niche} Setup Is Wrong",
            "{niche} Settings That Will Change Your Life",
            "The Secret {niche} Menu You Didn't Know About",
            "One {niche} Setting That Changes Everything",
            "Make Your {niche} 10x Faster With This",
            "The {adj} {niche} Shortcut Everyone Missed",
            "How To Enable Hidden {niche} Features",
            "The {adj} {niche} Feature Nobody Uses",
            "I Found a Secret {niche} Code That Does This",
            "Your {niche} Has a Built-in Tool You Never Noticed",
            "The {niche} Algorithm Explained in 60 Seconds",
            "Unlock Advanced {niche} Features With This Trick"
        ]
        
        # Health/fitness templates
        health_templates = [
            "This {niche} Habit Will Transform Your Body",
            "The {adj} {niche} Routine You Need to Try",
            "{n} Second {niche} Exercise That Works",
            "The {niche} Mistake Ruining Your Progress",
            "How I {verb} My {niche} In Just One Week",
            "The {niche} Secret Fitness Pros Use",
            "Try This {niche} Hack for Instant Results",
            "The Only {niche} Move You Need To Know",
            "Your {niche} Routine Is Wrong - Here's Why",
            "The {niche} Myth That's Holding You Back",
            "I Tried This {niche} Trick for 7 Days...",
            "The Morning {niche} Habit That Changed Everything",
            "This One {niche} Move Targets All Muscles",
            "Why Most {niche} Advice Is Actually Harmful",
            "How to {verb} Your {niche} Without Equipment"
        ]
        
        # Food/cooking templates
        food_templates = [
            "The {adj} {niche} Recipe Under 60 Seconds",
            "This {niche} Hack Will Change How You Cook",
            "Never Make This {niche} Mistake Again",
            "The {niche} Secret Chefs Don't Tell You",
            "Try This {niche} Trick For Perfect Results",
            "How To {verb} Your {niche} In Seconds",
            "The Only {niche} Technique You Need",
            "{n} {niche} Tips That Will Blow Your Mind",
            "This {niche} Shortcut Saves Hours",
            "The {niche} Hack That Changed My Cooking",
            "I Tried This Viral {niche} Hack...",
            "The Easiest Way to {verb} {niche} Ever",
            "The {niche} Method Professional Chefs Use",
            "Turn Boring {niche} Into Amazing In Seconds",
            "The {adj} {niche} Recipe With Only 3 Ingredients"
        ]
        
        # Select appropriate templates based on niche
        if any(term in niche_lower for term in ["finance", "money", "invest", "trading", "crypto", "wealth"]):
            niche_template_set = title_templates + finance_templates
        elif any(term in niche_lower for term in ["tech", "technology", "software", "digital", "ai", "programming"]):
            niche_template_set = title_templates + tech_templates
        elif any(term in niche_lower for term in ["health", "fitness", "exercise", "workout", "diet"]):
            niche_template_set = title_templates + health_templates
        elif any(term in niche_lower for term in ["food", "cooking", "recipe", "baking", "kitchen"]):
            niche_template_set = title_templates + food_templates
        else:
            niche_template_set = title_templates
        
        # Generate ideas based on templates
        template_ideas = []
        niche_template_set = list(set(niche_template_set))  # Remove duplicates
        
        # Generate until we have enough ideas
        while len(template_ideas) < count:
            # Pick a random template
            template = random.choice(niche_template_set)
            
            # Fill in the template with random elements
            title = template
            for key, values in elements.items():
                if "{" + key + "}" in title:
                    title = title.replace("{" + key + "}", str(random.choice(values)))
            
            # Replace {niche} with the actual niche
            title = title.replace("{niche}", niche)
            
            # Generate description and key points based on the title, optimized for Shorts
            description = self._generate_shorts_description(title, niche)
            key_points = self._generate_shorts_key_points(title, niche)
            keywords = self._generate_keywords(title, niche)
            
            # Create the idea object
            idea = {
                "title": title,
                "description": description,
                "key_points": key_points,
                "keywords": keywords
            }
            
            # Only add if not too similar to existing ideas
            if not self._is_duplicate(idea, template_ideas):
                template_ideas.append(idea)
        
        return template_ideas
    
    def _generate_shorts_description(self, title, niche):
        """Generate a very brief description based on the title, optimized for Shorts."""
        # Simple templates for short descriptions
        description_templates = [
            f"Quick {niche} tip that most people miss. Watch until the end!",
            f"This {niche} hack could save you time and money. #shorts",
            f"The {niche} secret professionals don't want you to know!",
            f"Transform your approach to {niche} in just 60 seconds!",
            f"You won't believe this {niche} fact! Follow for more tips.",
            f"This {niche} trick will change everything. Must try!",
            f"Learn this {niche} technique in under 60 seconds!",
            f"The {niche} hack everyone needs to know. Game-changer!",
            f"I wish I knew this {niche} tip sooner. Don't make my mistake!",
            f"This {niche} method is going viral for a reason. Try it now!",
            f"Secret {niche} strategy revealed in this quick video!",
            f"Most people get {niche} wrong. Here's what to do instead.",
            f"I tested this {niche} hack for a week. The results shocked me!",
            f"This {niche} shortcut saves me hours every week.",
            f"The {niche} tip that changed my life. Not clickbait!"
        ]
        
        # Return a random description
        return random.choice(description_templates)
    
    def _generate_shorts_key_points(self, title, niche):
        """Generate minimal key points based on the title, optimized for Shorts."""
        # For Shorts, we want fewer and more concise key points (2-3 maximum)
        point_starters = [
            "Show the problem",
            "Reveal the solution",
            "Demonstrate the benefit",
            "Compare before/after",
            "Share a surprising fact",
            "Ask a provocative question",
            "Call to action",
            "Highlight common mistake",
            "Show quick implementation",
            "Explain return on investment",
            "Show side-by-side comparison",
            "Reveal insider secret",
            "Share personal experience",
            "Show transformation process",
            "Provide actionable tip"
        ]
        
        # Generate 2-3 key points for Shorts
        num_points = random.randint(2, 3)
        key_points = []
        
        selected_starters = random.sample(point_starters, num_points)
        for starter in selected_starters:
            key_points.append(f"{starter} about {niche}")
        
        return key_points
    
    def _generate_keywords(self, title, niche):
        """Generate relevant keywords based on title and niche, optimized for Shorts."""
        # Base keywords always include the niche and "shorts"
        base_keywords = [niche.lower(), "shorts", "shortsvideo"]
        
        # Add keywords from title (excluding common words)
        common_words = ["the", "to", "a", "an", "in", "on", "for", "of", "and", "that", "with", "how"]
        title_words = [word.lower() for word in title.replace(":", "").replace("-", " ").split() 
                      if word.lower() not in common_words and len(word) > 3]
        
        # Common additional keywords for Shorts
        shorts_keywords = ["tiktok", "viral", "trending", "learning", "quicktips", "howto", 
                          "tutorial", "hack", "tip", "trick", "advice", "quick", "easy"]
        
        # Combine all keywords
        all_keywords = base_keywords + title_words + shorts_keywords
        
        # Select 5-8 unique keywords
        num_keywords = min(random.randint(5, 8), len(all_keywords))
        selected_keywords = []
        
        while len(selected_keywords) < num_keywords and all_keywords:
            keyword = random.choice(all_keywords)
            all_keywords.remove(keyword)
            if keyword not in selected_keywords:
                selected_keywords.append(keyword)
        
        return selected_keywords
    
    def _is_duplicate(self, new_idea, existing_ideas, threshold=0.7):
        """Check if a new idea is too similar to existing ones."""
        if not existing_ideas:
            return False
        
        new_title = new_idea["title"].lower()
        
        for idea in existing_ideas:
            # Compare titles
            existing_title = idea["title"].lower()
            
            # Simple similarity check (can be improved with more sophisticated methods)
            # Count common words
            new_words = set(new_title.split())
            existing_words = set(existing_title.split())
            common_words = new_words.intersection(existing_words)
            
            # Calculate similarity as proportion of common words
            similarity = len(common_words) / min(len(new_words), len(existing_words))
            
            if similarity > threshold:
                return True
        
        return False
    
    def _diversify_ideas(self, ideas, niche):
        """Ensure ideas are diverse and well-formatted."""
        if not ideas:
            return []
        
        # Sort ideas to group similar ones
        sorted_ideas = sorted(ideas, key=lambda x: x["title"])
        
        # Filter out duplicates and enhance remaining ideas
        filtered_ideas = []
        seen_titles = set()
        
        for idea in sorted_ideas:
            # Normalize title for comparison
            norm_title = idea["title"].lower()
            
            # Skip if too similar to existing idea
            if any(self._calc_similarity(norm_title, seen) > 0.7 for seen in seen_titles):
                continue
            
            # Enhance the idea
            enhanced_idea = self._enhance_idea(idea, niche)
            
            # Add to filtered list
            filtered_ideas.append(enhanced_idea)
            seen_titles.add(norm_title)
        
        return filtered_ideas
    
    def _calc_similarity(self, text1, text2):
        """Calculate simple text similarity."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0
        
        common_words = words1.intersection(words2)
        return len(common_words) / min(len(words1), len(words2))
    
    def _enhance_idea(self, idea, niche):
        """Enhance an idea with additional details if needed."""
        # Ensure all required fields exist
        if "title" not in idea:
            idea["title"] = f"Quick {niche} tip"
        
        if "description" not in idea or not idea["description"]:
            idea["description"] = self._generate_shorts_description(idea["title"], niche)
        
        if "key_points" not in idea or not idea["key_points"]:
            idea["key_points"] = self._generate_shorts_key_points(idea["title"], niche)
        elif isinstance(idea["key_points"], str):
            # Convert string to list if needed
            idea["key_points"] = [point.strip() for point in idea["key_points"].split(',')]
        
        if "keywords" not in idea or not idea["keywords"]:
            idea["keywords"] = self._generate_keywords(idea["title"], niche)
        elif isinstance(idea["keywords"], str):
            # Convert string to list if needed
            idea["keywords"] = [kw.strip() for kw in idea["keywords"].split(',')]
        
        # Format title properly
        idea["title"] = self._format_title(idea["title"])
        
        return idea
    
    def _format_title(self, title):
        """Properly format a title with capitalization."""
        # Words that should not be capitalized (unless first word)
        lowercase_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "in", "of"}
        
        words = title.split()
        if not words:
            return ""
        
        # Capitalize first and last word always
        words[0] = words[0].capitalize()
        if len(words) > 1:
            words[-1] = words[-1].capitalize()
        
        # Handle middle words
        for i in range(1, len(words) - 1):
            word = words[i]
            if word.lower() not in lowercase_words:
                words[i] = word.capitalize()
            else:
                words[i] = word.lower()
        
        return " ".join(words)
    
    def _extract_json_from_text(self, text):
        """Try to extract JSON from text that might have additional content."""
        ideas = []
        
        # Try to find JSON array in the text (improved pattern matching)
        try:
            # Look for anything that looks like a JSON array
            matches = re.findall(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            ideas.extend(parsed)
                            print(f"Successfully extracted {len(parsed)} ideas")
                    except:
                        continue
                        
            # If that fails, try to extract individual JSON objects
            if not ideas:
                matches = re.findall(r'\{.*?\}', text, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and 'title' in parsed:
                            ideas.append(parsed)
                    except:
                        continue
        except Exception as e:
            print(f"Could not extract JSON from text: {str(e)}")
        
        return ideas
    
    def _optimize_for_shorts(self, ideas):
        """Optimize content ideas specifically for YouTube Shorts."""
        optimized_ideas = []
        
        for idea in ideas:
            # 1. Ensure title is short and catchy (max 50 chars for Shorts)
            if len(idea["title"]) > 50:
                # Truncate and add ellipsis
                words = idea["title"].split()
                new_title = ""
                for word in words:
                    if len(new_title + " " + word) <= 46:
                        new_title += " " + word if new_title else word
                    else:
                        break
                idea["title"] = new_title + "..."
            
            # 2. Make sure "Shorts" or related term is in keywords
            shorts_related = ["shorts", "shortsvideo", "shortsyoutube", "tiktok", "reels"]
            has_shorts_keyword = any(kw in shorts_related for kw in idea["keywords"])
            
            if not has_shorts_keyword:
                idea["keywords"].append("shorts")
            
            # 3. Limit to max 3 key points for Shorts (keep them short)
            if len(idea["key_points"]) > 3:
                idea["key_points"] = idea["key_points"][:3]
            
            # 4. Make sure description is very concise (Shorts need to be quick)
            if len(idea["description"]) > 100:
                # Truncate long descriptions
                idea["description"] = idea["description"][:97] + "..."
            
            # 5. Add a hook or question if title doesn't have one
            lower_title = idea["title"].lower()
            has_hook = any(q in lower_title for q in ["?", "how", "why", "this", "secret", "try"])
            
            if not has_hook:
                hooks = [
                    f"Did you know this {random.choice(['secret', 'trick', 'hack'])}? ",
                    f"Try this {random.choice(['now', 'today', 'immediately'])}: ",
                    f"You've been doing {random.choice(['it', 'this'])} wrong: "
                ]
                idea["title"] = random.choice(hooks) + idea["title"]
                
                # Check length again after adding hook
                if len(idea["title"]) > 50:
                    idea["title"] = idea["title"][:47] + "..."
            
            optimized_ideas.append(idea)
        
        return optimized_ideas
    
    def _select_best_idea(self, ideas, niche):
        """
        Select the best idea from the list based on quality factors.
        Optimized for Shorts content.
        """
        if not ideas or len(ideas) == 1:
            return ideas[0] if ideas else None
        
        # Score each idea based on Shorts-specific quality factors
        scored_ideas = []
        for idea in ideas:
            score = 0
            
            # 1. Title quality for Shorts (hook, length, engagement)
            title = idea['title']
            
            # Ideal Shorts title length (30-45 chars)
            if 30 <= len(title) <= 45:
                score += 3
            elif len(title) < 30 or len(title) <= 50:
                score += 2
            
            # Check for hooks in title (crucial for Shorts)
            hooks = ["?", "how", "why", "this", "secret", "hack", "try", "!"]
            for hook in hooks:
                if hook in title.lower():
                    score += 2
                    break
            
            # Check for power words in title
            power_words = ["ultimate", "secret", "shocking", "proven", "powerful", 
                          "revealed", "strategy", "fast", "quick"]
            for word in power_words:
                if word in title.lower():
                    score += 1
            
            # 2. Key points quality (brevity is crucial for Shorts)
            key_points = idea['key_points']
            if isinstance(key_points, list):
                # 2-3 points is ideal for Shorts
                if 2 <= len(key_points) <= 3:
                    score += 3
                elif len(key_points) <= 4:
                    score += 1
                
                # Check brevity of points
                avg_point_length = sum(len(str(point)) for point in key_points) / len(key_points) if key_points else 0
                if 10 <= avg_point_length <= 40:  # Ideal length for Shorts points
                    score += 2
            
            # 3. Keyword quality (Shorts-specific)
            keywords = idea['keywords']
            if isinstance(keywords, list):
                # Check for Shorts-specific keywords
                shorts_keywords = ["shorts", "shortsvideo", "tiktok", "trending", "viral"]
                for kw in shorts_keywords:
                    if any(kw in str(keyword).lower() for keyword in keywords):
                        score += 2
                        break
            
            # 4. Description quality (needs to be very brief for Shorts)
            description = idea['description']
            if len(description) <= 80:  # Very concise is best for Shorts
                score += 3
            elif len(description) <= 100:
                score += 1
            
            # 5. Relevance to niche
            niche_words = niche.lower().split()
            relevance_score = 0
            for word in niche_words:
                if word in title.lower():
                    relevance_score += 1
                if any(word in str(kp).lower() for kp in key_points):
                    relevance_score += 0.5
            
            score += min(relevance_score, 3)  # Cap at 3 points
            
            # Save the scored idea
            scored_ideas.append((idea, score))
        
        # Sort by score (highest first) and return the best idea
        scored_ideas.sort(key=lambda x: x[1], reverse=True)
        
        # Get the top idea
        best_idea = scored_ideas[0][0]
        return best_idea
    
    def _record_video_data(self, idea, video_id, niche):
        """Record video data for analytics and learning."""
        # Create analytics directory if it doesn't exist
        analytics_dir = self.config['directories'].get('analytics', 'analytics')
        os.makedirs(analytics_dir, exist_ok=True)
        
        # Load existing data if available
        analytics_file = os.path.join(analytics_dir, "shorts_data.json")
        video_data = []
        
        if os.path.exists(analytics_file):
            try:
                with open(analytics_file, 'r') as f:
                    video_data = json.load(f)
            except Exception as e:
                print(f"Error loading analytics data: {str(e)}")
        
        # Add new video data
        new_data = {
            "video_id": video_id,
            "title": idea["title"],
            "niche": niche,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "keywords": idea["keywords"],
            "stats": {
                "views": 0,
                "likes": 0,
                "comments": 0
            },
            "is_short": True
        }
        
        video_data.append(new_data)
        
        # Save updated data
        try:
            with open(analytics_file, 'w') as f:
                json.dump(video_data, f, indent=4)
        except Exception as e:
            print(f"Error saving analytics data: {str(e)}")
    
    # ======== ENHANCED SCRIPT GENERATION ========
   
    def sanitize_filename(self,filename):
        invalid_chars = [':', '/', '\\', '?', '*', '"', '<', '>', '|', "'"]
        for char in invalid_chars:
            filename = filename.replace(char, '-')
             # Replace ellipsis with just 'etc'
        filename = filename.replace('...', '-etc')
        
        # Limit length for directory names (Windows has path length limitations)
        if len(filename) > 50:
            # Keep first 47 chars and add "-etc"
            filename = filename[:47] + "-etc"
        return filename

    def generate_script(self, idea):
        """Generate a concise script optimized for YouTube Shorts."""
        if not self.api_keys["openai"]:
            print("OpenAI API key missing. Using fallback script generation.")
            return self._generate_fallback_script(idea)
        
        # Try multiple models
        models_to_try = ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]
        max_attempts = self.config.get("api_settings", {}).get("retry_attempts", 3)
        
        for model in models_to_try:
            for attempt in range(max_attempts):
                try:
                    prompt = self._create_shorts_script_prompt(idea)
                    
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_keys['openai']}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7
                        },
                        timeout=60  # Longer timeout for script generation
                    )
                    
                    if response.status_code == 200:
                        script = response.json()["choices"][0]["message"]["content"]
                        
                        # Ensure scripts directory exists
                        os.makedirs(self.config['directories']['scripts'], exist_ok=True)
                        
                        # Sanitize the filename to remove invalid characters
                        safe_title = self.sanitize_filename(idea['title'])
                        script_filename = f"{self.config['directories']['scripts']}/{safe_title.replace(' ', '_')}_Short.txt"
                        
                        with open(script_filename, 'w') as f:
                            f.write(script)
                        
                        print(f"Shorts script generated with {model} and saved to {script_filename}")
                        return {
                            "content": script,
                            "filename": script_filename
                        }
                    else:
                        print(f"Error generating script with {model} (attempt {attempt+1}): {response.status_code}")
                        print(response.text)
                        continue
                        
                except Exception as e:
                    print(f"Error in script generation with {model} (attempt {attempt+1}): {str(e)}")
                    continue
        
        # If all API attempts failed, use fallback script generation
        print("All API attempts for script generation failed. Using fallback method.")
        return self._generate_fallback_script(idea)
    
    def _create_shorts_script_prompt(self, idea):
        """Create a detailed prompt for Shorts script generation."""
        prompt = f"""
        Write a concise YouTube Shorts script for a vertical video titled: "{idea['title']}"
        
        Description: {idea['description']}
        
        Key points to cover (briefly):
        {", ".join(idea['key_points']) if isinstance(idea['key_points'], list) else idea['key_points']}
        
        IMPORTANT REQUIREMENTS:
        1. The script MUST be VERY SHORT (30-60 seconds when spoken)
        2. Start with an attention-grabbing hook in the first 3 seconds
        3. Focus on just 1-2 key points maximum
        4. End with a clear call to action
        5. Use short, punchy sentences optimized for vertical video format
        6. Include visual cues for what should be shown on screen
        
        Format the script with:
        - [TEXT]: On-screen text overlays
        - [VISUAL]: Visual elements to show
        - [NARRATOR]: Spoken parts
        
        The tone should be {self.config['style']} and targeted at {self.config['target_audience']} audience.
        Remember this is for YouTube Shorts - it must be fast-paced, engaging, and get to the point immediately.
        """
        
        return prompt
    
    def _generate_fallback_script(self, idea):
        """Generate a short script when API is unavailable."""
        # Create script filename
        safe_title = self.sanitize_filename(idea['title'])
        script_filename = f"{self.config['directories']['scripts']}/{safe_title.replace(' ', '_')}_Short.txt"
        
        # Generate a very short script for Shorts
        # Hook
        intro = f"""
[TEXT] {idea['title']}

[VISUAL] Eye-catching intro related to {idea['keywords'][0] if idea['keywords'] else 'topic'}

[NARRATOR] Did you know this about {idea['title']}? In just 30 seconds, I'll show you the key insight.
"""
        
        # Main content (just 1-2 points for shorts)
        main_content = ""
        key_points = idea['key_points'] if isinstance(idea['key_points'], list) else [idea['key_points']]
        max_points = min(2, len(key_points))
        
        for i in range(max_points):
            main_content += f"""
[TEXT] {key_points[i].upper() if len(key_points[i]) < 20 else key_points[i][:17].upper() + "..."}

[VISUAL] Show {key_points[i].lower().replace("show", "").replace("demonstrate", "")}

[NARRATOR] {key_points[i]} This is crucial because it directly affects your results.
"""
        
        # Call to action
        conclusion = f"""
[TEXT] Follow for more {idea['keywords'][0] if idea['keywords'] else 'tips'}!

[VISUAL] Your channel handle or logo

[NARRATOR] If you found this helpful, like and follow for more quick {idea['keywords'][0] if idea['keywords'] else 'tips'} just like this!
"""
        
        # Combine all sections
        full_script = intro + main_content + conclusion
        
        # Create scripts directory if it doesn't exist
        os.makedirs(os.path.dirname(script_filename), exist_ok=True)
        
        # Save script to file
        with open(script_filename, 'w') as f:
            f.write(full_script)
        
        print(f"Fallback shorts script generated and saved to {script_filename}")
        return {
            "content": full_script,
            "filename": script_filename
        }
    
    # ======== ENHANCED VOICE NARRATION ========
    
    def get_available_voices(self):
        """Get list of available voices from ElevenLabs API."""
        if not self.api_keys["elevenlabs"]:
            print("ElevenLabs API key missing. Cannot fetch voice list.")
            return []
        
        try:
            response = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": self.api_keys["elevenlabs"]}
            )
            
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                return [{"id": voice["voice_id"], "name": voice["name"]} for voice in voices]
            else:
                print(f"Error fetching voices: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"Error in get_available_voices: {str(e)}")
            return []
    
    def generate_voice_narration(self, script_data, voice_id=None):
        """Convert script to voice narration with error handling and fallback."""
        if not self.api_keys["elevenlabs"]:
            print("ElevenLabs API key missing. Cannot generate voice narration.")
            return None
        
        # Use default voice if none provided
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
        
        # Extract narrator lines from the script
        narrator_lines = []
        for line in script_data["content"].split('\n'):
            if '[NARRATOR]' in line:
                # Extract the text after [NARRATOR]
                narrator_text = line.split('[NARRATOR]')[1].strip()
                narrator_lines.append(narrator_text)
        
        # Check if we found any narrator lines
        if not narrator_lines:
            print("ERROR: No [NARRATOR] lines found in script. Voice narration cannot be generated.")
            print("Script excerpt:", script_data["content"][:500])
            # Try to extract any text as fallback
            fallback_lines = [line.strip() for line in script_data["content"].split('\n') if line.strip()]
            if fallback_lines:
                print("Using fallback text for narration (no [NARRATOR] tags found)")
                narrator_lines = fallback_lines[:20]  # Limit to first 20 lines as a fallback
            else:
                return None
        
        print(f"Found {len(narrator_lines)} narrator lines in script")
        
        full_narration = " ".join(narrator_lines)
        print(f"Total narration length: {len(full_narration)} characters")
        
        # If full narration is too long, split into chunks
        max_chunk_length = 4000  # ElevenLabs limit
        chunks = self._split_into_chunks(full_narration, max_chunk_length)
        print(f"Split narration into {len(chunks)} chunks")
        
        # Process each chunk and combine results
        audio_chunks = []
        for i, chunk in enumerate(chunks):
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"Processing voice chunk {i+1}/{len(chunks)} (attempt {attempt+1}), {len(chunk)} chars")
                    
                    response = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",  # Using provided voice_id
                        headers={
                            "Accept": "audio/mpeg",
                            "Content-Type": "application/json",
                            "xi-api-key": self.api_keys["elevenlabs"]
                        },
                        json={
                            "text": chunk,
                            "model_id": "eleven_monolingual_v1",
                            "voice_settings": {
                                "stability": 0.5,
                                "similarity_boost": 0.5
                            }
                        },
                        timeout=60  # Increase timeout to 60 seconds
                    )
                    
                    if response.status_code == 200:
                        # Check response size to verify it's a valid audio file
                        content_length = len(response.content)
                        print(f"Received audio chunk: {content_length} bytes")
                        
                        if content_length < 1000:  # Suspiciously small audio file
                            print(f"WARNING: Audio chunk {i+1} is suspiciously small ({content_length} bytes)")
                            if attempt < max_attempts - 1:
                                print("Retrying...")
                                continue
                        
                        audio_chunks.append(response.content)
                        break  # Success, exit retry loop
                    else:
                        print(f"Error generating voice chunk {i+1}: {response.status_code}")
                        print(response.text)
                        if attempt < max_attempts - 1:  # Not the last attempt
                            print(f"Retrying...")
                            time.sleep(2)  # Wait before retry
                        
                except Exception as e:
                    print(f"Error in generate_voice_narration chunk {i+1}: {str(e)}")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print(f"Retrying...")
                        time.sleep(2)  # Wait before retry
        
        # If we got all chunks, combine them
        if len(audio_chunks) == len(chunks):
            # Combine audio chunks
            combined_audio = b''.join(audio_chunks)
            
            # Check combined audio size
            combined_size = len(combined_audio)
            print(f"Combined audio size: {combined_size} bytes")
            
            if combined_size < 1000:  # Suspiciously small
                print("WARNING: Combined audio file is suspiciously small. Voice narration may be corrupted.")
            
            # Create audio directory if it doesn't exist
            audio_dir = self.config['directories']['audio']
            os.makedirs(audio_dir, exist_ok=True)
            
            # Save the combined audio file
            audio_filename = script_data["filename"].replace('.txt', '.mp3').replace(
                self.config['directories']['scripts'], 
                self.config['directories']['audio']
            )
            
            with open(audio_filename, 'wb') as f:
                f.write(combined_audio)
            
            print(f"Voice narration generated and saved to {audio_filename}")
            
            # Verify the created audio file
            if os.path.exists(audio_filename):
                file_size = os.path.getsize(audio_filename)
                print(f"Saved audio file size: {file_size} bytes")
                
                if file_size < 1000:  # Suspiciously small
                    print("WARNING: Saved audio file is suspiciously small")
            
            return audio_filename
        else:
            print(f"Failed to generate all voice chunks ({len(audio_chunks)}/{len(chunks)} completed)")
            
            # If we got at least one chunk, save what we have instead of returning None
            if audio_chunks:
                print("Saving partial audio rather than failing completely")
                combined_audio = b''.join(audio_chunks)
                
                # Create audio directory if it doesn't exist
                audio_dir = self.config['directories']['audio']
                os.makedirs(audio_dir, exist_ok=True)
                
                # Save the combined audio file
                audio_filename = script_data["filename"].replace('.txt', '.mp3').replace(
                    self.config['directories']['scripts'], 
                    self.config['directories']['audio']
                )
                
                with open(audio_filename, 'wb') as f:
                    f.write(combined_audio)
                
                print(f"Partial voice narration saved to {audio_filename}")
                return audio_filename
            
            return None
    
    def _split_into_chunks(self, text, max_length):
        """Split text into chunks that don't exceed max_length, preserving sentences."""
        if not text:
            return []
            
        # If the text is already short enough, return it as a single chunk
        if len(text) <= max_length:
            return [text]
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If this sentence would make the chunk too long, start a new chunk
            if len(current_chunk) + len(sentence) + 1 > max_length:
                if current_chunk:  # Only add non-empty chunks
                    chunks.append(current_chunk.strip())
                
                # If a single sentence is longer than max_length, split it into multiple chunks
                if len(sentence) > max_length:
                    # Find the best place to split (at word boundaries)
                    words = sentence.split()
                    temp_chunk = ""
                    
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 > max_length:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            if temp_chunk:
                                temp_chunk += " " + word
                            else:
                                temp_chunk = word
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    # ======== ENHANCED STOCK FOOTAGE ========
    
    def search_stock_footage(self, query, per_page=10, vertical=True):
        """Search for stock footage with retry logic. Prioritize vertical format for Shorts."""
        if not self.api_keys["pexels"]:
            print("Pexels API key missing. Cannot search for stock footage.")
            return []
        
        # For Shorts, we should prioritize vertical videos
        orientation = "portrait" if vertical else "landscape"
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}&orientation={orientation}",
                    headers={"Authorization": self.api_keys["pexels"]},
                    timeout=30
                )
                
                if response.status_code == 200:
                    videos = response.json()["videos"]
                    video_urls = []
                    
                    for video in videos:
                        # Get the highest quality video file
                        files = sorted(video["video_files"], key=lambda x: x.get("height", 0), reverse=True)
                        
                        # For Shorts, filter to get vertical videos if possible
                        if vertical:
                            vertical_files = [f for f in files if f.get("height", 0) > f.get("width", 0)]
                            files_to_use = vertical_files if vertical_files else files
                        else:
                            files_to_use = files
                            
                        if files_to_use:
                            video_urls.append(files_to_use[0]["link"])
                    
                    return video_urls
                else:
                    print(f"Error searching stock footage (attempt {attempt+1}): {response.status_code}")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print("Retrying...")
                        time.sleep(2)  # Wait before retry
                    
            except Exception as e:
                print(f"Error in search_stock_footage (attempt {attempt+1}): {str(e)}")
                if attempt < max_attempts - 1:  # Not the last attempt
                    print("Retrying...")
                    time.sleep(2)  # Wait before retry
        
        # If all portrait attempts fail but vertical was requested, try again with any orientation
        if vertical:
            print("Failed to find vertical stock footage. Trying with any orientation.")
            return self.search_stock_footage(query, per_page=per_page, vertical=False)
            
        return []  # Return empty list if all attempts fail
    
    def download_stock_footage(self, video_urls, idea_title):
        """Download stock footage with better error handling."""
        safe_title = self.sanitize_filename(idea_title)
        video_dir = f"{self.config['directories']['video']}/{safe_title.replace(' ', '_')}"
        try:
                os.makedirs(video_dir, exist_ok=True)
                print(f"Created video directory: {video_dir}")
        except Exception as e:
                print(f"Error creating video directory: {e}")
                # Create a fallback directory with a simple name
                video_dir = f"{self.config['directories']['video']}/shorts_{int(time.time())}"
                os.makedirs(video_dir, exist_ok=True)
                print(f"Using fallback video directory: {video_dir}")
            
        downloaded_files = []
        successful_downloads = 0
        required_clips = min(6, len(video_urls))  # For Shorts, we need fewer clips
        
        for i, url in enumerate(video_urls):
            # If we already have enough clips, stop downloading
            if successful_downloads >= required_clips:
                break
                
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"Downloading clip {i+1}/{len(video_urls)} (attempt {attempt+1})")
                    
                    response = requests.get(url, stream=True, timeout=60)
                    if response.status_code == 200:
                        video_path = f"{video_dir}/clip_{i}.mp4"
                        with open(video_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    f.write(chunk)
                        
                        # Verify file was downloaded correctly
                        if os.path.getsize(video_path) > 1000:  # Ensure file isn't too small
                            downloaded_files.append(video_path)
                            successful_downloads += 1
                            print(f"Successfully downloaded clip {i+1}")
                            break  # Success, exit retry loop
                        else:
                            print(f"Downloaded file too small, retrying...")
                            os.remove(video_path)  # Remove corrupted file
                            continue
                    else:
                        print(f"Error downloading clip {i+1} (attempt {attempt+1}): {response.status_code}")
                        if attempt < max_attempts - 1:  # Not the last attempt
                            print("Retrying...")
                            time.sleep(2)  # Wait before retry
                
                except Exception as e:
                    print(f"Error downloading clip {i+1} (attempt {attempt+1}): {str(e)}")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print("Retrying...")
                        time.sleep(2)  # Wait before retry
        
        # Check if we have enough clips
        if len(downloaded_files) < 2:  # For Shorts, even 2 clips may be enough
            print("Warning: Not enough stock footage downloaded. Using fallback footage.")
            # TODO: Implement fallback footage option
        
        return downloaded_files
    
    # ======== ENHANCED THUMBNAIL GENERATION ========

    def create_thumbnail(self, idea):
        """Create a thumbnail with retry logic and fallback. Optimized for Shorts."""
        if not self.api_keys["openai"]:
            print("OpenAI API key missing. Cannot generate thumbnail.")
            safe_title = self.sanitize_filename(idea['title'])
            thumbnail_path = f"{self.config['directories']['thumbnails']}/{safe_title}.png"
            
            return self._create_placeholder_thumbnail(
                thumbnail_path, 
                idea['title']
            )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # First, generate a thumbnail description optimized for Shorts
                prompt = f"""
                Describe an eye-catching thumbnail image for a YouTube Short video titled:
                "{idea['title']}"
                
                The description should be detailed but concise (less than 200 words).
                Important requirements for Shorts thumbnails:
                - MUST be in VERTICAL format (taller than wide, 9:16 ratio)
                - Focus on a single striking visual element
                - Bold, large text overlay that's readable on small screens
                - Bright, high-contrast colors
                - Simple background with clear foreground subject
                - Emotionally engaging (surprising, intriguing, or exciting)
                """
                
                # Generate description
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['openai']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",  # Use cheaper model for description
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    },
                    timeout=45  # Increased timeout
                )
                
                if response.status_code == 200:
                    thumbnail_desc = response.json()["choices"][0]["message"]["content"]
                    print(f"Thumbnail description generated ({len(thumbnail_desc)} chars)")
                    
                    # Generate image
                    models_to_try = ["dall-e-3", "dall-e-2"]
                    for model in models_to_try:
                        try:
                            # Get main topic and keywords from title and description
                            title_words = idea['title'].split()
                            keywords = []
                            if len(title_words) > 5:
                                keywords = title_words[:5]  # Take first 5 words max
                            else:
                                keywords = title_words
                                
                            # Create a shortened prompt
                            shortened_desc = thumbnail_desc
                            if model == "dall-e-2":
                                # For DALL-E 2, we need a much shorter prompt
                                # Extract first 2 sentences max
                                sentences = thumbnail_desc.split('.')[:2]
                                shortened_desc = '.'.join(sentences)
                                
                                # Limit to 100 characters
                                if len(shortened_desc) > 100:
                                    shortened_desc = shortened_desc[:97] + "..."
                            
                            # Build the prompt with controlled length
                            base_prompt = f"YouTube Shorts thumbnail for: {' '.join(keywords)}. {shortened_desc}"
                            style_prompt = "Vertical format 9:16 ratio, bright colors, simple bold text, perfect for mobile viewing."
                            
                            # Check total length and trim if needed
                            total_prompt = f"{base_prompt} {style_prompt}"
                            if len(total_prompt) > 950:  # Buffer below 1000 limit
                                # Trim the base prompt part
                                available_length = 950 - len(style_prompt) - 1
                                base_prompt = base_prompt[:available_length - 3] + "..."
                                total_prompt = f"{base_prompt} {style_prompt}"
                            
                            print(f"Using {model} with prompt length: {len(total_prompt)}")
                            
                            response = requests.post(
                                "https://api.openai.com/v1/images/generations",
                                headers={
                                    "Authorization": f"Bearer {self.api_keys['openai']}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "prompt": total_prompt,
                                    "n": 1,
                                    "size": "1024x1024",  # Best for Shorts, we'll crop as needed
                                    "model": model
                                },
                                timeout=60  # Increased timeout for image generation
                            )
                            
                            if response.status_code == 200:
                                response_data = response.json()
                                print(f"DALL-E response received: {json.dumps(response_data, indent=2)}")
                                
                                if "data" in response_data and len(response_data["data"]) > 0 and "url" in response_data["data"][0]:
                                    image_url = response_data["data"][0]["url"]
                                    print(f"Image URL received: {image_url}")
                                    
                                    # Download the image with better error handling
                                    try:
                                        img_response = requests.get(image_url, timeout=30, stream=True)
                                        if img_response.status_code == 200:
                                            # Create the thumbnails directory if it doesn't exist
                                            thumbnails_dir = self.config['directories']['thumbnails']
                                            os.makedirs(thumbnails_dir, exist_ok=True)
                                            
                                            # Get content length to verify we have data
                                            content_length = int(img_response.headers.get('content-length', 0))
                                            if content_length == 0:
                                                print("Warning: Image has zero content length")
                                            
                                            # IMPORTANT FIX: Use consistent naming pattern without _Short suffix
                                            # This ensures names match what the web interface expects
                                            safe_title = self.sanitize_filename(idea['title'])
                                            thumbnail_path = f"{thumbnails_dir}/{safe_title}.png"
                                            
                                            with open(thumbnail_path, 'wb') as f:
                                                for chunk in img_response.iter_content(chunk_size=8192):
                                                    if chunk:
                                                        f.write(chunk)
                                            
                                            # Process the image to ensure it's vertical format for Shorts
                                            try:
                                                from PIL import Image
                                                
                                                # Open and convert to vertical format if needed
                                                img = Image.open(thumbnail_path)
                                                width, height = img.size
                                                
                                                # If it's not already vertical, crop it to be vertical (9:16 ratio)
                                                if width >= height:
                                                    # Calculate new width for 9:16 ratio
                                                    new_width = int(height * 9/16)
                                                    # Center crop
                                                    left = (width - new_width) // 2
                                                    right = left + new_width
                                                    img = img.crop((left, 0, right, height))
                                                    # Save the cropped image
                                                    img.save(thumbnail_path)
                                                    print(f"Image cropped to vertical format (9:16 ratio)")
                                            except Exception as e:
                                                print(f"Error processing thumbnail to vertical format: {str(e)}")
                                            
                                            # Verify the file was written successfully
                                            if os.path.getsize(thumbnail_path) > 0:
                                                print(f"✓ Shorts thumbnail generated with {model} and saved to {thumbnail_path} ({os.path.getsize(thumbnail_path)} bytes)")
                                                return thumbnail_path
                                            else:
                                                print(f"✗ Thumbnail file was created but has 0 bytes: {thumbnail_path}")
                                                # Try to create a simple placeholder instead
                                                if self._create_placeholder_thumbnail(thumbnail_path, idea['title']):
                                                    print(f"✓ Created placeholder thumbnail instead: {thumbnail_path}")
                                                    return thumbnail_path
                                        else:
                                            print(f"Error downloading thumbnail: {img_response.status_code}")
                                            print(f"Response: {img_response.text}")
                                    except Exception as e:
                                        print(f"Error downloading or saving thumbnail: {str(e)}")
                                else:
                                    print(f"Error: Missing 'data' or 'url' in DALL-E response: {response_data}")
                            else:
                                print(f"Error generating thumbnail with {model}: {response.status_code}")
                                if hasattr(response, 'text'):
                                    print(response.text)
                                continue
                        except Exception as e:
                            print(f"Error with {model} thumbnail generation: {str(e)}")
                            continue
                else:
                    print(f"Error generating thumbnail description (attempt {attempt+1}): {response.status_code}")
                    if hasattr(response, 'text'):
                        print(response.text)
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print("Retrying...")
                        time.sleep(2)  # Wait before retry
            
            except Exception as e:
                print(f"Error in create_thumbnail (attempt {attempt+1}): {str(e)}")
                if attempt < max_attempts - 1:  # Not the last attempt
                    print("Retrying...")
                    time.sleep(2)  # Wait before retry
        
        # If all attempts fail, create a placeholder
        print("All thumbnail generation attempts failed. Creating placeholder.")
        safe_title = self.sanitize_filename(idea['title'])
        thumbnail_path = f"{self.config['directories']['thumbnails']}/{safe_title}.png"
        if self._create_placeholder_thumbnail(thumbnail_path, idea['title'], vertical=True):
            return thumbnail_path
        else:
            return None

    def _create_placeholder_thumbnail(self, path, title, vertical=True):
        """Create a simple placeholder thumbnail with PIL, optimized for vertical format."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            if vertical:
                # Create a blank image with a vertical (9:16) aspect ratio
                img = Image.new('RGB', (720, 1280), color=(33, 33, 33))
            else:
                # Standard aspect ratio
                img = Image.new('RGB', (1280, 720), color=(33, 33, 33))
                
            draw = ImageDraw.Draw(img)
            
            # Draw a border
            if vertical:
                draw.rectangle([(40, 40), (680, 1240)], outline=(100, 100, 200), width=8)
            else:
                draw.rectangle([(40, 40), (1240, 680)], outline=(100, 100, 200), width=8)
            
            # Draw a gradient background (simple version)
            if vertical:
                # Vertical gradient
                for y in range(80, 1200):
                    # Create a gradient from dark blue to light blue
                    color = (
                        int(33 + (y/1200) * 60),  # R value
                        int(33 + (y/1200) * 70),  # G value
                        int(100 + (y/1200) * 155)  # B value
                    )
                    draw.line([(80, y), (640, y)], fill=color)
            else:
                # Horizontal gradient
                for y in range(80, 640):
                    # Create a gradient from dark blue to light blue
                    color = (
                        int(33 + (y/640) * 60),  # R value
                        int(33 + (y/640) * 70),  # G value
                        int(100 + (y/640) * 155)  # B value
                    )
                    draw.line([(80, y), (1200, y)], fill=color)
            
            # Add title text
            try:
                # Try to use a default font
                font = None
                try:
                    # Try a few different system fonts
                    for font_name in ['arial.ttf', 'Arial.ttf', 'Verdana.ttf', 'times.ttf', 'Times.ttf', 'Courier.ttf']:
                        try:
                            if vertical:
                                font = ImageFont.truetype(font_name, 80)  # Larger font for vertical
                            else:
                                font = ImageFont.truetype(font_name, 60)
                            break
                        except:
                            continue
                except:
                    pass
                    
                if font is None:
                    try:
                        font = ImageFont.load_default()
                    except:
                        pass
                    
                # Prepare the title (shorten if needed)
                text = title
                if len(text) > 30:
                    text = text[:27] + "..."
                
                # Calculate text size and position
                text_width = 600  # Approximate width as fallback
                text_height = 60  # Approximate height as fallback
                
                # Try to get actual text dimensions if the method exists
                if hasattr(draw, 'textbbox'):
                    # For newer PIL versions
                    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                    text_width = right - left
                    text_height = bottom - top
                elif hasattr(draw, 'textsize'):
                    # For older PIL versions
                    text_width, text_height = draw.textsize(text, font=font)
                
                # Calculate position to center the text
                if vertical:
                    position = ((720 - text_width) // 2, 300)  # Higher up in vertical format
                else:
                    position = ((1280 - text_width) // 2, (720 - text_height) // 2)
                
                # Draw text shadow
                shadow_offset = 3
                draw.text((position[0] + shadow_offset, position[1] + shadow_offset), 
                        text, fill=(0, 0, 0), font=font)
                
                # Draw the text
                draw.text(position, text, fill=(255, 255, 255), font=font)
                
                # For vertical format, add "SHORTS" text at the bottom
                if vertical:
                    shorts_text = "#SHORTS"
                    if hasattr(draw, 'textbbox'):
                        left, top, right, bottom = draw.textbbox((0, 0), shorts_text, font=font)
                        shorts_width = right - left
                    elif hasattr(draw, 'textsize'):
                        shorts_width, _ = draw.textsize(shorts_text, font=font)
                    else:
                        shorts_width = 300  # Estimate
                        
                    shorts_position = ((720 - shorts_width) // 2, 1100)
                    draw.text((shorts_position[0] + shadow_offset, shorts_position[1] + shadow_offset),
                            shorts_text, fill=(0, 0, 0), font=font)
                    draw.text(shorts_position, shorts_text, fill=(255, 100, 100), font=font)
                
            except Exception as e:
                print(f"Error adding text to thumbnail: {str(e)}")
                # Fall back to a very simple text
                try:
                    if vertical:
                        draw.text((360, 640), title[:20], fill=(255, 255, 255))
                    else:
                        draw.text((640, 360), title[:20], fill=(255, 255, 255))
                except:
                    pass
            
            # Save the image in PNG format
            img.save(path, format="PNG")
            print(f"Created placeholder thumbnail at {path}")
            return True
        except Exception as e:
            print(f"Error creating placeholder thumbnail: {str(e)}")
            # Last resort - create a tiny valid PNG file
            try:
                # Create a 1x1 pixel PNG
                with open(path, 'wb') as f:
                    # Minimal PNG file header and data (1x1 black pixel)
                    png_data = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63000000000001000001000118fa0000000049454e44ae426082')
                    f.write(png_data)
                    print(f"Created minimal 1x1 PNG as last resort")
                return True
            except Exception as e:
                print(f"Final fallback also failed: {str(e)}")
                return False
    
    # ======== VIDEO ASSEMBLY FOR SHORTS ========
    
    def assemble_video(self, audio_file, video_clips, idea_title):
        """Assemble the final video. For Shorts system, always use vertical format."""
        print("Creating YouTube Shorts format video...")
        return self.assemble_shorts_video(audio_file, video_clips, idea_title)
    
    def assemble_shorts_video(self, audio_file, video_clips, idea_title):
        """Assemble a YouTube Shorts video (vertical format, fast-paced)."""
        # Create output directory if it doesn't exist
        output_dir = self.config['directories']['output']
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the output filename
        safe_title = self.sanitize_filename(idea_title)
        final_output = f"{output_dir}/{safe_title.replace(' ', '_')}_Short.mp4"
        
        try:
            # SECTION 1: VERIFY INPUTS
            # Verify the audio file exists
            if not os.path.exists(audio_file):
                print(f"ERROR: Audio file does not exist: {audio_file}")
                return None
                
            audio_size = os.path.getsize(audio_file)
            print(f"Audio file size: {audio_size} bytes")
            
            if audio_size < 1000:
                print(f"WARNING: Audio file is suspiciously small ({audio_size} bytes). Check ElevenLabs API.")
                self._create_diagnostic_report(audio_file, video_clips, idea_title)
                return None
            
            # Verify we have video clips
            if not video_clips or len(video_clips) == 0:
                print("ERROR: No video clips provided")
                return None
                
            print(f"Found {len(video_clips)} video clips to process")
            
            # Create a directory for temporary files
            safe_title_dir = self.sanitize_filename(idea_title)
            video_dir = f"{self.config['directories']['video']}/{safe_title_dir.replace(' ', '_')}"
            os.makedirs(video_dir, exist_ok=True)
            
            # SECTION 2: STANDARDIZE CLIPS FOR SHORTS (VERTICAL FORMAT)
            # Standardize all clips to vertical format for Shorts
            standardized_clips = []
            for i, clip in enumerate(video_clips):
                std_clip = f"{video_dir}/std_clip_{i}.mp4"
                print(f"Standardizing clip {i+1}/{len(video_clips)} for Shorts...")
                
                try:
                    # For Shorts, we need vertical format (9:16 aspect ratio)
                    # Use 720x1280 as the standard vertical resolution for Shorts
                    subprocess.run([
                        "ffmpeg", "-y", "-i", clip, 
                        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                        "-pix_fmt", "yuv420p", std_clip
                    ], capture_output=True, check=True)
                    
                    standardized_clips.append(std_clip)
                except subprocess.CalledProcessError as e:
                    print(f"Error standardizing clip {i+1}:")
                    print(e.stderr.decode())
                    # Try a simpler conversion as fallback
                    try:
                        # Simpler approach that at least ensures vertical orientation
                        subprocess.run([
                            "ffmpeg", "-y", "-i", clip, 
                            "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                            "-c:v", "libx264", std_clip
                        ], capture_output=True, check=True)
                        standardized_clips.append(std_clip)
                    except subprocess.CalledProcessError as e:
                        print(f"Fallback conversion also failed for clip {i+1}")
                        print(e.stderr.decode())
                        continue
            
            if not standardized_clips:
                print("No clips could be standardized for Shorts format. Aborting.")
                return None
                
            # SECTION 3: CONCATENATE CLIPS INTO ONE VIDEO
            concat_output = f"{video_dir}/concat_output.mp4"
            
            # Create a file list for FFmpeg's concat demuxer
            clips_list_path = f"{video_dir}/clips_list.txt"
            with open(clips_list_path, 'w') as f:
                for clip in standardized_clips:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            
            # Method 1: Use concat demuxer (faster, but less reliable)
            concat_success = False
            try:
                print("Running FFmpeg to concatenate clips (Method 1)...")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                    "-i", clips_list_path, "-c:v", "libx264", 
                    "-pix_fmt", "yuv420p", concat_output
                ], capture_output=True, check=True)
                concat_success = True
            except subprocess.CalledProcessError as e:
                print("Method 1 failed. Trying Method 2...")
                print(e.stderr.decode())
                
                # Method 2: Use filtergraph (slower, but more reliable)
                try:
                    # Build the complex filtergraph
                    filter_parts = []
                    for i in range(len(standardized_clips)):
                        filter_parts.append(f"[{i}:v]")
                    
                    filter_complex = "".join(filter_parts) + f"concat=n={len(standardized_clips)}:v=1:a=0[outv]"
                    
                    # Build the input arguments
                    input_args = []
                    for clip in standardized_clips:
                        input_args.extend(["-i", clip])
                    
                    # Run FFmpeg with the complex filter
                    subprocess.run(
                        ["ffmpeg", "-y"] + input_args + [
                            "-filter_complex", filter_complex, 
                            "-map", "[outv]", 
                            "-c:v", "libx264", 
                            "-pix_fmt", "yuv420p", 
                            concat_output
                        ], capture_output=True, check=True
                    )
                    concat_success = True
                except subprocess.CalledProcessError as e:
                    print("Method 2 failed as well")
                    print(e.stderr.decode())
                    return None
            
            if not concat_success or not os.path.exists(concat_output):
                print("Failed to concatenate clips. Aborting.")
                return None
            
            # SECTION 4: GET AUDIO DURATION
            # Get audio duration using ffprobe
            audio_duration = 0
            try:
                # Try ffprobe first (most accurate)
                result = subprocess.run([
                    "ffprobe", 
                    "-v", "error", 
                    "-show_entries", "format=duration", 
                    "-of", "default=noprint_wrappers=1:nokey=1", 
                    audio_file
                ], capture_output=True, text=True, check=True)
                
                audio_duration = float(result.stdout.strip())
                print(f"Audio duration: {audio_duration:.2f} seconds")
            except:
                # Fallback to ffmpeg if ffprobe fails
                try:
                    result = subprocess.run([
                        "ffmpeg", "-i", audio_file, "-f", "null", "-"
                    ], capture_output=True, text=True)
                    
                    # Extract duration with regex
                    duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
                    if duration_match:
                        h, m, s = duration_match.groups()
                        audio_duration = float(h) * 3600 + float(m) * 60 + float(s)
                        print(f"Audio duration (from ffmpeg): {audio_duration:.2f} seconds")
                    else:
                        print("Couldn't determine audio duration, using default of 60 seconds (max for Shorts)")
                        audio_duration = 60  # Default to 60 seconds max for Shorts
                except:
                    print("Failed to determine audio duration. Using default of 60 seconds.")
                    audio_duration = 60  # Default to 60 seconds max for Shorts
            
            # Check if audio exceeds Shorts limit
            if audio_duration > 60:
                print(f"WARNING: Audio duration ({audio_duration:.2f} seconds) exceeds YouTube Shorts limit of 60 seconds.")
                print("Truncating to 60 seconds...")
                audio_duration = 60
                
                # Create a truncated version of the audio
                truncated_audio = f"{video_dir}/truncated_audio.mp3"
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", audio_file, 
                        "-t", "60", 
                        "-c:a", "aac", truncated_audio
                    ], capture_output=True, check=True)
                    
                    if os.path.exists(truncated_audio):
                        audio_file = truncated_audio
                        print(f"Created truncated audio file: {truncated_audio}")
                except Exception as e:
                    print(f"Error truncating audio: {str(e)}")
                    # Continue with original audio, will be truncated in final output
            
            # Verify valid audio duration
            if audio_duration < 1:
                print(f"WARNING: Audio duration is too short ({audio_duration:.2f} seconds)")
                print("This is likely due to an issue with the audio generation.")
                return None
            
            # SECTION 5: PREPARE VIDEO FOR ASSEMBLY
            # Get video duration
            video_duration = 0
            try:
                result = subprocess.run([
                    "ffprobe", 
                    "-v", "error", 
                    "-show_entries", "format=duration", 
                    "-of", "default=noprint_wrappers=1:nokey=1", 
                    concat_output
                ], capture_output=True, text=True, check=True)
                
                video_duration = float(result.stdout.strip())
                print(f"Video duration: {video_duration:.2f} seconds")
            except:
                print("Couldn't determine video duration. Assuming 30 seconds.")
                video_duration = 30  # Assume 30 seconds
            
            # Check if video needs to be extended to match audio
            # Extended version is needed if video is shorter than audio
            extended_video = None
            video_to_use = concat_output
            
            if video_duration < audio_duration:
                print(f"Video ({video_duration:.2f}s) is shorter than audio ({audio_duration:.2f}s). Extending video...")
                
                # Calculate number of loops needed
                loops_needed = int(audio_duration / video_duration) + 1
                print(f"Looping video {loops_needed} times to match audio")
                
                extended_video = f"{video_dir}/extended_video.mp4"
                try:
                    # Create extended video by looping
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-stream_loop", str(loops_needed),
                        "-i", concat_output,
                        "-c", "copy",
                        "-t", str(audio_duration + 1),  # Add 1 second buffer
                        extended_video
                    ], capture_output=True, check=True)
                    
                    if os.path.exists(extended_video):
                        video_to_use = extended_video
                        print("Video extended successfully")
                    else:
                        print("Failed to extend video. Using original concatenated video.")
                except Exception as e:
                    print(f"Error extending video: {e}")
                    print("Using original concatenated video.")
            
            # SECTION 6: COMBINE VIDEO WITH AUDIO AND ADD TEXT OVERLAYS
            # For Shorts, we may want to add text overlays based on the script
            # This would require parsing the script to extract [TEXT] tags
            
            print(f"Combining video with audio to create final Shorts video: {final_output}")
            try:
                # For Shorts, ensure the final video is exactly the right length
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", video_to_use,
                    "-i", audio_file,
                    "-c:v", "libx264",  # Copy video with re-encoding
                    "-c:a", "aac",      # Convert audio to AAC
                    "-map", "0:v:0",    # Take video from first input
                    "-map", "1:a:0",    # Take audio from second input
                    "-shortest",        # End when shortest input ends
                    "-t", str(min(audio_duration, 60)),  # Limit to max 60 seconds for Shorts
                    final_output
                ], capture_output=True, check=True)
                
                # Clean up temporary file if it exists
                if extended_video and os.path.exists(extended_video):
                    os.remove(extended_video)
                
                # Verify the final output
                if os.path.exists(final_output):
                    output_size = os.path.getsize(final_output)
                    print(f"Final Shorts video created: {final_output} ({output_size} bytes)")
                    
                    if output_size < 10000:  # Very small file
                        print("WARNING: Final video file is suspiciously small")
                        
                    # Check the duration of the final video
                    try:
                        result = subprocess.run([
                            "ffprobe", 
                            "-v", "error", 
                            "-show_entries", "format=duration", 
                            "-of", "default=noprint_wrappers=1:nokey=1", 
                            final_output
                        ], capture_output=True, text=True, check=True)
                        
                        final_duration = float(result.stdout.strip())
                        print(f"Final video duration: {final_duration:.2f} seconds")
                        
                        if final_duration < 1:
                            print("WARNING: Final video is much shorter than expected!")
                            print("Attempting alternate assembly method...")
                            
                            # Try one more method if first assembly failed
                            alternate_output = f"{output_dir}/{idea_title.replace(' ', '_')}_alt_short.mp4"
                            return self._alternate_shorts_video_assembly(concat_output, audio_file, alternate_output)
                    except:
                        pass
                    
                    return final_output
                else:
                    print("Final video file not created. Attempting alternate method...")
                    
                    # Try one more method if first assembly failed
                    alternate_output = f"{output_dir}/{idea_title.replace(' ', '_')}_alt_short.mp4"
                    return self._alternate_shorts_video_assembly(concat_output, audio_file, alternate_output)
            except Exception as e:
                print(f"Error combining video with audio: {e}")
                # Try one more method if first assembly failed
                alternate_output = f"{output_dir}/{idea_title.replace(' ', '_')}_alt_short.mp4"
                return self._alternate_shorts_video_assembly(concat_output, audio_file, alternate_output)
                
        except Exception as e:
            print(f"Error in assemble_shorts_video: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
        return None
   
    def _alternate_shorts_video_assembly(self, video_path, audio_path, output_path):
        """Alternative video assembly method for Shorts as a fallback."""
        print("Using alternate Shorts video assembly method...")
        
        try:
            # 1. First, get audio duration (max 60 seconds for Shorts)
            audio_duration = 0
            try:
                result = subprocess.run([
                    "ffprobe", 
                    "-v", "error", 
                    "-show_entries", "format=duration", 
                    "-of", "default=noprint_wrappers=1:nokey=1", 
                    audio_path
                ], capture_output=True, text=True, check=True)
                audio_duration = min(float(result.stdout.strip()), 60)  # Cap at 60 seconds for Shorts
            except:
                audio_duration = 60  # Default to max Shorts duration
            
            # 2. Create a temporary extended video file
            temp_dir = "temp_files"
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_extended = os.path.join(temp_dir, "temp_extended.mp4")
            
            # Loop the video to be longer than the audio
            loops_needed = max(1, int(audio_duration / 15) + 1)  # Assume 15s original video
            
            subprocess.run([
                "ffmpeg", "-y",
                "-stream_loop", str(loops_needed),
                "-i", video_path,
                "-c:v", "libx264",  # Re-encode for reliability
                "-t", str(audio_duration + 2),  # Add buffer
                "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",  # Force vertical format for Shorts
                temp_extended
            ], capture_output=True, check=True)
            
            # 3. Now combine with audio
            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_extended,
                "-i", audio_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-t", str(audio_duration),  # Ensure max 60 seconds for Shorts
                output_path
            ], capture_output=True, check=True)
            
            # Clean up temp files
            if os.path.exists(temp_extended):
                os.remove(temp_extended)
            
            # Verify the output
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                print(f"Alternate method succeeded: {output_path}")
                return output_path
            else:
                print("Alternate method failed.")
                return None
        except Exception as e:
            print(f"Error in alternate Shorts video assembly: {e}")
            return None
            
    def _create_diagnostic_report(self, audio_file, video_clips, idea_title):
        """Create a diagnostic report for troubleshooting."""
        try:
            report_path = f"diagnostic_report_{idea_title.replace(' ', '_')}.txt"
            with open(report_path, 'w') as f:
                f.write(f"=== DIAGNOSTIC REPORT FOR {idea_title} (SHORTS) ===\n\n")
                
                # System information
                f.write("System Information:\n")
                f.write(f"Python version: {sys.version}\n")
                f.write(f"Current directory: {os.getcwd()}\n\n")
                
                # API keys status (without showing the actual keys)
                f.write("API Keys Status:\n")
                for key_name, key_value in self.api_keys.items():
                    status = "Available" if key_value else "Missing"
                    f.write(f"{key_name}: {status}\n")
                f.write("\n")
                
                # Shorts config information
                f.write("Shorts Configuration:\n")
                f.write(f"shorts_mode: {self.config.get('shorts_mode', False)}\n")
                shorts_settings = self.config.get('shorts_settings', {})
                for key, value in shorts_settings.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # Audio file information
                f.write("Audio File Information:\n")
                f.write(f"Path: {audio_file}\n")
                if os.path.exists(audio_file):
                    f.write(f"Size: {os.path.getsize(audio_file)} bytes\n")
                    f.write(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(audio_file))}\n")
                else:
                    f.write("ERROR: File does not exist\n")
                f.write("\n")
                
                # Video clips information
                f.write(f"Video Clips Information ({len(video_clips)} clips):\n")
                for i, clip in enumerate(video_clips):
                    f.write(f"Clip {i+1}: {clip}\n")
                    if os.path.exists(clip):
                        f.write(f"  Size: {os.path.getsize(clip)} bytes\n")
                        f.write(f"  Last modified: {datetime.fromtimestamp(os.path.getmtime(clip))}\n")
                    else:
                        f.write("  ERROR: File does not exist\n")
                f.write("\n")
                
                # Directories information
                f.write("Directories Information:\n")
                for dir_name, dir_path in self.config["directories"].items():
                    f.write(f"{dir_name}: {dir_path}")
                    if os.path.exists(dir_path):
                        f.write(" (exists)\n")
                    else:
                        f.write(" (does not exist)\n")
                f.write("\n")
                
                # Try to get FFmpeg version
                f.write("FFmpeg Information:\n")
                try:
                    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
                    if result.returncode == 0:
                        f.write(f"Version: {result.stdout.splitlines()[0]}\n")
                    else:
                        f.write("Error checking FFmpeg version\n")
                except:
                    f.write("FFmpeg not found in PATH\n")
                f.write("\n")
                
                f.write("=== END OF REPORT ===\n")
            
            print(f"Diagnostic report created at {report_path}")
            
        except Exception as e:
            print(f"Error creating diagnostic report: {e}")
    
    # ======== ENHANCED YOUTUBE UPLOAD ========
    
    def upload_to_youtube(self, video_path, idea, thumbnail_path=None):
        """Upload the video to YouTube with better error handling, optimized for Shorts."""
        # Import the YouTubeUploader
        try:
            from youtube_uploader import YouTubeUploader
        except ImportError:
            print("YouTubeUploader module not found. Creating the module...")
            
            # Save the uploader module to a file
            with open("youtube_uploader.py", "w") as f:
                f.write("""
                # [Contents of youtube_uploader.py would be here]
                # This is just a placeholder to avoid an error - in a real scenario, 
                # you would create the actual uploader code
                """)
            
            # Install required dependencies
            try:
                print("Installing required packages...")
                import subprocess
                subprocess.run(["pip", "install", "google-api-python-client", "google-auth-oauthlib"])
            except:
                print("Failed to install required packages.")
            
            try:
                # Try again to import
                from youtube_uploader import YouTubeUploader
            except ImportError:
                print("Failed to import YouTubeUploader after creation. Skipping upload.")
                
                # Record video data even if upload failed
                self._record_video_data(idea, "local_only", "local")
                return None
        
        # Check if client_secrets.json exists
        if not os.path.exists("client_secrets.json"):
            print("WARNING: client_secrets.json not found! Upload will be skipped.")
            print("Please create this file with your YouTube API OAuth credentials.")
            
            # Record video data even if upload failed
            self._record_video_data(idea, "local_only", "local")
            return None
        
        # Create YouTube uploader
        try:
            uploader = YouTubeUploader(client_secrets_file="client_secrets.json")
        except Exception as e:
            print(f"Error creating YouTube uploader: {str(e)}")
            
            # Record video data even if upload failed
            self._record_video_data(idea, "local_only", "local")
            return None
        
        # Prepare video metadata optimized for Shorts
        title = idea["title"]
        
        # Create a description that includes Shorts hashtags
        description = f"{idea['description']}\n\n"
        
        # Add hashtags for Shorts visibility
        description += "#Shorts #YouTubeShorts "
        
        # Add topic-specific hashtags
        if isinstance(idea["keywords"], list) and idea["keywords"]:
            topic_hashtags = " ".join([f"#{keyword.replace(' ', '')}" for keyword in idea["keywords"][:5] if keyword.lower() not in ["shorts", "youtubeshorts", "shortvideo"]])
            description += topic_hashtags
        
        # Convert keywords to tags, ensuring "shorts" is included
        tags = idea["keywords"] if isinstance(idea["keywords"], list) else []
        if "shorts" not in [t.lower() for t in tags]:
            tags.append("shorts")
        if "youtubeshorts" not in [t.lower() for t in tags]:
            tags.append("YouTubeShorts")
        
        # Choose a privacy status (private, unlisted, or public)
        # Start with private so you can review before publishing
        privacy_status = "private"
        
        # Upload the video with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"Uploading Shorts video: {title} (attempt {attempt+1})")
                video_id = uploader.upload_video(
                    video_file=video_path,
                    title=title,
                    description=description,
                    tags=tags,
                    privacy_status=privacy_status
                )
                
                if not video_id:
                    print(f"Video upload failed (attempt {attempt+1})")
                    if attempt < max_attempts - 1:  # Not the last attempt
                        print("Retrying...")
                        time.sleep(5)  # Wait before retry
                        continue
                    else:
                        # Record video data even if upload failed
                        self._record_video_data(idea, "local_only", "local")
                        return None
                
                # Upload thumbnail if available
                if thumbnail_path and os.path.exists(thumbnail_path):
                    print("Setting custom thumbnail...")
                    thumbnail_success = uploader.update_thumbnail(video_id, thumbnail_path)
                    if not thumbnail_success:
                        print("Warning: Failed to set custom thumbnail, but video was uploaded successfully.")
                
                # Print video URL
                video_url = f"https://www.youtube.com/shorts/{video_id}"
                print(f"Shorts video uploaded successfully: {video_url}")
                
                # Record successful upload
                self._record_video_data(idea, video_id, title)
                
                return video_id
                
            except Exception as e:
                print(f"Error in upload_to_youtube (attempt {attempt+1}): {str(e)}")
                if attempt < max_attempts - 1:  # Not the last attempt
                    print("Retrying...")
                    time.sleep(5)  # Wait before retry
                else:
                    # Record video data even if upload failed
                    self._record_video_data(idea, "local_only", "local")
                    return None
    
    # ======== SHORTS AUTOMATION PIPELINE ========
    
    def run_full_automation(self, niche, voice_id=None):
        """Run the full automation pipeline for YouTube Shorts with enhanced resilience."""
        print(f"Starting Shorts automation for niche: {niche}")
        
        # Verify API keys are available
        print("\n=== API KEY STATUS ===")
        for key_name, key_value in self.api_keys.items():
            status = "✓ Available" if key_value else "✗ Missing"
            print(f"{key_name}: {status}")
        print("=====================\n")
        
        # Force shorts mode to be true (this is a Shorts-only system)
        self.config["shorts_mode"] = True
        if "shorts_settings" not in self.config:
            self.config["shorts_settings"] = {
                "enabled": True,
                "max_duration": 60,
                "vertical_format": True,
                "fast_paced": True
            }
        else:
            self.config["shorts_settings"]["enabled"] = True
        
        # Step 1: Generate content ideas specifically for Shorts
        ideas = self.generate_content_ideas(niche)
        if not ideas:
            print("Failed to generate Shorts content ideas. Aborting.")
            return
        
        # Select the best idea (not just random)
        idea = self._select_best_idea(ideas, niche)
        print(f"Selected Shorts idea: {idea['title']}")
        
        # Step 2: Generate script optimized for Shorts
        script_data = None
        max_script_attempts = self.config.get("api_settings", {}).get("retry_attempts", 3)
        for attempt in range(max_script_attempts):
            script_data = self.generate_script(idea)
            if script_data:
                break
            print(f"Shorts script generation attempt {attempt+1} failed. Retrying...")
        
        if not script_data:
            print("Failed to generate Shorts script after multiple attempts. Aborting.")
            return
        
        # Step 3: Generate voice narration with retry
        audio_file = None
        max_audio_attempts = self.config.get("api_settings", {}).get("retry_attempts", 3)
        for attempt in range(max_audio_attempts):
            audio_file = self.generate_voice_narration(script_data, voice_id)
            if audio_file:
                break
            print(f"Voice narration attempt {attempt+1} failed. Retrying...")
        
        # Step 4: Search and download vertical stock footage with quality monitoring
        search_terms = [idea['title']] + idea['key_points'] + idea['keywords']
        all_video_urls = []
        
        # For Shorts, prioritize vertical format
        for term in search_terms[:3]:  # Limit to first 3 terms
            urls = self.search_stock_footage(term, per_page=3, vertical=True)
            if urls:
                all_video_urls.extend(urls)
        
        # If we didn't get enough footage, try broader terms
        if len(all_video_urls) < 3:
            print("Not enough vertical stock footage found. Trying broader terms...")
            broader_terms = [niche, "social media", "vertical video", "shorts"]
            for term in broader_terms:
                if len(all_video_urls) >= 6:  # We have enough now
                    break
                urls = self.search_stock_footage(term, per_page=3, vertical=True)
                if urls:
                    all_video_urls.extend(urls)
        
        video_clips = self.download_stock_footage(all_video_urls, idea['title'])
        if not video_clips:
            print("Failed to download stock footage. Aborting.")
            return
        
        # Step 5: Create thumbnail optimized for Shorts with retry
        thumbnail_path = None
        max_thumbnail_attempts = self.config.get("api_settings", {}).get("retry_attempts", 3)
        for attempt in range(max_thumbnail_attempts):
            thumbnail_path = self.create_thumbnail(idea)
            if thumbnail_path:
                break
            print(f"Thumbnail creation attempt {attempt+1} failed. Retrying...")
        
        # Step 6: Assemble Shorts video
        final_video = self.assemble_shorts_video(audio_file, video_clips, idea['title'])
        if not final_video:
            print("Failed to assemble Shorts video. Aborting.")
            return
        
        # Step 7: Upload to YouTube as a Short
        video_id = self.upload_to_youtube(final_video, idea, thumbnail_path)
        if video_id:
            print(f"Shorts video published successfully! ID: {video_id}")
            print(f"Watch at: https://www.youtube.com/shorts/{video_id}")
        
            print("Shorts automation pipeline completed successfully!")
            print(f"Final Shorts video saved to: {final_video}")
            return final_video
        else:
            print("Shorts video was created but not uploaded to YouTube. You can find it at:")
            print(f"  {final_video}")
            final_output = final_video  
            return final_output


# Example usage
if __name__ == "__main__":
    # Create the automation system specifically for Shorts
    automation = YouTubeShortsAutomationSystem()
    
    # Run the full automation pipeline for a specific niche
    niche = input("Enter content niche for Shorts (default: fintech tips): ") or "fintech tips"
    automation.run_full_automation(niche)