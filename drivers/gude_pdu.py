import requests
import logging
import json

# Setup Logger
logger = logging.getLogger("Afara.Gude")

class GudePDU:
    def __init__(self, ip, username="admin", password=None):
        self.ip = ip
        self.auth = (username, password) if password else None
        # Standard Gude JSON endpoint
        self.url = f"http://{self.ip}/status.json"

    def get_sensors(self):
        """
        Fetches Real Temperature and Humidity from Gude PDU.
        """
        data = {
            "temp": None,
            "humidity": None,
            "error": None
        }

        try:
            # Short timeout for faster report
            response = requests.get(self.url, auth=self.auth, timeout=3)
            
            if response.status_code == 200:
                json_data = response.json()
                
                # Checks for sensor_values list in Gude JSON structure
                sensors = json_data.get("sensor_values", [])
                
                for s in sensors:
                    # Gude Type 1 = Temperature
                    if s.get("type") == 1:
                        data['temp'] = f"{s.get('value')}°C"
                    
                    # Gude Type 2 = Humidity
                    elif s.get("type") == 2:
                        data['humidity'] = f"{s.get('value')}%"
            else:
                data['error'] = f"HTTP {response.status_code}"

        except Exception as e:
            # If PDU cannot be reached, return None so the system falls back
            data['error'] = "Unreachable"
        
        return data