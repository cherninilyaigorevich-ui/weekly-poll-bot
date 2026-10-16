import os
import tempfile
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("GROUP_ID", "-100123")
os.environ.setdefault("TOPIC_ID", "10")
os.environ["STATE_PATH"] = tempfile.mktemp(suffix=".json")
