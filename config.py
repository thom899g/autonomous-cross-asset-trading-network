"""
Configuration management for the trading network.
Centralized config with environment variable fallbacks.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ExchangeConfig:
    """Exchange-specific configuration"""
    name: str
    api_key: str
    secret: str
    sandbox: bool = True
    rate_limit: int = 1000  # ms between requests

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    type: str = "service_account"

@dataclass
class ModelConfig:
    """ML model configuration"""
    retrain_interval_hours: int = 24
    prediction_horizon_minutes: int = 15
    confidence_threshold: float = 0.65

@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size_usd: float = 1000.0
    max_daily_loss_percent: float = 2.0
    stop_loss_percent: float = 1.5
    max_open_positions: int = 5

class TradingConfig:
    """Main configuration singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration with environment variables"""
        # Firebase config
        self.firebase = FirebaseConfig(
            project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
            private_key_id=os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            private_key=os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            client_email=os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            client_id=os.getenv("FIREBASE_CLIENT_ID", "")
        )
        
        # Exchange configs
        self.exchanges: Dict[str, ExchangeConfig] = {}
        
        # Binance config
        binance_key = os.getenv("BINANCE_API_KEY")
        binance_secret = os.getenv("BINANCE_API_SECRET")
        if binance_key and binance_secret:
            self.exchanges["binance"] = ExchangeConfig(
                name="binance",
                api_key=binance_key,
                secret=binance_secret,
                sandbox=os.getenv("BINANCE_SANDBOX", "True") == "True"
            )
        
        # Alpaca config (for traditional assets)
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_API_SECRET")
        if alpaca_key and alpaca_secret:
            self.exchanges["alpaca"] = ExchangeConfig(
                name="alpaca",
                api_key=alpaca_key,
                secret=alpaca_secret,
                sandbox=os.getenv("ALPACA_SANDBOX", "True") == "True"
            )
        
        # Model config
        self.model = ModelConfig()
        
        # Risk config
        self.risk = RiskConfig()
        
        # Logging config
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate critical config
        self._validate()
    
    def _validate(self):
        """Validate critical configuration"""
        if not self.firebase.project_id:
            logging.warning("Firebase project ID not configured")
        
        if not self.exchanges:
            logging.warning("No exchange configurations found")
        
        # Check for required environment variables
        required_vars = ["FIREBASE_PROJECT_ID"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            logging.error(f"Missing required environment variables: {missing}")
    
    def get_exchange_config(self, exchange_name: str) -> Optional[ExchangeConfig]:
        """Get exchange config by name"""
        return self.exchanges.get(exchange_name.lower())
    
    def is_production(self) -> bool:
        """Check if any exchange is in production mode"""
        return any(not exchange.sandbox for exchange in self.exchanges.values())

# Global config instance
config = TradingConfig()