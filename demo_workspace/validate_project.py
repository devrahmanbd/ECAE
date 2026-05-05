import asyncio
import os
from multi_separator import run_separator
from multi_contact_uploader import run_uploader

async def test_imports():
    print("Testing imports...")
    try:
        import aiogram
        import httpx
        import msal
        print("✅ Core dependencies imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import dependencies: {e}")
        return

    print("Testing multi_separator logic (dry run)...")
    # Create dummy data
    with open("test_all_data.txt", "w") as f:
        f.write("test1@example.com\ntest2@example.com\ntest3@example.com\n")
    
    with open("test_users.txt", "w") as f:
        f.write("user1\n")

    if not os.path.exists("test_storage"):
        os.makedirs("test_storage")

    try:
        # This will actually write to files, so we use test names
        await run_separator("test_users.txt", "test_all_data.txt", 1, "test_storage")
        print("✅ multi_separator dry run successful.")
    except Exception as e:
        print(f"❌ multi_separator failed: {e}")

    # Clean up
    for f in ["test_all_data.txt", "test_users.txt", "emails.txt"]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists("test_storage/user1.txt"):
        os.remove("test_storage/user1.txt")
    if os.path.exists("test_storage"):
        os.rmdir("test_storage")

if __name__ == "__main__":
    asyncio.run(test_imports())
