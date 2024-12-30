import numpy as np
from scipy.stats import ks_2samp
from collections import deque
from datetime import datetime

class DriftDetector:
    def __init__(self, window_size=1000, threshold=0.05):
        self.window_size = window_size
        self.threshold = threshold
        self.reference_window = deque(maxlen=window_size)
        self.current_window = deque(maxlen=window_size)
        self.last_drift_detected = None
        
    def update_reference(self, value):
        """Update reference window with new data"""
        self.reference_window.append(value)
        
    def update_current(self, value):
        """Update current window with new data"""
        self.current_window.append(value)
        
    def check_drift(self):
        """Check for data drift between reference and current windows"""
        if len(self.reference_window) < 100 or len(self.current_window) < 100:
            return False
            
        # Perform Kolmogorov-Smirnov test
        statistic, p_value = ks_2samp(
            np.array(self.reference_window),
            np.array(self.current_window)
        )
        
        if p_value < self.threshold:
            self.last_drift_detected = datetime.now()
            return True
            
        return False
        
    def get_status(self):
        """Get current drift detection status"""
        return {
            'reference_window_size': len(self.reference_window),
            'current_window_size': len(self.current_window),
            'last_drift_detected': self.last_drift_detected,
            'threshold': self.threshold
        }
