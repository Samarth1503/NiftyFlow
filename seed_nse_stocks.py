import asyncio
import csv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import engine, AsyncSessionLocal
from backend.models.security import Security

async def seed_stocks():
    print("Loading stocks from CSV...")
    
    # Read the CSV
    stocks = []
    with open("nse_equities.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        for row in reader:
            if len(row) >= 2:
                symbol = row[0].strip()
                name = row[1].strip()
                stocks.append({"symbol": symbol, "name": name, "exchange": "NSE"})
                
    print(f"Found {len(stocks)} stocks. Inserting into database...")
    
    async with AsyncSessionLocal() as session:
        # Get existing stocks to avoid duplicates
        result = await session.execute(select(Security.symbol))
        existing_symbols = {row[0] for row in result.all()}
        
        new_stocks = [
            Security(symbol=s["symbol"], name=s["name"], exchange=s["exchange"])
            for s in stocks if s["symbol"] not in existing_symbols
        ]
        
        if new_stocks:
            session.add_all(new_stocks)
            await session.commit()
            print(f"Successfully added {len(new_stocks)} new stocks!")
        else:
            print("No new stocks to add. Database is already up to date.")

if __name__ == "__main__":
    asyncio.run(seed_stocks())
