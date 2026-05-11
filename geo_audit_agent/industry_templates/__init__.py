"""Industry-specific templates for GEO audit recommendations."""

from .fitness_gym import FitnessGymTemplate
from .ecommerce import EcommerceTemplate
from .dental_clinic import DentalClinicTemplate
from .restaurant import RestaurantTemplate

TEMPLATES = {
    'fitness_gym': FitnessGymTemplate,
    'ecommerce': EcommerceTemplate,
    'dental_clinic': DentalClinicTemplate,
    'restaurant': RestaurantTemplate,
}

def get_template(category: str):
    """Get industry template based on category."""
    category_lower = category.lower()

    # Check for ecommerce keywords
    ecommerce_keywords = [
        'ecommerce', 'e-commerce', 'online store', 'online shop', 'fashion store',
        'clothing store', 'shopify', 'retail', 'marketplace', 'skincare store',
        'electronics store', 'furniture store'
    ]
    if any(keyword in category_lower for keyword in ecommerce_keywords):
        return TEMPLATES['ecommerce']()

    # Check for fitness/gym keywords
    fitness_keywords = ['fitness', 'gym', 'health club', 'training', 'personal training']
    if any(keyword in category_lower for keyword in fitness_keywords):
        return TEMPLATES['fitness_gym']()

    # Check for dental keywords
    dental_keywords = ['dental', 'dentist', 'dental clinic', 'dental practice', 'tooth', 'oral health']
    if any(keyword in category_lower for keyword in dental_keywords):
        return TEMPLATES['dental_clinic']()

    # Check for restaurant keywords
    restaurant_keywords = [
        'restaurant', 'cafe', 'coffee shop', 'bakery', 'fast food',
        'burger restaurant', 'pizza restaurant', 'fine dining',
        'casual dining', 'food', 'takeaway', 'delivery restaurant',
        'desi restaurant', 'chinese restaurant', 'italian restaurant',
        'bbq restaurant', 'steakhouse'
    ]
    if any(keyword in category_lower for keyword in restaurant_keywords):
        return TEMPLATES['restaurant']()

    return None

__all__ = ['get_template', 'FitnessGymTemplate', 'EcommerceTemplate', 'DentalClinicTemplate', 'RestaurantTemplate', 'TEMPLATES']
