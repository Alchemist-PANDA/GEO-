import json

def generate_json_ld(brand_name, product_info):
    """
    Generates a valid JSON-LD string for a schema.org/Product or LocalBusiness.

    Args:
        brand_name (str): The name of the brand.
        product_info (dict): A dictionary containing keys: name, description, price, address, telephone.

    Returns:
        str: A JSON-LD formatted string.
    """
    # Decide whether to use Product or LocalBusiness based on available info
    # For this implementation, we'll create a Product with an embedded Offer
    # and potentially include LocalBusiness information if relevant.

    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product_info.get("name"),
        "description": product_info.get("description"),
        "brand": {
            "@type": "Brand",
            "name": brand_name
        },
        "offers": {
            "@type": "Offer",
            "price": product_info.get("price"),
            "priceCurrency": "USD", # Defaulting to USD, could be parameterized
            "availability": "https://schema.org/InStock"
        }
    }

    # If address or telephone are provided, we can add a LocalBusiness/Seller info
    if product_info.get("address") or product_info.get("telephone"):
        schema["offers"]["seller"] = {
            "@type": "LocalBusiness",
            "name": brand_name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": product_info.get("address")
            },
            "telephone": product_info.get("telephone")
        }

    return json.dumps(schema, indent=2)

if __name__ == "__main__":
    # Test block
    brand = "EcoFriendly Gear"
    product = {
        "name": "Bamboo Water Bottle",
        "description": "A sustainable 500ml water bottle made from natural bamboo.",
        "price": "25.00",
        "address": "123 Green Way, Eco City, CA 90210",
        "telephone": "+1-555-0199"
    }

    json_ld_output = generate_json_ld(brand, product)
    print("Generated JSON-LD:")
    print(json_ld_output)
