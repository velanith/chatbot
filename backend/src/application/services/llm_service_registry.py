"""LLM service registry for provider registration and configuration."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .llm_service_interface import (
    LLMServiceInterface,
    LLMServiceFactory,
    LLMServiceManager,
    LLMProvider,
    LLMModel
)
from .openrouter_service import OpenRouterService
from src.infrastructure.config import Settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    enabled: bool = True
    priority: int = 0  # Lower number = higher priority
    extra_config: Optional[Dict[str, Any]] = None


class LLMServiceRegistry:
    """Registry for managing LLM service providers."""
    
    def __init__(self):
        """Initialize the registry."""
        self._registered = False
        self._configs: List[LLMProviderConfig] = []
        self._services: List[LLMServiceInterface] = []
        self._manager: Optional[LLMServiceManager] = None
    
    def register_providers(self):
        """Register all available LLM service providers."""
        if self._registered:
            return
        
        # Register OpenRouter client (primary)
        LLMServiceFactory.register_service(LLMProvider.OPENROUTER, OpenRouterService)
        
        self._registered = True
        logger.info("LLM service providers registered")
    
    def configure_from_settings(self, settings: Settings) -> None:
        """Configure providers from application settings.
        
        Args:
            settings: Application settings
        """
        self._configs.clear()
        
        # Configure OpenRouter as primary LLM provider
        if getattr(settings, 'openrouter_api_key', None):
            openrouter_config = LLMProviderConfig(
                provider=LLMProvider.OPENROUTER,
                api_key=settings.openrouter_api_key,
                base_url=getattr(settings, 'openrouter_base_url', 'https://openrouter.ai/api/v1'),
                timeout=getattr(settings, 'openai_timeout', 30),
                max_retries=getattr(settings, 'openai_max_retries', 3),
                enabled=True,
                priority=0,  # Primary priority
                extra_config={
                    "app_name": getattr(settings, 'app_name', 'Polyglot'),
                    "app_url": "https://github.com/polyglot"
                }
            )
            self._configs.append(openrouter_config)
        
        # Sort by priority (lower number = higher priority)
        self._configs.sort(key=lambda x: x.priority)
        
        logger.info(f"Configured {len(self._configs)} LLM providers")
    
    def add_provider_config(self, config: LLMProviderConfig) -> None:
        """Add a provider configuration.
        
        Args:
            config: Provider configuration
        """
        self._configs.append(config)
        # Re-sort by priority
        self._configs.sort(key=lambda x: x.priority)
    
    def get_provider_configs(self) -> List[LLMProviderConfig]:
        """Get all provider configurations.
        
        Returns:
            List of provider configurations
        """
        return self._configs.copy()
    
    def get_enabled_configs(self) -> List[LLMProviderConfig]:
        """Get enabled provider configurations.
        
        Returns:
            List of enabled provider configurations
        """
        return [config for config in self._configs if config.enabled]
    
    async def create_services(self) -> List[LLMServiceInterface]:
        """Create service instances from configurations.
        
        Returns:
            List of LLM service instances
            
        Raises:
            ValueError: If no providers are configured
        """
        if not self._registered:
            self.register_providers()
        
        enabled_configs = self.get_enabled_configs()
        if not enabled_configs:
            raise ValueError("No enabled LLM providers configured")
        
        services = []
        
        for config in enabled_configs:
            try:
                # Prepare service arguments
                service_kwargs = {
                    "api_key": config.api_key,
                    "timeout": config.timeout,
                    "max_retries": config.max_retries,
                    "retry_delay": config.retry_delay,
                    "max_retry_delay": config.max_retry_delay
                }
                
                # Add base URL if specified
                if config.base_url:
                    service_kwargs["base_url"] = config.base_url
                
                # Add extra configuration
                if config.extra_config:
                    service_kwargs.update(config.extra_config)
                
                # Create service instance
                service = LLMServiceFactory.create_service(
                    config.provider,
                    **service_kwargs
                )
                
                # Test service availability
                if await service.is_available():
                    services.append(service)
                    logger.info(f"Created and verified {config.provider.value} service")
                else:
                    logger.warning(f"{config.provider.value} service is not available")
            
            except Exception as e:
                logger.error(f"Failed to create {config.provider.value} service: {str(e)}")
                continue
        
        if not services:
            raise ValueError("No LLM services are available")
        
        self._services = services
        return services
    
    async def get_service_manager(self) -> LLMServiceManager:
        """Get or create a service manager with all configured services.
        
        Returns:
            LLM service manager
            
        Raises:
            ValueError: If no services are available
        """
        if self._manager is None:
            if not self._services:
                await self.create_services()
            
            self._manager = LLMServiceManager(self._services)
            logger.info(f"Created LLM service manager with {len(self._services)} services")
        
        return self._manager
    
    async def get_primary_service(self) -> LLMServiceInterface:
        """Get the primary (highest priority) service.
        
        Returns:
            Primary LLM service
            
        Raises:
            ValueError: If no services are available
        """
        if not self._services:
            await self.create_services()
        
        return self._services[0]
    
    def get_service_by_provider(self, provider: LLMProvider) -> Optional[LLMServiceInterface]:
        """Get service by provider type.
        
        Args:
            provider: Provider type
            
        Returns:
            Service instance or None if not found
        """
        for service in self._services:
            if service.provider == provider:
                return service
        return None
    
    def get_service_for_model(self, model: LLMModel) -> Optional[LLMServiceInterface]:
        """Get the best service for a specific model.
        
        Args:
            model: Model to find service for
            
        Returns:
            Service that supports the model, or None
        """
        for service in self._services:
            if model in service.supported_models:
                return service
        return None
    
    def get_available_models(self) -> List[LLMModel]:
        """Get all available models from all services.
        
        Returns:
            List of available models
        """
        models = set()
        for service in self._services:
            models.update(service.supported_models)
        return list(models)
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all configured services.
        
        Returns:
            Dictionary mapping provider names to availability status
        """
        health_status = {}
        
        for service in self._services:
            try:
                is_available = await service.is_available()
                health_status[service.provider.value] = is_available
            except Exception as e:
                logger.error(f"Health check failed for {service.provider.value}: {str(e)}")
                health_status[service.provider.value] = False
        
        return health_status
    
    async def cleanup(self):
        """Cleanup all services."""
        for service in self._services:
            if hasattr(service, 'close'):
                try:
                    await service.close()
                except Exception as e:
                    logger.error(f"Error closing {service.provider.value} service: {str(e)}")
        
        self._services.clear()
        self._manager = None
        logger.info("LLM services cleaned up")


# Global registry instance
llm_registry = LLMServiceRegistry()


async def get_llm_service_manager(settings: Settings) -> LLMServiceManager:
    """Get configured LLM service manager.
    
    Args:
        settings: Application settings
        
    Returns:
        LLM service manager
    """
    llm_registry.configure_from_settings(settings)
    return await llm_registry.get_service_manager()


async def get_primary_llm_service(settings: Settings) -> LLMServiceInterface:
    """Get primary LLM service.
    
    Args:
        settings: Application settings
        
    Returns:
        Primary LLM service
    """
    llm_registry.configure_from_settings(settings)
    return await llm_registry.get_primary_service()