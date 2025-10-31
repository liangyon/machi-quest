"""
Token Blacklist Service using Redis

Implements token revocation by maintaining a blacklist of invalidated tokens.
This allows immediate logout and token invalidation before natural expiration.
"""
import hashlib
from typing import Optional
import redis
from .config import settings


class TokenBlacklist:
    """
    Token blacklist using Redis for fast lookups.
    
    Tokens are hashed before storage to prevent token leakage if Redis is compromised.
    Tokens automatically expire from the blacklist when they would naturally expire.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection"""
        url = redis_url or settings.REDIS_URL
        if not url:
            raise ValueError("REDIS_URL must be configured for token blacklist")
        
        self.redis_client = redis.from_url(url, decode_responses=True)
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def revoke_token(self, token: str, expires_in_seconds: int):
        """
        Add token to blacklist until it would naturally expire.
        
        Args:
            token: The JWT token to revoke
            expires_in_seconds: How many seconds until the token naturally expires
        """
        token_hash = self._hash_token(token)
        # Store with expiration matching token's natural expiration
        self.redis_client.setex(
            f"blacklist:{token_hash}",
            expires_in_seconds,
            "1"
        )
    
    def is_revoked(self, token: str) -> bool:
        """
        Check if token is in the blacklist.
        
        Args:
            token: The JWT token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        token_hash = self._hash_token(token)
        return self.redis_client.exists(f"blacklist:{token_hash}") > 0
    
    def revoke_all_user_tokens(self, user_id: str, max_token_lifetime_seconds: int = 604800):
        """
        Revoke all tokens for a specific user.
        
        Useful for:
        - Password changes (invalidate all existing sessions)
        - Account compromise (force re-authentication)
        - Account deletion
        
        Args:
            user_id: The user's ID
            max_token_lifetime_seconds: Maximum lifetime of any token (default: 7 days)
        """
        # Store user ID in blacklist for the maximum possible token lifetime
        self.redis_client.setex(
            f"user_blacklist:{user_id}",
            max_token_lifetime_seconds,
            "1"
        )
    
    def is_user_blacklisted(self, user_id: str) -> bool:
        """
        Check if all of a user's tokens should be revoked.
        
        Args:
            user_id: The user's ID
            
        Returns:
            True if user is blacklisted, False otherwise
        """
        return self.redis_client.exists(f"user_blacklist:{user_id}") > 0


# Global instance
_token_blacklist: Optional[TokenBlacklist] = None


def get_token_blacklist() -> TokenBlacklist:
    """Get or create the global token blacklist instance"""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist
