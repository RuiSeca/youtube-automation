"""
Test script for the YouTube automation system.
Run this file to execute the full automation pipeline.
"""

from youtube_shorts_automation import YouTubeShortsAutomationSystem

if __name__ == "__main__":
    # Create the automation system
    automation = YouTubeShortsAutomationSystem()
    
    # Ask for a niche
    niche = input("Enter a content niche (e.g., technology tutorials, cooking recipes): ")
    if not niche:
        niche = "technology tutorials"  # Default niche
    
    # Run the full automation pipeline
    automation.run_full_automation(niche)