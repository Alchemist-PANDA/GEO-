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

        # Cuisine subtype detection
        self.cuisine_subtypes = {
            'turkish': {
                'keywords': ['turkish', 'kebab', 'shawarma', 'doner', 'pide', 'lahmacun', 'baklava', 'kofta', 'mezze'],
                'label': 'Turkish',
                'local_content': 'Best Turkish restaurant in {city}',
                'signature': ['kebab', 'shawarma', 'pide', 'doner'],
                'local_intent_keywords': ['kebab', 'shawarma', 'pide', 'Turkish family restaurant', 'takeaway', 'delivery'],
            },
            'chinese': {
                'keywords': ['chinese', 'noodles', 'dumplings', 'dim sum', 'hotpot', 'manchurian', 'chow mein', 'fried rice', 'wonton'],
                'label': 'Chinese',
                'local_content': 'Best Chinese restaurant in {city}',
                'signature': ['noodles', 'dumplings', 'hotpot', 'chow mein'],
                'local_intent_keywords': ['noodles', 'dumplings', 'hotpot', 'Chinese family restaurant', 'takeaway', 'delivery'],
            },
            'desi': {
                'keywords': ['desi', 'pakistani', 'biryani', 'karahi', 'nihari', 'handi', 'paratha', 'haleem', 'chapli', 'seekh kabab', 'tandoor', 'tikka'],
                'label': 'Desi/Pakistani',
                'local_content': 'Best desi restaurant in {city}',
                'signature': ['biryani', 'karahi', 'nihari', 'tandoor'],
                'local_intent_keywords': ['biryani', 'karahi', 'nihari', 'Desi family restaurant', 'takeaway', 'delivery'],
            },
            'fast_food': {
                'keywords': ['fast food', 'burger', 'fries', 'fried chicken', 'wraps', 'pizza', 'deals', 'combos', 'kids meal', 'drive thru'],
                'label': 'Fast food',
                'local_content': 'Best fast food in {city}',
                'signature': ['burgers', 'fries', 'combos', 'deals'],
                'local_intent_keywords': ['burger', 'fried chicken', 'deals', 'Fast food takeaway', 'delivery'],
            },
            'pizza': {
                'keywords': ['pizza', 'pizzeria', 'pepperoni', 'margherita', 'wood fired', 'thin crust', 'deep dish'],
                'label': 'Pizza',
                'local_content': 'Best pizza in {city}',
                'signature': ['pizza varieties', 'crusts', 'toppings'],
                'local_intent_keywords': ['pizza', 'pizzeria', 'thin crust', 'Pizza delivery', 'takeaway'],
            },
            'bbq': {
                'keywords': ['bbq', 'barbecue', 'grill', 'smoked', 'ribs', 'brisket', 'grilled'],
                'label': 'BBQ',
                'local_content': 'Best BBQ restaurant in {city}',
                'signature': ['smoked meats', 'BBQ sauce', 'grilled specialties'],
                'local_intent_keywords': ['bbq', 'barbecue', 'grill', 'BBQ takeaway', 'delivery'],
            },
            'cafe': {
                'keywords': ['cafe', 'coffee shop', 'espresso', 'latte', 'cappuccino', 'pastries', 'brunch', 'tea house', 'coffehouse'],
                'label': 'Cafe',
                'local_content': 'Best cafe in {city}',
                'signature': ['coffee', 'pastries', 'brunch'],
                'local_intent_keywords': ['coffee shop', 'brunch', 'espresso', 'Cafe takeaway'],
            },
            'bakery': {
                'keywords': ['bakery', 'cakes', 'pastries', 'breads', 'desserts', 'custom cakes', 'cupcakes', 'cookies', 'artisan bread'],
                'label': 'Bakery',
                'local_content': 'Best bakery in {city}',
                'signature': ['custom cakes', 'pastries', 'artisan breads'],
                'local_intent_keywords': ['custom cakes', 'bakery', 'pastries', 'artisan bread'],
            },
            'fine_dining': {
                'keywords': ['fine dining', 'gourmet', 'michelin', 'prix fixe', 'tasting menu', 'chef table', 'upscale'],
                'label': 'Fine dining',
                'local_content': 'Best fine dining restaurant in {city}',
                'signature': ['tasting menu', 'gourmet dishes', 'wine pairing'],
                'local_intent_keywords': ['fine dining', 'gourmet restaurant', 'tasting menu', 'upscale dining'],
            },
            'casual_dining': {
                'keywords': ['casual dining', 'family restaurant', 'buffet', 'all day dining', 'relaxed atmosphere'],
                'label': 'Casual dining',
                'local_content': 'Best casual dining in {city}',
                'signature': ['family-friendly', 'variety', 'buffet'],
                'local_intent_keywords': ['casual dining', 'family restaurant', 'buffet', 'variety'],
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

    def get_subtype(self, business_data: dict) -> dict:
        """Detect cuisine subtype from category and business context."""
        context = self.get_context_text(business_data)
        category = business_data.get("category", "").lower()
        combined = f"{category} {context}"

        # Score each subtype
        scores = {}
        for subtype_key, subtype_data in self.cuisine_subtypes.items():
            score = 0
            for keyword in subtype_data['keywords']:
                if keyword in combined:
                    score += 1
            if score > 0:
                scores[subtype_key] = score

        # Return highest scoring subtype or default
        if scores:
            best_subtype = max(scores, key=scores.get)
            return {
                'key': best_subtype,
                'label': self.cuisine_subtypes[best_subtype]['label'],
                'local_content': self.cuisine_subtypes[best_subtype]['local_content'],
                'signature': self.cuisine_subtypes[best_subtype]['signature'],
                'local_intent_keywords': self.cuisine_subtypes[best_subtype].get('local_intent_keywords', []),
            }

        return {
            'key': 'generic',
            'label': 'Restaurant',
            'local_content': 'Best restaurant in {city}',
            'signature': ['signature dishes'],
            'local_intent_keywords': ['family restaurant', 'takeaway', 'delivery'],
        }

    def get_gaps(self, business_data: dict) -> list:
        """Generate restaurant-specific gaps based on business data."""
        gaps = []
        context = self.get_context_text(business_data)
        subtype = self.get_subtype(business_data)

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

        # Check for signature dishes (subtype-specific)
        signature_keywords = ['signature', 'famous for', 'best seller', 'chef special'] + subtype.get('signature', [])
        if not any(kw in context for kw in signature_keywords):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing signature dish content',
                'description': f'No information about signature or recommended {subtype["label"].lower()} dishes found',
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

        # Check for local comparison (subtype-specific)
        # Check both the dictionary root and the business_context field
        city = business_data.get('city', '')
        if not city:
            # Fallback for some callers
            city = business_data.get('business_context', {}).get('city', '') if isinstance(business_data.get('business_context'), dict) else ''

        local_content_formatted = subtype['local_content'].format(city=city)

        has_comparison = business_data.get('has_local_comparison')
        if has_comparison is None:
            # Try to get from nested if it exists
            if isinstance(business_data.get('business_context'), dict):
                has_comparison = business_data['business_context'].get('has_local_comparison')

        if has_comparison is None:
            # Check context if not explicitly provided
            has_comparison = city.lower() in context if city else False

        if city and not has_comparison:
            gaps.append({
                'type': 'local_seo',
                'severity': 'high',
                'title': 'Missing local comparison content',
                'description': f'No "{local_content_formatted}" style content found',
            })

        return gaps

    def get_strengths(self, business_data: dict) -> list:
        """Identify restaurant-specific strengths."""
        strengths = []
        context = self.get_context_text(business_data)
        subtype = self.get_subtype(business_data)

        # Review base
        review_count = business_data.get('review_count', 0)
        rating = business_data.get('rating', 0)
        if review_count >= 30 or rating >= 4.0:
            strengths.append({
                'type': 'social_proof',
                'title': 'Strong review base',
                'description': f'{rating} rating with {review_count} reviews' if review_count and rating else 'Highly rated with significant review volume',
            })

        # Cuisine subtype positioning (subtype-specific)
        subtype_label = subtype.get('label', 'Restaurant')
        if subtype.get('key') != 'generic':
            strengths.append({
                'type': 'positioning',
                'title': f'Authentic {subtype_label} cuisine positioning',
                'description': f'Strongly positioned as an authentic {subtype_label.lower()} restaurant with traditional recipes and flavors',
            })
        else:
            # Generic restaurant cuisine positioning
            cuisines = ['burger', 'pizza', 'chinese', 'desi', 'italian', 'bbq', 'steakhouse', 'bakery', 'cafe']
            found_cuisines = [c for c in cuisines if c in context]
            if found_cuisines:
                strengths.append({
                    'type': 'positioning',
                    'title': 'Clear cuisine positioning',
                    'description': f'Strongly positioned as a {", ".join(found_cuisines[:2])} specialist',
                })

        # Signature dishes/Menu depth (subtype-specific)
        if any(kw in context for kw in ['gourmet', 'signature', 'specialty', 'variety', 'wide range', 'menu depth']):
            signature_dishes = subtype.get('signature', ['signature dishes'])
            strengths.append({
                'type': 'content',
                'title': 'Signature dishes/Menu depth',
                'description': f'Clear information about specialty {subtype_label.lower()} dishes including {", ".join(signature_dishes[:2])}',
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
