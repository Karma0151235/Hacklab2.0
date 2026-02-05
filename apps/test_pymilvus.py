
try:
    from pymilvus import connections, Collection
    print("pymilvus imported successfully")
    try:
        connections.connect("default", host="localhost", port="19530", timeout=2)
        print("Connected (unexpected)")
    except Exception as e:
        print(f"Connection failed as expected: {e}")
except Exception as e:
    print(f"Import failed: {e}")
