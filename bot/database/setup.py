import asqlite

async def setup_database(pool):
    query = """
    CREATE TABLE IF NOT EXISTS tokens(
        user_id TEXT PRIMARY KEY,
        token TEXT NOT NULL,
        refresh TEXT NOT NULL
    )
    """
    async with pool.acquire() as conn:
        await conn.execute(query)
        await conn.commit()

async def load_tokens(pool, add_token_func):
    async with pool.acquire() as conn:
        rows = await conn.fetchall("SELECT * FROM tokens")
    for row in rows:
        await add_token_func(row["token"], row["refresh"])