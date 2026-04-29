import boto3
from decimal import Decimal
import os

TABLE_NAME = os.environ.get("PRODUCTS_TABLE", "products_table_guru")
dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table(TABLE_NAME)

expanded_products = [
    # Books
    {"id": "1", "name": "All That We See or Seem", "price": 5000, "category": "Books", "stock_quantity": 15, "description": "A captivating novel exploring the depths of human perception and reality.", "rating": 4.5},
    {"id": "2", "name": "All The Way to the River", "price": 2000, "category": "Books", "stock_quantity": 8, "description": "An adventurous tale of self-discovery and the journey of life.", "rating": 4.2},
    {"id": "3", "name": "The Antidote", "price": 3000, "category": "Books", "stock_quantity": 12, "description": "A philosophical exploration of happiness and the human condition.", "rating": 4.7},
    {"id": "4", "name": "Atmosphere", "price": 2100, "category": "Books", "stock_quantity": 20, "description": "A scientific journey through Earth's atmosphere and climate.", "rating": 4.3},
    {"id": "5", "name": "Audition", "price": 3500, "category": "Books", "stock_quantity": 6, "description": "A thrilling story about ambition, talent, and the entertainment industry.", "rating": 4.1},
    {"id": "6", "name": "The Silent Patient", "price": 4200, "category": "Books", "stock_quantity": 30, "description": "A shocking psychological thriller.", "rating": 4.8},
    {"id": "7", "name": "Atomic Habits", "price": 3800, "category": "Books", "stock_quantity": 50, "description": "Tiny changes, remarkable results.", "rating": 4.9},
    {"id": "8", "name": "Dune", "price": 4500, "category": "Books", "stock_quantity": 15, "description": "A masterpiece of science fiction.", "rating": 4.7},
    
    # Electronics
    {"id": "9", "name": "Wireless Bluetooth Headphones", "price": 15000, "category": "Electronics", "stock_quantity": 25, "description": "Premium noise-cancelling wireless headphones with 30-hour battery life.", "rating": 4.6},
    {"id": "10", "name": "Smart Fitness Watch", "price": 25000, "category": "Electronics", "stock_quantity": 10, "description": "Advanced fitness tracker with heart rate monitoring and GPS.", "rating": 4.4},
    {"id": "11", "name": "Wireless Charging Pad", "price": 3000, "category": "Electronics", "stock_quantity": 22, "description": "Fast wireless charging pad compatible with all Qi-enabled devices.", "rating": 4.1},
    {"id": "12", "name": "4K Action Camera", "price": 45000, "category": "Electronics", "stock_quantity": 15, "description": "Waterproof 4K action camera with stabilization.", "rating": 4.5},
    {"id": "13", "name": "Mechanical Keyboard", "price": 8500, "category": "Electronics", "stock_quantity": 12, "description": "RGB mechanical keyboard with tactile switches.", "rating": 4.7},
    {"id": "14", "name": "Ergonomic Mouse", "price": 4200, "category": "Electronics", "stock_quantity": 40, "description": "Wireless ergonomic mouse for long work hours.", "rating": 4.3},
    {"id": "15", "name": "Portable Power Bank", "price": 2500, "category": "Electronics", "stock_quantity": 60, "description": "20000mAh portable charger with fast charging.", "rating": 4.2},
    {"id": "16", "name": "Noise Cancelling Earbuds", "price": 12000, "category": "Electronics", "stock_quantity": 20, "description": "True wireless earbuds with active noise cancellation.", "rating": 4.6},

    # Clothing
    {"id": "17", "name": "Organic Cotton T-Shirt", "price": 2500, "category": "Clothing", "stock_quantity": 50, "description": "Comfortable, eco-friendly t-shirt made from 100% organic cotton.", "rating": 4.0},
    {"id": "18", "name": "Denim Jacket", "price": 6500, "category": "Clothing", "stock_quantity": 15, "description": "Classic vintage style denim jacket.", "rating": 4.5},
    {"id": "19", "name": "Running Shorts", "price": 1800, "category": "Clothing", "stock_quantity": 40, "description": "Lightweight and breathable running shorts.", "rating": 4.3},
    {"id": "20", "name": "Wool Beanie", "price": 1200, "category": "Clothing", "stock_quantity": 35, "description": "Warm merino wool beanie for winter.", "rating": 4.7},
    {"id": "21", "name": "Athletic Sneakers", "price": 8000, "category": "Clothing", "stock_quantity": 25, "description": "High-performance sneakers for running and training.", "rating": 4.6},
    {"id": "22", "name": "Leather Wallet", "price": 3500, "category": "Clothing", "stock_quantity": 20, "description": "Genuine leather bi-fold wallet.", "rating": 4.4},

    # Home & Kitchen
    {"id": "23", "name": "Ceramic Coffee Mug", "price": 800, "category": "Home & Kitchen", "stock_quantity": 30, "description": "Handcrafted ceramic mug perfect for your morning coffee ritual.", "rating": 4.2},
    {"id": "24", "name": "Stainless Steel Water Bottle", "price": 1200, "category": "Home & Kitchen", "stock_quantity": 40, "description": "Insulated stainless steel bottle that keeps drinks cold for 24 hours.", "rating": 4.3},
    {"id": "25", "name": "French Press Maker", "price": 2200, "category": "Home & Kitchen", "stock_quantity": 15, "description": "Glass and stainless steel french press coffee maker.", "rating": 4.6},
    {"id": "26", "name": "Cast Iron Skillet", "price": 4500, "category": "Home & Kitchen", "stock_quantity": 10, "description": "Pre-seasoned 10-inch cast iron skillet.", "rating": 4.8},
    {"id": "27", "name": "Aromatherapy Diffuser", "price": 2800, "category": "Home & Kitchen", "stock_quantity": 25, "description": "Ultrasonic essential oil diffuser with LED lights.", "rating": 4.4},
    {"id": "28", "name": "Bamboo Cutting Board", "price": 1500, "category": "Home & Kitchen", "stock_quantity": 30, "description": "Durable and eco-friendly bamboo cutting board.", "rating": 4.5},

    # Sports & Fitness
    {"id": "29", "name": "Yoga Mat Premium", "price": 4500, "category": "Sports & Fitness", "stock_quantity": 18, "description": "Non-slip, eco-friendly yoga mat with excellent cushioning.", "rating": 4.5},
    {"id": "30", "name": "Dumbbell Set", "price": 5500, "category": "Sports & Fitness", "stock_quantity": 10, "description": "Adjustable dumbbell set for home workouts.", "rating": 4.7},
    
    # New Premium Products (Added for Redesign)
    {"id": "31", "name": "Ultra-Wide Monitor", "price": 45000, "category": "Electronics", "stock_quantity": 8, "description": "34-inch curved ultra-wide monitor for immersive gaming and productivity.", "rating": 4.8},
    {"id": "32", "name": "Mechanical Watch", "price": 12500, "category": "Clothing", "stock_quantity": 15, "description": "Elegant automatic mechanical watch with sapphire crystal.", "rating": 4.6},
    {"id": "33", "name": "Smart Speaker Hub", "price": 8900, "category": "Electronics", "stock_quantity": 25, "description": "Voice-controlled smart home hub with premium 360-degree sound.", "rating": 4.4},
    {"id": "34", "name": "Cashmere Sweater", "price": 15000, "category": "Clothing", "stock_quantity": 12, "description": "100% pure cashmere sweater, incredibly soft and warm.", "rating": 4.9},
    {"id": "35", "name": "Espresso Machine", "price": 32000, "category": "Home & Kitchen", "stock_quantity": 5, "description": "Professional-grade home espresso machine with milk frother.", "rating": 4.7},
    {"id": "36", "name": "Resistance Band Set", "price": 1800, "category": "Sports & Fitness", "stock_quantity": 40, "description": "Set of 5 premium fabric resistance bands for full-body workouts.", "rating": 4.3},
    {"id": "37", "name": "The Art of War", "price": 1200, "category": "Books", "stock_quantity": 35, "description": "Ancient Chinese military treatise attributed to Sun Tzu.", "rating": 4.5},
    {"id": "38", "name": "Drone with 4K Camera", "price": 55000, "category": "Electronics", "stock_quantity": 6, "description": "Foldable drone with 3-axis gimbal and 4K camera.", "rating": 4.8},
    {"id": "39", "name": "Silk Pillowcase", "price": 2500, "category": "Home & Kitchen", "stock_quantity": 20, "description": "100% mulberry silk pillowcase for skin and hair care.", "rating": 4.6},
    {"id": "40", "name": "Adjustable Kettlebell", "price": 6500, "category": "Sports & Fitness", "stock_quantity": 12, "description": "Space-saving adjustable kettlebell ranging from 5 to 40 lbs.", "rating": 4.7},
]

def seed_products():
    try:
        print(f"Seeding {len(expanded_products)} products into {TABLE_NAME}...")
        
        with product_table.batch_writer() as batch:
            for product in expanded_products:
                batch.put_item(Item={
                    "id": str(product["id"]),
                    "name": product["name"],
                    "price": int(product["price"]),
                    "category": product["category"],
                    "stock_quantity": int(product["stock_quantity"]),
                    "description": product["description"],
                    "rating": Decimal(str(product["rating"]))
                })
                
        print("Seeding completed ✅")

    except Exception as e:
        print(f"ERROR seeding products: {str(e)}")

if __name__ == "__main__":
    # Ensure AWS credentials/region are configured locally or via IAM roles
    seed_products()
