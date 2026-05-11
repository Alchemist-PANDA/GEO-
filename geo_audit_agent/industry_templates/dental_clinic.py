"""Dental clinic industry template for GEO audit recommendations."""

class DentalClinicTemplate:
    """Industry-specific template for dental clinics and dental practices."""

    def __init__(self):
        self.category_triggers = [
            'dental', 'dentist', 'dental clinic', 'dental practice',
            'tooth', 'oral health', 'dental care', 'orthodontist'
        ]

        self.recommendation_signals = [
            'google_rating',
            'review_count',
            'dental_credibility',
            'treatment_options',
            'hygiene_safety',
            'emergency_care',
            'insurance_payment',
            'appointment_booking',
            'before_after_cases',
            'faq_content',
            'treatment_specific_pages',
        ]

        self.schema_recommendations = [
            'Dentist',
            'MedicalClinic',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'LocalBusiness',
            'Review',
            'FAQPage',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
            'Dentist',
        ]

        self.review_keywords = [
            'clean',
            'professional',
            'gentle',
            'painless',
            'hygiene',
            'sterilization',
            'friendly',
            'expert',
            'results',
            'teeth',
            'smile',
            'treatment',
            'appointment',
        ]

        self.remediation_playbook = {
            'schema': {
                'priority': 'high',
                'actions': [
                    'Add Dentist schema',
                    'Add MedicalClinic schema',
                    'Add LocalBusiness schema with specialized medical fields',
                ],
            },
            'content': {
                'priority': 'high',
                'actions': [
                    'Add treatment pages for braces',
                    'Add treatment pages for implants',
                    'Add treatment pages for whitening',
                    'Add treatment pages for root canal',
                    'Add treatment pages for emergency dentistry',
                    'Add dentist bio/credential pages',
                    'Add hygiene/safety section',
                    'Add insurance/payment info',
                    'Add emergency appointment info',
                    'Add treatment FAQs',
                    'Add before/after cases where compliant',
                ],
            },
            'reviews': {
                'priority': 'medium',
                'actions': [
                    'Collect reviews mentioning cleanliness and hygiene',
                    'Collect reviews mentioning professional dentists',
                    'Collect reviews mentioning painless treatment',
                    'Collect reviews mentioning appointment ease',
                    'Collect reviews mentioning treatment results',
                ],
            },
            'local_seo': {
                'priority': 'high',
                'actions': [
                    'Improve Google Business Profile with clinic photos',
                    'Update service list on Google Business Profile',
                    'Create "Best dental clinic in [city]" content',
                    'Create local comparison content',
                    'Add emergency dental care info',
                ],
            },
        }

    def get_gaps(self, business_data: dict) -> list:
        """Generate dental-specific gaps based on business data."""
        gaps = []

        context = business_data.get('business_context', '').lower() if isinstance(business_data.get('business_context'), str) else ''

        # Check for schema
        if not business_data.get('has_schema'):
            gaps.append({
                'type': 'schema',
                'severity': 'high',
                'title': 'Missing structured data',
                'description': 'No Dentist or MedicalClinic schema detected',
            })

        # Check for treatment-specific pages
        services = business_data.get('services', [])
        expected_treatments = ['braces', 'implants', 'whitening', 'root canal', 'emergency dentistry']
        missing_treatments = []

        for treatment in expected_treatments:
            if treatment not in context and not any(treatment in str(srv).lower() for srv in services):
                missing_treatments.append(treatment)

        if missing_treatments:
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing treatment-specific pages',
                'description': f'No dedicated pages for: {", ".join(missing_treatments)}',
            })

        # Check for dentist credentials
        if not business_data.get('has_credentials') and not any(kw in context for kw in ['professional dentist', 'credential', 'expert', 'experienced']):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing dentist credentials',
                'description': 'No dentist bio or credential pages found',
            })

        # Check for emergency availability
        if not business_data.get('has_emergency_info') and 'emergency' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'high',
                'title': 'Missing emergency availability',
                'description': 'No information about emergency dentistry or availability',
            })

        # Check for insurance/payment info
        if not business_data.get('has_insurance_info') and 'insurance' not in context and 'payment' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing insurance/payment info',
                'description': 'No insurance or payment option details found',
            })

        # Check for hygiene/safety information
        if not business_data.get('has_hygiene_info') and not any(kw in context for kw in ['hygiene', 'safety', 'sterilization', 'clean', 'painless']):
            gaps.append({
                'type': 'content',
                'severity': 'medium',
                'title': 'Missing hygiene/safety information',
                'description': 'No information about clinic hygiene or safety protocols',
            })

        # Check for FAQ content
        if not business_data.get('has_faq') and 'faq' not in context:
            gaps.append({
                'type': 'content',
                'severity': 'low',
                'title': 'Missing FAQ content',
                'description': 'No treatment FAQs found on the website',
            })

        # Check for local comparison content
        city = business_data.get('city', '')
        if city and not business_data.get('has_local_comparison'):
            gaps.append({
                'type': 'local_seo',
                'severity': 'high',
                'title': 'Missing local comparison content',
                'description': f'No "best dental clinic in {city}" style content found',
            })

        return gaps

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

    def get_strengths(self, business_data: dict) -> list:
        """Identify dental-specific strengths."""
        strengths = []

        context = self.get_context_text(business_data)

        # Strong review base
        review_count = business_data.get('review_count', 0)
        rating = business_data.get('rating', 0)

        # Also check structured business_context if present
        if isinstance(business_data.get("business_context"), dict):
            ctx = business_data["business_context"]
            if not review_count: review_count = ctx.get('review_count', 0)
            if not rating: rating = ctx.get('rating', 0.0)

        if review_count > 0 or rating > 0:
            if review_count >= 30 or rating >= 4.0:
                strengths.append({
                    'type': 'social_proof',
                    'title': 'Strong review base',
                    'description': f'{rating} rating with {review_count} reviews' if review_count > 0 and rating > 0 else (f'{rating} rating' if rating > 0 else f'{review_count} reviews'),
                })

        # Professional credentials/dentists
        has_credentials = business_data.get('has_credentials')
        if isinstance(business_data.get("business_context"), dict):
            if has_credentials is None: has_credentials = business_data["business_context"].get("has_credentials")

        if has_credentials or any(kw in context for kw in ['professional dentist', 'experienced dentist', 'qualified dentist', 'dentist credentials', 'orthodontist', 'implant specialist', 'credential', 'expert', 'experienced', 'iso', 'specialist']):
            strengths.append({
                'type': 'credentials',
                'title': 'Professional dentist positioning',
                'description': 'Dentists with verified credentials and expertise' if has_credentials else 'Positioned as professional dental experts with specialized skills',
            })

        # Emergency care availability
        has_emergency = business_data.get('has_emergency_info')
        if isinstance(business_data.get("business_context"), dict):
            if has_emergency is None: has_emergency = business_data["business_context"].get("has_emergency_info")

        if has_emergency or any(kw in context for kw in ['emergency dental', 'emergency dentist', 'emergency care']):
            strengths.append({
                'type': 'emergency_care',
                'title': 'Emergency care availability',
                'description': 'Emergency dental services and urgent care availability',
            })

        # Hygiene and safety
        has_hygiene = business_data.get('has_hygiene_info')
        if isinstance(business_data.get("business_context"), dict):
            if has_hygiene is None: has_hygiene = business_data["business_context"].get("has_hygiene_info")

        if has_hygiene or any(kw in context for kw in ['hygiene', 'hygienic', 'clean', 'painless', 'patient care', 'comfort']):
            strengths.append({
                'type': 'hygiene_safety',
                'title': 'Hygiene and patient comfort positioning',
                'description': 'Clinic maintains high hygiene standards and focuses on patient comfort',
            })

        # Appointment booking
        has_appointment = business_data.get('has_appointment_info')
        if isinstance(business_data.get("business_context"), dict):
            if has_appointment is None: has_appointment = business_data["business_context"].get("has_appointment_info")

        if has_appointment or any(kw in context for kw in ['appointment', 'booking', 'online booking', 'phone booking']):
            strengths.append({
                'type': 'appointment_booking',
                'title': 'Appointment booking clarity',
                'description': 'Clear information about appointment booking and scheduling',
            })

        # Comprehensive services / Broad treatment range
        services = business_data.get('services', [])
        if isinstance(business_data.get("business_context"), dict):
            if not services: services = business_data["business_context"].get("services", [])

        # Also check context for treatment variety
        treatments = ['braces', 'implants', 'whitening', 'root canal', 'crowns', 'veneers', 'pediatric', 'cosmetic']
        context_treatments = [t for t in treatments if t in context]

        if len(services) >= 3 or len(context_treatments) >= 3:
            service_list = services if services else context_treatments
            strengths.append({
                'type': 'comprehensive_services',
                'title': 'Broad treatment range',
                'description': f'Offers a wide variety of dental treatments including: {", ".join(service_list[:5])}',
            })

        return strengths
