from dbcrawler.evaluation.snapshot import write_snapshot

if __name__ == "__main__":
    data = write_snapshot()
    print(f"wrote {len(data)} golden results")
