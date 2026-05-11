"""Restaurant industry template for GEO audit recommendations."""

class RestaurantTemplate:
    """Industry-specific template for restaurants, cafes, and food establishments."""

    def __init__(self):
        self.category_triggers = [
            'restaurant', 'cafe', 'coffee shop', 'bakery', 'fast food',
            'burger restaurant', 'pizza restaurant', 'fine dining',
            'casual dining', 'food', 'takeaway', 'delivery restaurant',
            'desi restaurant', 'chinese restaurant', 'italian restaurant',
            'bbq restaurant', 'steakhouse'
        ]

        self.recommendation_signals = [
            'google_rating',
            'review_count',
            'cuisine_type',
            'menu_clarity',
            'signature_dishes',
            'food_quality',
            'taste',
            'ambience',
            'service_quality',
            'hygiene_cleanliness',
            'family_friendly',
            'price_range',
            'location_convenience',
            'opening_hours',
            'delivery_availability',
            'reservation_availability',
            'food_photos',
            'social_media_presence',
            'gbp_completeness',
            'local_listicle_visibility',
        ]

        self.schema_recommendations = [
            'Restaurant',
            'Menu',
            'LocalBusiness',
            'FoodEstablishment',
            'AggregateRating',
            'Review',
            'OpeningHoursSpecification',
            'FAQPage',
        ]

        self.review_keywords = [
            'taste', 'delicious', 'food quality', 'fresh', 'ambience',
            'service', 'staff', 'clean', 'hygienic', 'family',
            'price', 'value', 'delivery', 'reservation', 'parking',
            'portion size', 'spicy', 'authentic'
        ]

        self.remediation_playbook = {
            'schema': {
                'priority': 'high',
                'actions': [
                    'Add Restaurant schema',
                    'Add Menu schema',
                    'Add LocalBusiness schema with food establishment fields',
                    'Add AggregateRating and Review schema',
                    'Add OpeningHoursSpecification schema',
                ],
            },
            'content': {
                'priority': 'high',
                'actions': [
                    'Create or optimize menu page with structured items',
                    'Add signature dish sections/pages with descriptions and photos',
                    'Add delivery and reservation information clearly',
                    'Add opening hours and price range',
                    'Add high-quality food and ambience photos',
                    'Add treatment FAQs' # Reusing generic label if needed or specific below
                ],
            },
            'reviews': {
                'priority': 'medium',
                'actions': [
                    'Collect reviews mentioning taste and food quality',
                    'Collect reviews mentioning service and staff',
                    'Collect reviews mentioning ambience and cleanliness',
                    'Collect reviews mentioning value for money',
                ],
            },
            'local_seo': {
                'priority': 'high',
                'actions': [
                    'Improve Google Business Profile with menu and food photos',
                    'Update service list on Google Business Profile',
                    'Create "Best [cuisine] restaurant in [city]" content',
                    'Create local comparison content',
                ],
            },
        }

    def get_context_text(self, business_data: dict) -> str:
        """Helper to extract raw text from various possible business_data shapes."""
        parts = []

        if isinstance(business_data.get("business_context"), str):
            parts.append(business_data.get("business_context"))

        if isinstance(business_data.get("business_context"), dict):
            ctx = business_data["business_context"]
            parts.append(ctx.get("raw_text", ""))
            parts.append(ctx.get("business_context_text", ""))

        parts.append(business_data.get("raw_business_context", ""))
        parts.append(business_data.get("business_context_text", ""))

        return " ".join([p for p in parts if p]).lower()

    def get_gaps(self, business_data: dict) -> list:
        """Generate restaurant-specific gaps based on business data."""
        gaps = []
        context = self.get_context_text(business_data)

        # Check for schema
        if not business_data.get('has_schema') and not any(kw in context for kw in ['schema', 'structured data', 'json-ld']):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing Restaurant/Menu schema',
                'description': 'No Restaurant or Menu structured data detected on the website',
            })

        # Check for menu content
        if not any(kw in context for kw in ['menu', 'food list', 'dishes', 'pricing']):
            gaps.append({
                'type': 'content',
                'severity': 'high',
                'title': 'Missing menu page or structured menu',
                'description': 'No clear digital menu or structured food list found',
            })

        # Check for signature dishes
        if not any(kw in context for kw in ['signature', 'famous for', 'best seller', 'chef special']):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing signature dish content',
                'description': 'No information about signature or recommended dishes found',
            })

        # Check for opening hours and price range
        if 'hour' not in context and 'open' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing opening hours',
                'description': 'No information about business hours found',
            })

        if 'price' not in context and '$' not in context and 'rs' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing price range information',
                'description': 'No information about pricing or price range found',
            })

        # Check for delivery/reservation
        if not any(kw in context for kw in ['delivery', 'takeaway', 'order online']):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing delivery information',
                'description': 'No information about delivery or takeaway options found',
            })

        if not any(kw in context for kw in ['reservation', 'book a table', 'booking']):
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing reservation information',
                'description': 'No information about table reservations found',
            })

        # Check for photos
        if not any(kw in context for kw in ['photo', 'gallery', 'image', 'picture', 'interior', 'food']):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing food/ambience photos',
                'description': 'No visual content of food or restaurant ambience found',
            })

        # Check for FAQ
        if 'faq' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing FAQ content',
                'description': 'No restaurant FAQs found covering reservations, parking, or payment',
            })

        # Check for local comparison
        city = business_data.get('city', '')
        if city and not business_data.get('has_local_comparison'):
            gaps.append({
                'type': 'local_seo',
                'severity': 'high',
                'title': 'Missing local comparison content',
                'description': f'No "best restaurant in {city}" style content found',
            })

        return gaps

    def get_strengths(self, business_data: dict) -> list:
        """Identify restaurant-specific strengths."""
        strengths = []
        context = self.get_context_text(business_data)

        # Review base
        review_count = business_data.get('review_count', 0)
        rating = business_data.get('rating', 0)
        if review_count >= 30 or rating >= 4.0:
            strengths.append({
                'type': 'social_proof',
                'title': 'Strong review base',
                'description': f'{rating} rating with {review_count} reviews' if review_count and rating else 'Highly rated with significant review volume',
            })

        # Cuisine positioning
        cuisines = ['burger', 'pizza', 'chinese', 'desi', 'italian', 'bbq', 'steakhouse', 'bakery', 'cafe']
        found_cuisines = [c for c in cuisines if c in context]
        if found_cuisines:
            strengths.append({
                'type': 'positioning',
                'title': 'Clear cuisine positioning',
                'description': f'Strongly positioned as a {", ".join(found_cuisines[:2])} specialist',
            })

        # Signature dishes/Menu depth
        if any(kw in context for kw in ['gourmet', 'signature', 'specialty', 'variety', 'wide range', 'menu depth']):
            strengths.append({
                'type': 'content',
                'title': 'Signature dishes/Menu depth',
                'description': 'Clear information about specialty dishes and menu variety',
            })

        # Ambience
        if any(kw in context for kw in ['ambience', 'interior', 'vibe', 'atmosphere', 'decor', 'seating']):
            strengths.append({
                'type': 'ambience',
                'title': 'Ambience positioning',
                'description': 'Detailed information about restaurant atmosphere and dining environment',
            })

        # Delivery/Reservation
        if 'delivery' in context or 'takeaway' in context or 'online ordering' in context:
            strengths.append({
                'type': 'service',
                'title': 'Delivery availability',
                'description': 'Offers convenient delivery and takeaway options',
            })

        if 'reservation' in context or 'book' in context:
            strengths.append({
                'type': 'service',
                'title': 'Reservation availability',
                'description': 'Supports table reservations for customers',
            })

        # Location convenience
        if any(kw in context for kw in ['central', 'parking', 'convenient', 'location', 'accessible']):
            strengths.append({
                'type': 'location',
                'title': 'Location convenience',
                'description': 'Emphasizes accessible location and facility convenience',
            })

        # Social presence
        if any(kw in context for kw in ['instagram', 'facebook', 'social', '@']):
            strengths.append({
                'type': 'marketing',
                'title': 'Social presence',
                'description': 'Active social media presence with visual engagement',
            })

        # Review themes
        if any(kw in context for kw in ['taste', 'delicious', 'fresh', 'quality', 'clean', 'hygienic', 'service', 'staff']):
            strengths.append({
                'type': 'themes',
                'title': 'Positive food/service/hygiene review themes',
                'description': 'Review content highlights strong performance in food quality, service, and hygiene',
            })

        return strengths
