from backend.app import db
from backend.models import Offcut, OffcutUsageHistory
import openai  # or your preferred LLM client library

def get_recommendations(cutting_instructions):
    recommendations = []
    used_offcut_ids = set()  # Track used offcut IDs
    
    print(f"Processing cutting instructions: {cutting_instructions}")
    
    for instruction in cutting_instructions:
        material_profile = instruction['material_profile']
        required_length = instruction['required_length']
        is_double_cut = instruction.get('double_cut', False)
        
        print(f"Searching for: profile={material_profile}, length>={required_length}, double_cut={is_double_cut}")
        
        if is_double_cut:
            # For double cuts, find two matching offcuts that haven't been used
            offcuts = Offcut.query.filter_by(
                is_available=True,
                material_profile=material_profile
            ).filter(
                Offcut.length_mm >= required_length,
                ~Offcut.legacy_offcut_id.in_(list(used_offcut_ids))  # Exclude used offcuts
            ).order_by(Offcut.length_mm.asc()).limit(2).all()
            
            if len(offcuts) >= 2:
                # Add both offcut IDs to used set
                used_offcut_ids.add(offcuts[0].legacy_offcut_id)
                used_offcut_ids.add(offcuts[1].legacy_offcut_id)
                
                recommendations.append({
                    'legacy_offcut_id': offcuts[0].legacy_offcut_id,
                    'related_legacy_offcut_id': offcuts[1].legacy_offcut_id,
                    'matched_profile': offcuts[0].material_profile,
                    'suggested_length': offcuts[0].length_mm,
                    'is_double_cut': True,
                    'reasoning': f"Matched pair of offcuts for double cut {material_profile} with required length {required_length}mm"
                })
        else:
            # Single-cut logic with exclusion of used offcuts
            offcut = Offcut.query.filter_by(
                is_available=True,
                material_profile=material_profile
            ).filter(
                Offcut.length_mm >= required_length,
                ~Offcut.legacy_offcut_id.in_(list(used_offcut_ids))  # Exclude used offcuts
            ).order_by(Offcut.length_mm.asc()).first()
            
            if offcut:
                used_offcut_ids.add(offcut.legacy_offcut_id)
                recommendations.append({
                    'legacy_offcut_id': offcut.legacy_offcut_id,
                    'matched_profile': offcut.material_profile,
                    'suggested_length': offcut.length_mm,
                    'is_double_cut': False,
                    'reasoning': f"Best matching offcut for {material_profile} with required length {required_length}mm"
                })
    
    print(f"Returning {len(recommendations)} recommendations")
    return recommendations

def _get_historical_context():
    """Fetch relevant historical data about offcut reuse patterns"""
    success_rates = db.session.query(
        OffcutUsageHistory.offcut_id,
        db.func.avg(db.case(
            (OffcutUsageHistory.reuse_success == True, 1),
            else_=0
        ))
    ).group_by(OffcutUsageHistory.offcut_id).all()
    
    return f"Historical success rates for {len(success_rates)} offcuts available."

def _calculate_success_rate(offcut_id):
    """Calculate historical success rate for an offcut"""
    history = OffcutUsageHistory.query.filter_by(offcut_id=offcut_id).all()
    if not history:
        return 1.0  # Default to 1.0 for new offcuts
    
    success_count = sum(1 for h in history if h.reuse_success)
    return success_count / len(history)

def _get_llm_recommendation(prompt):
    """Interface with LLM to get recommendation"""
    # Replace with your actual LLM integration
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or your preferred model
            messages=[
                {"role": "system", "content": "You are a manufacturing optimization assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return {
            'selected_id': int(response.choices[0].message.content.split()[0]),
            'explanation': response.choices[0].message.content
        }
    except Exception as e:
        raise Exception(f"LLM recommendation failed: {e}")

def _parse_llm_response(response):
    """Parse LLM response to extract offcut ID"""
    try:
        return response['selected_id']
    except (KeyError, ValueError):
        raise Exception("Invalid LLM response format")