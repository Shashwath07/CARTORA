import re

with open('backend/services/support_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace handle_message
new_func = '''def handle_message(customer_id: str, message: str, order_context: str = None, session_id: str = 'default'):
    import time, json
    t_start = time.perf_counter()
    customer_id, message = validate_request(customer_id, message)
    
    # Frustration detection (Rules-based)
    state = get_session_state(session_id)
    frustration_keywords = ['useless', 'third time', 'still not', 'manager', 'human', 'agent', 'operator', 'representative', 'real person']
    msg_lower = message.lower()
    
    frustrated = False
    if any(k in msg_lower for k in frustration_keywords):
        state['score'] += 3
    if message.isupper() and len(message) > 10:
        state['score'] += 2
        
    if state['score'] >= 3:
        state['mood'] = 'frustrated'
        frustrated = True
        
    save_session_state(session_id, state)
    
    # Escalation Path
    if frustrated and not state.get('escalation_offered'):
        from agent.prompts import build_escalation_prompt
        from backend.services.commerce_service import create_escalation_case
        
        recent_turns = get_short_term_context(session_id)
        esc_prompt = build_escalation_prompt(customer_id, order_context, recent_turns)
        
        t_llm_start = time.perf_counter()
        esc_res = generate_response(esc_prompt)
        t_llm = time.perf_counter() - t_llm_start
        
        try:
            # simple json extraction
            content = esc_res['content']
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            brief = json.loads(content.strip())
        except:
            brief = {'issue': 'User frustrated', 'mood': state['mood']}
            
        case = create_escalation_case(customer_id, order_context, brief)
        
        state['escalation_offered'] = True
        save_session_state(session_id, state)
        
        reply = f"I understand you're frustrated, and I want to get this resolved for you. I have escalated this to our human support team. Your case ID is {case['case_id']}. An agent will review the details and contact you shortly."
        add_short_term_context(session_id, message, reply)
        retain_memory(customer_id, message, 'Escalated to human', f"{customer_id}-{session_id}")
        
        return {
            'reply': reply,
            'customer_id': customer_id,
            'memories_used': 0,
            'memory_saved': True,
            'tokens': esc_res['usage'],
            'latency_ms': {'recall': 0, 'llm': round(t_llm * 1000), 'retain': 0, 'total': round((time.perf_counter() - t_start)*1000)},
            'escalated': True,
            'case_id': case['case_id']
        }

    # Normal flow
    profile = get_customer_profile(customer_id) or {}
    commerce_ctx = build_commerce_context(customer_id, order_id=order_context)
    
    t_recall_start = time.perf_counter()
    cues = ['again', 'last time', 'still', 'earlier', 'before', 'already', 'tried', 'previous']
    needs_memory = any(c in msg_lower for c in cues)
    memories = recall_memories(customer_id, message) if needs_memory else []
    t_recall = time.perf_counter() - t_recall_start
    
    recent_turns = get_short_term_context(session_id)
    prompt_messages = build_support_prompt(query=message, memories=memories, customer_profile=profile, commerce_context=commerce_ctx, recent_turns=recent_turns)
    
    t_llm_start = time.perf_counter()
    llm_output = generate_response(prompt_messages)
    t_llm = time.perf_counter() - t_llm_start
    
    reply = format_response(llm_output['content'])
    add_short_term_context(session_id, message, reply)
    
    t_retain_start = time.perf_counter()
    memory_saved = retain_memory(customer_id, message, reply[:100] + '...', f"{customer_id}-{session_id}")
    t_retain = time.perf_counter() - t_retain_start
    
    t_total = time.perf_counter() - t_start
    
    return {
        'reply': reply,
        'customer_id': customer_id,
        'memories_used': len(memories),
        'memory_saved': memory_saved,
        'tokens': llm_output['usage'],
        'latency_ms': {'recall': round(t_recall*1000), 'llm': round(t_llm*1000), 'retain': round(t_retain*1000), 'total': round(t_total*1000)},
        'escalated': False
    }
'''

text = re.sub(r'def handle_message.*?return \{.*?\n    \}', new_func, text, flags=re.DOTALL)

with open('backend/services/support_service.py', 'w', encoding='utf-8') as f:
    f.write(text)
