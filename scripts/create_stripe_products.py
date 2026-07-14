import os

import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

TIERS = {
    "starter": {"name": "Starter", "price": 2900, "desc": "ChatGPT + Gemini, 50 audits/month"},
    "professional": {"name": "Professional", "price": 4900, "desc": "ChatGPT + Gemini + Claude, 150 audits/month"},
    "business": {"name": "Business", "price": 9900, "desc": "5 AI models, 500 audits/month"},
}

def main():
    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY is not set in .env")
        return

    for tier_id, config in TIERS.items():
        try:
            # Create product
            product = stripe.Product.create(
                name=config["name"],
                description=config["desc"],
                metadata={"tier": tier_id}
            )

            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=config["price"],
                currency="usd",
                recurring={"interval": "month"},
                lookup_key=f"price_{tier_id}",
            )

            print(f"✅ Created {config['name']}: {price.id}")
        except Exception as e:
            print(f"Error creating {config['name']}: {e}")

if __name__ == "__main__":
    main()
