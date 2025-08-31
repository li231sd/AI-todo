import tensorflow as tf
import numpy as np
import re
from datetime import datetime, timedelta
import calendar
import spacy

class TaskParser:
    def __init__(self):
        """Initialize the task parser with TensorFlow models and NLP tools"""
        self.setup_nlp()
        self.setup_patterns()
        
    def setup_nlp(self):
        """Setup spaCy for better NLP processing"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def setup_patterns(self):
        """Setup regex patterns for date and time extraction"""
        # Date patterns
        self.date_patterns = {
            # Day names
            r'\b(monday|mon)\b': 'monday',
            r'\b(tuesday|tue|tues)\b': 'tuesday',
            r'\b(wednesday|wed)\b': 'wednesday',
            r'\b(thursday|thu|thurs)\b': 'thursday',
            r'\b(friday|fri)\b': 'friday',
            r'\b(saturday|sat)\b': 'saturday',
            r'\b(sunday|sun)\b': 'sunday',
            
            # Relative dates
            r'\b(today)\b': 'today',
            r'\b(tomorrow|tmrw|tmr)\b': 'tomorrow',
            r'\b(yesterday)\b': 'yesterday',
            r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': 'next_weekday',

            # Natural day parts
            r'\b(this\s+morning|this\s+afternoon|this\s+evening|tonight)\b': 'part_of_day',
            
            # Ordinal dates like "13th", "1st"
            r'\b(on\s+the\s+)?(\d{1,2})(st|nd|rd|th)\b': 'ordinal_date',

            # Slash-form dates (MM/DD or DD/MM)
            r'\b(\d{1,2})/(1[0-2]|0?[1-9])\b': 'date_slash',
            r'\b(1[0-2]|0?[1-9])/(\d{1,2})\b': 'date_slash_reverse',
            
            # Month names with optional ordinal suffix
            r'\b(january|jan)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(february|feb)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(march|mar)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(april|apr)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(may)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(june|jun)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(july|jul)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(august|aug)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(september|sep|sept)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(october|oct)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(november|nov)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
            r'\b(december|dec)\s+(\d{1,2})(st|nd|rd|th)?\b': 'month_date',
        }
        
        # Time patterns - inclusive of natural language forms
        self.time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)\b',      # 3:30pm
            r'\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b',              # 3pm
            r'\bat\s+(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)\b', # at 3:30pm
            r'\bat\s+(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b',         # at 3pm
            r'\b(\d{1,2}):(\d{2})\b',                              # 15:30 (24-hour)
            # Natural spoken forms
            r'\bat\s+(\d{1,2})\b',                                 # at 5
            r'\b(\d{1,2})\s*(in the morning|in the evening|in the afternoon|at night)\b',
            r'\bnoon\b',
            r'\bmidnight\b',
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(st|nd|rd|th)?",
            # Relative/natural language time
            r'\bin (\d{1,2}) hours\b',
            r'\bhalf past (\d{1,2})\b',
            r'\bquarter to (\d{1,2})\b',
            r'\bquarter past (\d{1,2})\b',
            r'\bbetween (\d{1,2}) and (\d{1,2})(am|pm)?\b',
        ]
    
    def parse(self, text):
        """Main parsing function"""
        text_lower = text.lower().strip()
        
        # Extract date
        date_info = self.extract_date(text_lower, text)
        
        # Extract time
        time_info = self.extract_time(text_lower)
        
        # Extract title
        title = self.extract_title(text, date_info.get('matched_text', ''), time_info.get('matched_text', ''))
        
        # NLP enhancement
        if self.nlp:
            title = self.enhance_title_with_nlp(title)
        
        return {
            'title': title or 'Untitled Task',
            'date': date_info.get('formatted_date'),
            'time': time_info.get('formatted_time'),
            'date_type': date_info.get('type'),
            'confidence': self.calculate_confidence(date_info, time_info, title),
            'raw_text': text
        }
    
    def extract_date(self, text_lower, original_text):
        for pattern, date_type in self.date_patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return self.process_date_match(match, date_type, original_text)
        return {'formatted_date': None, 'type': None, 'matched_text': ''}
    
    def process_date_match(self, match, date_type, original_text):
        matched_text = match.group(0)
        
        if date_type in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']:
            return {'formatted_date': date_type.capitalize(),'type':'weekday','matched_text':matched_text}
        elif date_type == 'today':
            return {'formatted_date':'Today','type':'relative','matched_text':matched_text}
        elif date_type == 'tomorrow':
            return {'formatted_date':'Tomorrow','type':'relative','matched_text':matched_text}
        elif date_type == 'yesterday':
            return {'formatted_date':'Yesterday','type':'relative','matched_text':matched_text}
        elif date_type == 'part_of_day':
            return {'formatted_date': matched_text.capitalize(),'type':'part_of_day','matched_text':matched_text}
        elif date_type == 'ordinal_date':
            day_num = int(match.group(2))
            current_month = datetime.now().strftime("%B")
            return {'formatted_date':f"{current_month} {day_num}",'type':'ordinal','matched_text':matched_text}
        elif date_type == 'month_date':
            month_name = match.group(1).capitalize()
            day_num = match.group(2)
            return {'formatted_date':f"{month_name} {day_num}",'type':'month_day','matched_text':matched_text}
        return {'formatted_date':None,'type':None,'matched_text':matched_text}
    
    def extract_time(self, text_lower):
        for pattern in self.time_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return self.process_time_match(match)
        return {'formatted_time': None, 'matched_text': ''}
    
    def process_time_match(self, match):
        matched_text = match.group(0).lower()
        groups = match.groups() if match.groups() else []

        try:
            # Noon / Midnight
            if "noon" in matched_text:
                return {'formatted_time': "12:00 PM", 'matched_text': matched_text}
            if "midnight" in matched_text:
                return {'formatted_time': "12:00 AM", 'matched_text': matched_text}

            # "at 5" → default to PM
            if re.match(r'at\s+\d{1,2}$', matched_text):
                hours = int(groups[0])
                return {'formatted_time': f"{hours}:00 PM", 'matched_text': matched_text}

            # "5 in the morning"/"5 in the evening"
            if len(groups) == 2 and "in the" in groups[1]:
                hours = int(groups[0])
                if "morning" in groups[1]:
                    return {'formatted_time': f"{hours}:00 AM", 'matched_text': matched_text}
                else:
                    if hours < 12: hours += 12
                    return {'formatted_time': f"{hours-12 if hours>12 else hours}:00 PM", 'matched_text': matched_text}

            # Standard parsing (hh:mm am/pm, etc.)
            groups = match.groups()
            if len(groups) == 3 and groups[2]:
                hours, minutes, meridiem = int(groups[0]), int(groups[1]), groups[2]
            elif len(groups) == 2 and not groups[1].isdigit():
                hours, minutes, meridiem = int(groups[0]), 0, groups[1]
            elif len(groups) == 2 and groups[1].isdigit():
                hours, minutes, meridiem = int(groups[0]), int(groups[1]), None
            else:
                return {'formatted_time': None, 'matched_text': matched_text}

            meridiem = meridiem.lower().replace('.', '') if meridiem else None
            if meridiem and 'p' in meridiem and hours != 12:
                hours += 12
            elif meridiem and 'a' in meridiem and hours == 12:
                hours = 0

            if hours == 0:
                display_hours, period = 12, 'AM'
            elif hours < 12:
                display_hours, period = hours, 'AM'
            elif hours == 12:
                display_hours, period = 12, 'PM'
            else:
                display_hours, period = hours - 12, 'PM'

            return {'formatted_time': f"{display_hours}:{minutes:02d} {period}", 'matched_text': matched_text}

        except Exception as e:
            print(f"Error processing time: {e}")
            return {'formatted_time': None, 'matched_text': matched_text}
    
    def extract_title(self, original_text, date_text, time_text):
        title = original_text
        # Remove all date/time patterns from title
        for pattern in list(self.date_patterns.keys()) + self.time_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def enhance_title_with_nlp(self, title):
        if not self.nlp or not title:
            return title
        doc = self.nlp(title)
        important_tokens = [t.text for t in doc if not t.is_stop and not t.is_punct and t.pos_ in ['NOUN','VERB','ADJ','PROPN']]
        return ' '.join(important_tokens) if important_tokens else title
    
    def calculate_confidence(self, date_info, time_info, title):
        score = 0.0
        if date_info.get('formatted_date'): score += 0.4
        if time_info.get('formatted_time'): score += 0.4
        if title and len(title.strip()) > 0: score += 0.2
        return min(score, 1.0)

