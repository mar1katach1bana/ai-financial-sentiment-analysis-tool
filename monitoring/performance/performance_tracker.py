import time
import psutil
from datetime import datetime
from collections import deque

class PerformanceTracker:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.cpu_usage = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.disk_io = deque(maxlen=window_size)
        self.network_io = deque(maxlen=window_size)
        self.last_update = datetime.now()
        
    def update(self):
        """Update performance metrics"""
        self.cpu_usage.append(psutil.cpu_percent())
        self.memory_usage.append(psutil.virtual_memory().percent)
        disk_io = psutil.disk_io_counters()
        self.disk_io.append((disk_io.read_bytes, disk_io.write_bytes))
        network_io = psutil.net_io_counters()
        self.network_io.append((network_io.bytes_sent, network_io.bytes_recv))
        self.last_update = datetime.now()
        
    def get_status(self):
        """Get current performance status"""
        return {
            'last_update': self.last_update,
            'cpu_usage': list(self.cpu_usage),
            'memory_usage': list(self.memory_usage),
            'disk_io': list(self.disk_io),
            'network_io': list(self.network_io),
            'avg_cpu': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
            'avg_memory': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        }
        
    def check_thresholds(self, cpu_threshold=90, memory_threshold=90):
        """Check if performance exceeds thresholds"""
        if self.cpu_usage and self.cpu_usage[-1] > cpu_threshold:
            return True
        if self.memory_usage and self.memory_usage[-1] > memory_threshold:
            return True
        return False
