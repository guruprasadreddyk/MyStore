import boto3
from decimal import Decimal
import os

TABLE_NAME  = os.environ.get("PRODUCTS_TABLE", "products_table_guru")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "idp-sbx-trn-lab-01")
AWS_REGION  = os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1")

session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
dynamodb = session.resource("dynamodb")
product_table = dynamodb.Table(TABLE_NAME)

expanded_products = [
    # Books — priced as per Amazon India / Flipkart estimates
    {"id": "1",  "name": "All That We See or Seem",        "price": 399,    "category": "Books",           "stock_quantity": 15, "description": "A captivating novel exploring the depths of human perception and reality.",                          "rating": 4.5, "review_count": 128},
    {"id": "2",  "name": "All The Way to the River",       "price": 299,    "category": "Books",           "stock_quantity": 8,  "description": "An adventurous tale of self-discovery and the journey of life.",                                    "rating": 4.2, "review_count": 74},
    {"id": "3",  "name": "The Antidote",                   "price": 499,    "category": "Books",           "stock_quantity": 12, "description": "A philosophical exploration of happiness and the human condition.",                                 "rating": 4.7, "review_count": 312},
    {"id": "4",  "name": "Atmosphere",                     "price": 349,    "category": "Books",           "stock_quantity": 20, "description": "A scientific journey through Earth's atmosphere and climate.",                                      "rating": 4.3, "review_count": 89},
    {"id": "5",  "name": "Audition",                       "price": 449,    "category": "Books",           "stock_quantity": 6,  "description": "A thrilling story about ambition, talent, and the entertainment industry.",                         "rating": 4.1, "review_count": 56},
    {"id": "6",  "name": "The Silent Patient",             "price": 399,    "category": "Books",           "stock_quantity": 30, "description": "A shocking psychological thriller.",                                                                "rating": 4.8, "review_count": 2841},
    {"id": "7",  "name": "Atomic Habits",                  "price": 499,    "category": "Books",           "stock_quantity": 50, "description": "Tiny changes, remarkable results.",                                                                 "rating": 4.9, "review_count": 5623},
    {"id": "8",  "name": "Dune",                           "price": 599,    "category": "Books",           "stock_quantity": 15, "description": "A masterpiece of science fiction.",                                                                 "rating": 4.7, "review_count": 1892},
    {"id": "37", "name": "The Art of War",                 "price": 199,    "category": "Books",           "stock_quantity": 35, "description": "Ancient Chinese military treatise attributed to Sun Tzu.",                                         "rating": 4.5, "review_count": 743},

    # Electronics — priced as per Indian market (Amazon.in / Croma estimates)
    {"id": "9",  "name": "Wireless Bluetooth Headphones",  "price": 2999,   "category": "Electronics",     "stock_quantity": 25, "description": "Premium noise-cancelling wireless headphones with 30-hour battery life.",                          "rating": 4.6, "review_count": 1247},
    {"id": "10", "name": "Smart Fitness Watch",            "price": 4999,   "category": "Electronics",     "stock_quantity": 10, "description": "Advanced fitness tracker with heart rate monitoring and GPS.",                                    "rating": 4.4, "review_count": 892},
    {"id": "11", "name": "Wireless Charging Pad",          "price": 999,    "category": "Electronics",     "stock_quantity": 22, "description": "Fast wireless charging pad compatible with all Qi-enabled devices.",                              "rating": 4.1, "review_count": 534},
    {"id": "12", "name": "4K Action Camera",               "price": 24999,  "category": "Electronics",     "stock_quantity": 15, "description": "Waterproof 4K action camera with stabilization.",                                                "rating": 4.5, "review_count": 678},
    {"id": "13", "name": "Mechanical Keyboard",            "price": 3499,   "category": "Electronics",     "stock_quantity": 12, "description": "RGB mechanical keyboard with tactile switches.",                                                  "rating": 4.7, "review_count": 1103},
    {"id": "14", "name": "Ergonomic Mouse",                "price": 1799,   "category": "Electronics",     "stock_quantity": 40, "description": "Wireless ergonomic mouse for long work hours.",                                                   "rating": 4.3, "review_count": 765},
    {"id": "15", "name": "Portable Power Bank",            "price": 1299,   "category": "Electronics",     "stock_quantity": 60, "description": "20000mAh portable charger with fast charging.",                                                   "rating": 4.2, "review_count": 2341},
    {"id": "16", "name": "Noise Cancelling Earbuds",       "price": 5999,   "category": "Electronics",     "stock_quantity": 20, "description": "True wireless earbuds with active noise cancellation.",                                          "rating": 4.6, "review_count": 1567},
    {"id": "31", "name": "Ultra-Wide Monitor",             "price": 34999,  "category": "Electronics",     "stock_quantity": 8,  "description": "34-inch curved ultra-wide monitor for immersive gaming and productivity.",                        "rating": 4.8, "review_count": 423},
    {"id": "33", "name": "Smart Speaker Hub",              "price": 3499,   "category": "Electronics",     "stock_quantity": 25, "description": "Voice-controlled smart home hub with premium 360-degree sound.",                                  "rating": 4.4, "review_count": 987},
    {"id": "38", "name": "Drone with 4K Camera",           "price": 44999,  "category": "Electronics",     "stock_quantity": 6,  "description": "Foldable drone with 3-axis gimbal and 4K camera.",                                               "rating": 4.8, "review_count": 312},

    # Clothing — priced as per Myntra / Ajio estimates
    {"id": "17", "name": "Organic Cotton T-Shirt",         "price": 699,    "category": "Clothing",        "stock_quantity": 50, "description": "Comfortable, eco-friendly t-shirt made from 100% organic cotton.",                               "rating": 4.0, "review_count": 1823},
    {"id": "18", "name": "Denim Jacket",                   "price": 2499,   "category": "Clothing",        "stock_quantity": 15, "description": "Classic vintage style denim jacket.",                                                            "rating": 4.5, "review_count": 634},
    {"id": "19", "name": "Running Shorts",                 "price": 799,    "category": "Clothing",        "stock_quantity": 40, "description": "Lightweight and breathable running shorts.",                                                      "rating": 4.3, "review_count": 912},
    {"id": "20", "name": "Wool Beanie",                    "price": 499,    "category": "Clothing",        "stock_quantity": 35, "description": "Warm merino wool beanie for winter.",                                                            "rating": 4.7, "review_count": 445},
    {"id": "21", "name": "Athletic Sneakers",              "price": 3499,   "category": "Clothing",        "stock_quantity": 25, "description": "High-performance sneakers for running and training.",                                            "rating": 4.6, "review_count": 1234},
    {"id": "22", "name": "Leather Wallet",                 "price": 999,    "category": "Clothing",        "stock_quantity": 20, "description": "Genuine leather bi-fold wallet.",                                                                "rating": 4.4, "review_count": 567},
    {"id": "32", "name": "Mechanical Watch",               "price": 8999,   "category": "Clothing",        "stock_quantity": 15, "description": "Elegant automatic mechanical watch with sapphire crystal.",                                      "rating": 4.6, "review_count": 289},
    {"id": "34", "name": "Cashmere Sweater",               "price": 4999,   "category": "Clothing",        "stock_quantity": 12, "description": "100% pure cashmere sweater, incredibly soft and warm.",                                         "rating": 4.9, "review_count": 178},

    # Home & Kitchen — priced as per Amazon India estimates
    {"id": "23", "name": "Ceramic Coffee Mug",             "price": 349,    "category": "Home & Kitchen",  "stock_quantity": 30, "description": "Handcrafted ceramic mug perfect for your morning coffee ritual.",                               "rating": 4.2, "review_count": 2156},
    {"id": "24", "name": "Stainless Steel Water Bottle",   "price": 599,    "category": "Home & Kitchen",  "stock_quantity": 40, "description": "Insulated stainless steel bottle that keeps drinks cold for 24 hours.",                        "rating": 4.3, "review_count": 3421},
    {"id": "25", "name": "French Press Maker",             "price": 1299,   "category": "Home & Kitchen",  "stock_quantity": 15, "description": "Glass and stainless steel french press coffee maker.",                                         "rating": 4.6, "review_count": 876},
    {"id": "26", "name": "Cast Iron Skillet",              "price": 1999,   "category": "Home & Kitchen",  "stock_quantity": 10, "description": "Pre-seasoned 10-inch cast iron skillet.",                                                      "rating": 4.8, "review_count": 1432},
    {"id": "27", "name": "Aromatherapy Diffuser",          "price": 1499,   "category": "Home & Kitchen",  "stock_quantity": 25, "description": "Ultrasonic essential oil diffuser with LED lights.",                                           "rating": 4.4, "review_count": 723},
    {"id": "28", "name": "Bamboo Cutting Board",           "price": 699,    "category": "Home & Kitchen",  "stock_quantity": 30, "description": "Durable and eco-friendly bamboo cutting board.",                                               "rating": 4.5, "review_count": 1089},
    {"id": "35", "name": "Espresso Machine",               "price": 12999,  "category": "Home & Kitchen",  "stock_quantity": 5,  "description": "Professional-grade home espresso machine with milk frother.",                                  "rating": 4.7, "review_count": 234},
    {"id": "39", "name": "Silk Pillowcase",                "price": 999,    "category": "Home & Kitchen",  "stock_quantity": 20, "description": "100% mulberry silk pillowcase for skin and hair care.",                                        "rating": 4.6, "review_count": 567},

    # Sports & Fitness — priced as per Decathlon India / Amazon estimates
    {"id": "29", "name": "Yoga Mat Premium",               "price": 1299,   "category": "Sports & Fitness","stock_quantity": 18, "description": "Non-slip, eco-friendly yoga mat with excellent cushioning.",                                    "rating": 4.5, "review_count": 2341},
    {"id": "30", "name": "Dumbbell Set",                   "price": 2499,   "category": "Sports & Fitness","stock_quantity": 10, "description": "Adjustable dumbbell set for home workouts.",                                                   "rating": 4.7, "review_count": 1123},
    {"id": "36", "name": "Resistance Band Set",            "price": 599,    "category": "Sports & Fitness","stock_quantity": 40, "description": "Set of 5 premium fabric resistance bands for full-body workouts.",                             "rating": 4.3, "review_count": 1876},
    {"id": "40", "name": "Adjustable Kettlebell",          "price": 2999,   "category": "Sports & Fitness","stock_quantity": 12, "description": "Space-saving adjustable kettlebell ranging from 5 to 40 lbs.",                                "rating": 4.7, "review_count": 445},
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
                    "rating": Decimal(str(product["rating"])),
                    "review_count": int(product["review_count"])
                })
                
        print("Seeding completed ✅")

    except Exception as e:
        print(f"ERROR seeding products: {str(e)}")

if __name__ == "__main__":
    # Ensure AWS credentials/region are configured locally or via IAM roles
    seed_products()
