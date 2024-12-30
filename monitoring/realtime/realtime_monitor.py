import time
from datetime import datetime
from collections import deque
from core.models import PredictiveModel
from core.nlp import SentimentAnalyzer

class RealtimeMonitor:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.sentiment_scores = deque(maxlen=window_size)
        self.predictions = deque(maxlen=window_size)
        self.last_update = datetime.now()
        
    def update(self, sentiment_score, prediction):
        """Update monitor with new data"""
        self.sentiment_scores.append(sentiment_score)
        self.predictions.append(prediction)
        self.last_update = datetime.now()
        
    def get_status(self):
        """Get current monitoring status"""
        return {
            'last_update': self.last_update,
            'sentiment_window': list(self.sentiment_scores),
            'prediction_window': list(self.predictions),
            'avg_sentiment': sum(self.sentiment_scores) / len(self.sentiment_scores) if self.sentiment_scores else 0,
            'avg_prediction': sum(self.predictions) / len(self.predictions) if self.predictions else 0
        }
        
    def check_anomalies(self):
        """Check for anomalies in the data"""
        # Basic anomaly detection
        if len(self.sentiment_scores) < 2:
            return False
            
        last_sentiment = self.sentiment_scores[-1]
        avg_sentiment = sum(self.sentiment_scores) / len(self.sentiment_scores)
        
        return abs(last_sentiment - avg_sentiment) > 0.5  # Threshold for anomaly
