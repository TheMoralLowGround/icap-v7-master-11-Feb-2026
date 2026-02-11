import hashlib
import os
import threading
import time
from core.models import PostProcess, PromptDictionary
from core.services.code_generator import CodeGenerator


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def update_postprocess_cron():
    """
    1. get all prompts from the prompt dictionary
    2. for each prompt, get the hash from the prompt dictionary table
    3. take the process name from the prompt dictionary table
    4. get postprocess record using the process name
    5. compare the hash from the postprocess table with the hash from the prompt dictionary table
    6. if hash doesnt match, delete the record from postprocess table
    7. generate the new code and save it to the postprocess table
    """
    prompts = PromptDictionary.objects.exclude(prompt__isnull=True).exclude(prompt="")
    print(f"Processing {prompts.count()} prompts from PromptDictionary")

    for prompt_entry in prompts:
        process_name = prompt_entry.name
        prompt_hash = prompt_entry.unique_hash

        postprocess = (
            PostProcess.objects.filter(process=process_name)
            .order_by("-created_at")
            .first()
        )
        postprocess_hash = postprocess.unique_hash if postprocess else None

        if postprocess_hash == prompt_hash:
            print(f"  - {process_name}: Hash matches, skipping")
            continue

        if postprocess and postprocess_hash != prompt_hash:
            # Get all postprocess records for this process, ordered by creation date
            all_records = PostProcess.objects.filter(process=process_name).order_by('-created_at')
            
            # Keep only the last 3 records, delete the rest
            if all_records.count() >= 3:
                records_to_delete = all_records[2:]  # Delete everything except the first 3 (newest)
                for record in records_to_delete:
                    record.delete()
                print(f"  - {process_name}: Deleted {records_to_delete.count()} old records, keeping last 3")

        print(f"  - {process_name}: Generating new code...")
        generator = CodeGenerator()
        generated_code = generator.generate(prompt_entry.prompt)

        PostProcess.objects.create(
            prompt=prompt_entry.prompt,
            code=generated_code,
            process=process_name,
        )
        print(f"  - {process_name}: New code generated and saved")


def start_periodic_task():
    """Start the periodic task in a daemon thread"""
    interval_seconds = int(os.getenv("RUN_INTERVAL_SECONDS", "30"))

    def run():
        while True:
            try:
                update_postprocess_cron()
            except Exception as e:
                print(f"Periodic task error: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"Started periodic prompt scheduler task (interval: {interval_seconds}s)")
