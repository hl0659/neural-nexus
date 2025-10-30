"""
Neural Nexus v3.0 - Signal Handler
Handles graceful shutdown on Ctrl+C
"""

import signal
import sys
from typing import Callable, Optional


class GracefulShutdown:
    """Handles graceful shutdown signals"""
    
    def __init__(self, shutdown_callback: Optional[Callable] = None):
        self.shutdown_requested = False
        self.shutdown_callback = shutdown_callback
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        if self.shutdown_requested:
            print("\n\n⚠️  Force shutdown requested!")
            print("Exiting immediately...")
            sys.exit(1)
        
        self.shutdown_requested = True
        print("\n\n⚠️  Shutdown requested (Ctrl+C detected)")
        print("Finishing current operations...")
        print("(Press Ctrl+C again to force quit)")
        
        if self.shutdown_callback:
            try:
                self.shutdown_callback()
            except Exception as e:
                print(f"Error during shutdown: {e}")
    
    def should_stop(self) -> bool:
        """Check if shutdown has been requested"""
        return self.shutdown_requested


if __name__ == "__main__":
    import time
    
    print("Testing Graceful Shutdown...")
    print("="*60)
    print("Press Ctrl+C to test graceful shutdown")
    print("(Press Ctrl+C twice to force quit)")
    
    def on_shutdown():
        print("  → Running cleanup tasks...")
        time.sleep(1)
        print("  → Saving progress...")
        time.sleep(1)
        print("  → Closing connections...")
        time.sleep(1)
        print("  ✓ Cleanup complete!")
    
    shutdown = GracefulShutdown(on_shutdown)
    
    try:
        count = 0
        while not shutdown.should_stop():
            count += 1
            print(f"Working... {count}")
            time.sleep(1)
    except SystemExit:
        pass
    
    print("\n✓ Graceful shutdown test complete!")