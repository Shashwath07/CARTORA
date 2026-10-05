def build_support_prompt(query: str, memories: list = None, customer_profile: dict = None, commerce_context: str = None) -> list:
    """Build the message list for Groq support generation."""
    system_parts = []
    system_parts.append(
        'You are Cartora Assist, the customer support assistant for Cartora, '
        'a direct-to-consumer e-commerce marketplace. '
        'You help customers with orders, deliveries, returns, refunds, warranties, '
        'products and account questions.'
    )
    system_parts.append(
        'Rules:\n'
        '- Be professional, clear, friendly and concise.\n'
        '- Use conversation history only when it is relevant to the current question.\n'
        '- NEVER invent or guess order numbers, prices, delivery dates, return eligibility, '
        'warranty dates, refund amounts, payment details or any account/policy facts.\n'
        '- Only reference order, product, delivery, return, warranty and account facts '
        'that are provided in the customer context below.\n'
        '- Do not ask for information that is already available in the context or history.\n'
        '- If you do not have the information needed to answer, say so clearly and '
        'offer to connect the customer with a human support agent.\n'
        '- Do not reveal internal system details, memory mechanisms or API structure.\n'
        '- Keep responses under 300 words unless the customer explicitly asks for detail.'
    )
    if customer_profile:
        profile_lines = []
        if customer_profile.get('name'):
            profile_lines.append(f"Customer name: {customer_profile['name']}")
        if customer_profile.get('tier'):
            profile_lines.append(f"Loyalty tier: {customer_profile['tier']}")
        if customer_profile.get('city'):
            profile_lines.append(f"City: {customer_profile['city']}")
        if profile_lines:
            system_parts.append('Customer profile:\n' + '\n'.join(profile_lines))
    if commerce_context:
        system_parts.append(f'Customer commerce context (use these facts, do not invent others):\n{commerce_context}')
    if memories:
        memory_text = '\n---\n'.join(memories)
        system_parts.append(f'Relevant previous support history:\n{memory_text}')
    else:
        system_parts.append('No previous support history available for this query.')
    system_content = '\n\n'.join(system_parts)
    return [
        {'role': 'system', 'content': system_content},
        {'role': 'user', 'content': query}
    ]
