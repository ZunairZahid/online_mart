from aiokafka import AIOKafkaConsumer
import asyncio
import json





async def consume_product_created_events():
    consumer = AIOKafkaConsumer(
        'product-events',
        bootstrap_servers='localhost:9092',
        group_id="inventory-group"
    )
    
    await consumer.start()
    try:
        async for msg in consumer:
            event = json.loads(msg.value)
            if event['type'] == 'productCreated':
                product_id = event['data']['productId']
                product_name = event['data']['productName']
                
                # Initialize stock level to 0 or some predefined value
                stock_level = 0
                
                # Update the inventory database with this new product
                create_inventory_record(product_id, product_name, stock_level)
                
                print(f"New product created: {product_name} with ID {product_id}")
                
    finally:
        await consumer.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume_product_created_events())
