"""
🎯 Background Tasks Service
Manages scheduled tasks and background processing
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional

from app.services.tcgdex_data_fetcher import sync_tcgdex_data

logger = structlog.get_logger(__name__)

class BackgroundTaskManager:
    """Manages background tasks and scheduled operations"""
    
    def __init__(self):
        self.tasks = []
        self.running = False
        self.last_tcgdex_sync = None
    
    async def start(self):
        """Start background task processing"""
        self.running = True
        
        # Start TCGdex data sync task
        sync_task = asyncio.create_task(self._tcgdex_sync_scheduler())
        self.tasks.append(sync_task)
        
        logger.info("Background task manager started with TCGdex sync scheduler")
    
    async def stop(self):
        """Stop background task processing"""
        self.running = False
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Background task manager stopped")
    
    async def _tcgdex_sync_scheduler(self):
        """Schedule periodic TCGdex data synchronization"""
        logger.info("Starting TCGdex sync scheduler")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Sync every 6 hours or on first run
                should_sync = (
                    self.last_tcgdex_sync is None or 
                    (current_time - self.last_tcgdex_sync) > timedelta(hours=6)
                )
                
                if should_sync:
                    logger.info("Starting scheduled TCGdex data sync")
                    synced_count = await sync_tcgdex_data(limit=20)  # Limit to 20 sets to avoid overload
                    logger.info(f"Scheduled TCGdex sync completed: {synced_count} sets synced")
                    self.last_tcgdex_sync = current_time
                
                # Wait 30 minutes before checking again
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in TCGdex sync scheduler: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def force_tcgdex_sync(self, limit: Optional[int] = None) -> int:
        """Force immediate TCGdex data synchronization"""
        try:
            logger.info(f"Force syncing TCGdex data (limit: {limit})")
            synced_count = await sync_tcgdex_data(limit=limit)
            self.last_tcgdex_sync = datetime.utcnow()
            logger.info(f"Force TCGdex sync completed: {synced_count} sets synced")
            return synced_count
        except Exception as e:
            logger.error(f"Force TCGdex sync failed: {str(e)}")
            raise

# Global instance
background_task_manager = BackgroundTaskManager()