from database_worker import DatabaseWorker

if __name__ == "__main__":
    db_runner = DatabaseWorker()
    db_runner.initialize_database()
