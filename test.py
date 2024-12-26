import psycopg as pg
from collections.abc import Sequence

connector = pg.connect(dbname="testdb", password="password", host="localhost", port="5432",
                           user="postgres", sslmode="prefer", connect_timeout="10")
cursor: pg.Cursor = connector.cursor()
cursor.execute("insert into flashcards values (default, %s, %s, %s, %s) returning id",
                   ["1", "2", "3", 's'])
cursor.connection.commit()
