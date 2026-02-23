import time

def main():
    print("StreamForge Consumer Started")
    # TODO: Implement Redpanda consumer -> Polars -> MinIO logic
    while True:
        print("Waiting for events...")
        time.sleep(5)

if __name__ == "__main__":
    main()
