from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Start periodic task when explicitly enabled
        # Use file-based lock to prevent duplicate execution in both dev and production
        if os.environ.get("ENABLE_PERIODIC_TASK") == "true":
            lock_file = "/tmp/periodic_task.lock"
            current_pid = os.getpid()
            
            try:
                # Check if lock file exists and if the process that created it is still running
                if os.path.exists(lock_file):
                    try:
                        with open(lock_file, 'r') as f:
                            lock_content = f.read().strip()
                        
                        # Extract PID from lock content
                        if lock_content.startswith("locked_by_pid_"):
                            lock_pid = int(lock_content.split("_")[-1])
                            
                            # Check if the process that created the lock is still running
                            try:
                                os.kill(lock_pid, 0)  # Signal 0 just checks if process exists
                                # Process is still running, don't start new periodic task
                                return
                            except OSError:
                                # Process is dead, remove stale lock
                                os.remove(lock_file)
                    except (ValueError, IndexError, IOError):
                        # Lock file is corrupted, remove it
                        os.remove(lock_file)
                
                # Try to create lock file (atomic operation)
                with open(lock_file, 'x') as f:
                    f.write(f"locked_by_pid_{current_pid}")
                
                # Lock acquired successfully, start periodic task
                from .tasks import start_periodic_task
                start_periodic_task()
                
            except FileExistsError:
                # Lock already exists and process is still running
                pass
            except Exception as e:
                # Log error but don't crash the app
                print(f"Warning: Could not create periodic task lock: {e}")
