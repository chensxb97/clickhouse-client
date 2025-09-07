import clickhouse_connect

def main():
    # Connect to the ClickHouse server
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='password')

    # Create a database
    client.command('CREATE DATABASE IF NOT EXISTS test_db')

    # Use the database
    client.command('USE test_db')

    # Create a table
    client.command('''
        CREATE TABLE IF NOT EXISTS test_table (
            id UInt32,
            name String
        ) ENGINE = MergeTree()
        ORDER BY id
    ''')

    # Insert data into the table
    client.command("INSERT INTO test_table (id, name) VALUES (1, 'Alice'), (2, 'Bob')")

    # Query the data
    result = client.query('SELECT * FROM test_table')
    print(result.result_rows)

if __name__ == '__main__':
    main()